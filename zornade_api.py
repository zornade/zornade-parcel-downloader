"""
Zornade API v2 Client — Dati Catastali e Geocoding.

Accede agli endpoint REST gratuiti di Zornade per particelle catastali
arricchite, geocoding diretto e inverso.

Documentazione: https://zornade.com/api-particelle-catastali
Token: https://app.zornade.com
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Dict, Any, List

API_BASE_URL = (
    "https://wupqwfqjfpwrapgnogjv.supabase.co"
    "/functions/v1/api-v2/api/v2"
)


class ZornadeApiError(Exception):
    """Errore specifico dell'API Zornade."""

    def __init__(self, message: str, code: str = "", status: int = 0):
        super().__init__(message)
        self.code = code
        self.status = status


class ZornadeApiClient:
    """Client per Zornade API v2 — Dati Catastali e Geocoding."""

    def __init__(self, token: str):
        self.token = token.strip()
        self.base_url = API_BASE_URL

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _request(self, endpoint: str,
                 params: Optional[Dict[str, Any]] = None) -> Dict:
        """Esegue una richiesta GET autenticata."""
        url = f"{self.base_url}/{endpoint}"
        if params:
            filtered = {k: str(v) for k, v in params.items()
                        if v is not None}
            url = f"{url}?{urllib.parse.urlencode(filtered)}"

        req = urllib.request.Request(url, method="GET")
        req.add_header("x-api-key", self.token)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "ZornadeQGISPlugin/2.0")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                err = json.loads(body)
                err_field = err.get("error", "")
                if isinstance(err_field, dict):
                    code = err_field.get("code", "")
                    msg = err_field.get("message", str(exc))
                else:
                    code = str(err_field)
                    msg = err.get("message", str(exc))
            except (json.JSONDecodeError, ValueError):
                # HTML error pages (e.g. Cloudflare 502/503) — don't dump raw HTML
                if exc.code >= 500:
                    code = str(exc.code)
                    msg = f"Server temporaneamente non disponibile (HTTP {exc.code})"
                else:
                    code, msg = "", str(exc)
            raise ZornadeApiError(msg, code=code, status=exc.code) from exc
        except urllib.error.URLError as exc:
            raise ZornadeApiError(
                f"Errore di connessione: {exc.reason}") from exc
        except Exception as exc:
            raise ZornadeApiError(
                f"Errore imprevisto: {exc}") from exc

    # ------------------------------------------------------------------
    # Parcels
    # ------------------------------------------------------------------

    def locate_parcels(self, lat: float, lng: float,
                       limit: int = 10) -> Dict:
        """Localizza particelle catastali vicine a un punto geografico.

        Endpoint: GET /parcels/locate
        Scope: parcels:read
        """
        return self._request("parcels/locate", {
            "lat": lat, "lng": lng, "limit": limit,
        })

    def locate_parcels_bbox(self, min_lng: float, min_lat: float,
                            max_lng: float, max_lat: float,
                            limit: int = 200) -> Dict:
        """Localizza particelle in un bounding box.

        Endpoint: GET /parcels/locate?bbox=minLng,minLat,maxLng,maxLat
        Scope: parcels:read

        Vincoli: max 0.05 deg per lato, limit max 200.
        """
        bbox_str = f"{min_lng},{min_lat},{max_lng},{max_lat}"
        return self._request("parcels/locate", {
            "bbox": bbox_str, "limit": min(limit, 200),
        })

    def search_parcels(self, municipality: str,
                       sheet: Optional[str] = None,
                       parcel: Optional[str] = None,
                       limit: int = 20) -> Dict:
        """Cerca particelle per riferimento catastale.

        Endpoint: GET /parcels/search
        Scope: parcels:read
        """
        return self._request("parcels/search", {
            "municipality": municipality,
            "sheet": sheet,
            "parcel": parcel,
            "limit": limit,
        })

    def get_parcel_detail(self, parcel_id) -> Dict:
        """Profilo arricchito di una singola particella.

        Endpoint: GET /parcels/{id}
        Scope: parcels:read
        """
        return self._request(f"parcels/{parcel_id}")

    # ------------------------------------------------------------------
    # Geocoding
    # ------------------------------------------------------------------

    def geocode_search(self, query: str, limit: int = 5) -> Dict:
        """Geocoding diretto — indirizzo → coordinate.

        Endpoint: GET /geocode/search
        Scope: geocoding:read
        """
        return self._request("geocode/search", {
            "q": query, "limit": limit,
        })

    def geocode_reverse(self, lat: float, lng: float,
                        radius: int = 100, limit: int = 5) -> Dict:
        """Geocoding inverso — coordinate → indirizzo.

        Endpoint: GET /geocode/reverse
        Scope: geocoding:read
        """
        return self._request("geocode/reverse", {
            "lat": lat, "lng": lng,
            "radius": radius, "limit": limit,
        })

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def validate_token(self) -> bool:
        """Verifica la validità del token con una chiamata leggera."""
        try:
            self.geocode_search("Roma", limit=1)
            return True
        except ZornadeApiError as exc:
            return exc.status not in (401, 403)
        except Exception:
            return False
