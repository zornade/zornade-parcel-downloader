#!/usr/bin/env python3
"""Load test empirico per l'API Zornade v2.

Obiettivo: capire come risponde il server a richieste concorrenti
(/parcels/{id}?include=all) per dimensionare la concorrenza lato plugin QGIS.

- Recupera parcel_id reali via /parcels/locate?bbox=...
- Esegue il dettaglio a vari livelli di concorrenza
- Distribuisce le richieste su piu' chiavi API (round-robin) per non
  esaurire un singolo budget orario durante il test
- Riporta latenza (min/mean/p50/p95/p99/max), success rate, status code,
  e gli header X-RateLimit-* osservati

NB: nessuna modifica lato server. Solo richieste GET di lettura.
"""
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle

BASE_URL = "https://api.zornade.com/api/v2"

# Le chiavi API NON vanno committate. Passale via variabile d'ambiente:
#   export ZORNADE_API_KEYS="zrn_xxx,zrn_yyy,zrn_zzz"
#   python scripts/load_test.py
API_KEYS = [k.strip() for k in
            os.environ.get("ZORNADE_API_KEYS", "").split(",") if k.strip()]
if not API_KEYS:
    print("ERRORE: imposta ZORNADE_API_KEYS (chiavi separate da virgola).",
          file=sys.stderr)
    sys.exit(2)


def request(path, key, params=None, timeout=60):
    """GET autenticato. Ritorna (status, body_dict_or_text, headers, elapsed)."""
    url = f"{BASE_URL}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET")
    req.add_header("x-api-key", key)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "ZornadeLoadTest/1.0")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            body = resp.read().decode("utf-8", "replace")
            elapsed = time.perf_counter() - t0
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            try:
                body = json.loads(body)
            except ValueError:
                pass
            return resp.status, body, hdrs, elapsed
    except urllib.error.HTTPError as exc:
        elapsed = time.perf_counter() - t0
        hdrs = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        body = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(body)
        except ValueError:
            pass
        return exc.code, body, hdrs, elapsed
    except Exception as exc:  # noqa: BLE001
        elapsed = time.perf_counter() - t0
        return -1, str(exc), {}, elapsed


def collect_parcel_ids(target=40):
    """Raccoglie parcel_id reali da piu' bbox urbani (max 0.05 deg/lato)."""
    # Centri urbani sparsi: Roma, Milano, Napoli, Torino, Bologna
    centers = [
        (12.490, 41.900), (9.190, 45.464), (14.250, 40.850),
        (7.686, 45.070), (11.343, 44.494),
    ]
    half = 0.02  # bbox 0.04 deg/lato, sotto il cap di 0.05
    ids = []
    keys = cycle(API_KEYS)
    for lng, lat in centers:
        bbox = f"{lng-half},{lat-half},{lng+half},{lat+half}"
        status, body, hdrs, el = request(
            "parcels/locate", next(keys),
            {"bbox": bbox, "limit": 200})
        if status == 200 and isinstance(body, dict):
            feats = body.get("data", body)
            if isinstance(feats, dict):
                feats = feats.get("parcels") or feats.get("features") or []
            if isinstance(feats, list):
                for f in feats:
                    if not isinstance(f, dict):
                        continue
                    pid = (f.get("fid") or f.get("id")
                           or (f.get("properties", {}) or {}).get("fid"))
                    if pid is not None:
                        ids.append(pid)
        print(f"  bbox {bbox}: status={status} elapsed={el*1000:.0f}ms "
              f"raccolti_finora={len(ids)}")
        if len(ids) >= target:
            break
    # dedup mantenendo ordine
    seen = set()
    uniq = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    return uniq[:target]


def percentile(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def run_level(parcel_ids, concurrency):
    """Esegue il dettaglio per N particelle con la concorrenza data."""
    keys = cycle(API_KEYS)
    jobs = [(pid, next(keys)) for pid in parcel_ids]
    results = []
    wall0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = {
            ex.submit(request, f"parcels/{pid}", key, {"include": "all"}): pid
            for pid, key in jobs
        }
        for fut in as_completed(futs):
            status, body, hdrs, el = fut.result()
            results.append((status, el, hdrs))
    wall = time.perf_counter() - wall0

    lat = [el for st, el, _ in results if st == 200]
    statuses = {}
    for st, _, _ in results:
        statuses[st] = statuses.get(st, 0) + 1
    rl_remaining = [
        h.get("x-ratelimit-remaining") for _, _, h in results
        if h.get("x-ratelimit-remaining") is not None
    ]
    n429 = statuses.get(429, 0)
    ok = statuses.get(200, 0)

    print(f"\n=== Concorrenza {concurrency} | {len(parcel_ids)} particelle ===")
    print(f"  wall-clock totale : {wall:.2f}s "
          f"({len(parcel_ids)/wall:.1f} particelle/s)")
    print(f"  status            : {dict(sorted(statuses.items()))}")
    print(f"  success (200)     : {ok}/{len(parcel_ids)}  429={n429}")
    if lat:
        print(f"  latenza ms        : min={min(lat)*1000:.0f} "
              f"mean={statistics.mean(lat)*1000:.0f} "
              f"p50={percentile(lat,50)*1000:.0f} "
              f"p95={percentile(lat,95)*1000:.0f} "
              f"p99={percentile(lat,99)*1000:.0f} "
              f"max={max(lat)*1000:.0f}")
    if rl_remaining:
        try:
            mn = min(int(x) for x in rl_remaining)
            print(f"  X-RateLimit-Remaining min osservato: {mn}")
        except ValueError:
            pass
    return {
        "concurrency": concurrency, "wall": wall, "ok": ok,
        "n429": n429, "lat": lat, "statuses": statuses,
    }


def warmup(ids):
    """Scalda isolate Edge e cache di validazione token (TTL 60s) su tutte
    le chiavi, cosi' le misure non sono falsate dai cold start."""
    print("== Warm-up (scalda edge isolates + cache token) ==")
    pairs = [(pid, key) for pid in ids[:12] for key in API_KEYS]
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = [ex.submit(request, f"parcels/{pid}", key, {"include": "all"})
                for pid, key in pairs[:20]]
        for f in futs:
            f.result()
    print(f"  {min(20, len(pairs))} richieste di warm-up completate.\n")


def main():
    workload = 30   # particelle per ogni run (stesse id per ogni livello)
    reps = 3        # ripetizioni per livello (riduce il rumore)
    print("== Raccolta parcel_id reali ==")
    ids = collect_parcel_ids(target=workload)
    print(f"Raccolti {len(ids)} parcel_id unici.\n")
    if len(ids) < workload:
        print(f"Solo {len(ids)} id: riduco il workload a questo valore.")
        workload = len(ids)
    ids = ids[:workload]

    warmup(ids)

    levels = [1, 5, 10, 20, 30, 40, 50]
    summary = []
    for c in levels:
        runs = []
        for r in range(reps):
            runs.append(run_level(ids, c))
            time.sleep(0.4)
        # aggrega le ripetizioni
        lat = [x for run in runs for x in run["lat"]]
        wall = statistics.mean(run["wall"] for run in runs)
        ok = sum(run["ok"] for run in runs)
        n429 = sum(run["n429"] for run in runs)
        statuses = {}
        for run in runs:
            for k, v in run["statuses"].items():
                statuses[k] = statuses.get(k, 0) + v
        summary.append({"concurrency": c, "wall": wall, "ok": ok,
                        "n429": n429, "lat": lat, "statuses": statuses,
                        "reps": reps})
        time.sleep(0.8)

    print("\n\n================ RIEPILOGO (medie su "
          f"{reps} ripetizioni, {workload} particelle/run, post warm-up) "
          "================")
    print(f"{'conc':>5} {'wall_s':>7} {'p/s':>6} {'ok%':>5} {'err':>4} "
          f"{'429':>4} {'p50ms':>6} {'p95ms':>6} {'p99ms':>6} {'maxms':>7}")
    for s in summary:
        lat = s["lat"]
        total = sum(s["statuses"].values())
        okpct = 100.0 * s["ok"] / total if total else 0
        err = total - s["ok"]
        p50 = percentile(lat, 50) * 1000 if lat else 0
        p95 = percentile(lat, 95) * 1000 if lat else 0
        p99 = percentile(lat, 99) * 1000 if lat else 0
        mx = max(lat) * 1000 if lat else 0
        pps = (workload / s["wall"]) if s["wall"] else 0
        print(f"{s['concurrency']:>5} {s['wall']:>7.2f} {pps:>6.1f} "
              f"{okpct:>5.0f} {err:>4} {s['n429']:>4} {p50:>6.0f} {p95:>6.0f} "
              f"{p99:>6.0f} {mx:>7.0f}")
    # statuses non-200 aggregati
    print("\nStatus non-200 osservati per livello:")
    for s in summary:
        bad = {k: v for k, v in s["statuses"].items() if k != 200}
        print(f"  conc {s['concurrency']:>2}: {bad or 'nessuno'}")


if __name__ == "__main__":
    main()
