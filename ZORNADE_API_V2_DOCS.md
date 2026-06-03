# Zornade API v2 — Documentazione Completa

**Versione API:** 2.4.0  
**Base URL:** `https://api.zornade.com/api/v2`  
**Ultimo aggiornamento:** 28 aprile 2026

---

## Indice

1. [Autenticazione](#1-autenticazione)
2. [Rate Limiting](#2-rate-limiting)
3. [Formato risposte ed errori](#3-formato-risposte-ed-errori)
4. [Endpoint: Health](#4-health)
5. [Endpoint: Parcels](#5-parcels)
   - [5.1 Dettaglio particella](#51-dettaglio-particella-get-apiv2parcelsid)
   - [5.2 Ricerca catastale](#52-ricerca-catastale-get-apiv2parcelssearch)
   - [5.3 Localizzazione](#53-localizzazione-get-apiv2parcelslocate)
6. [Endpoint: Geocoding](#6-geocoding)
   - [6.1 Ricerca indirizzo](#61-ricerca-indirizzo-get-apiv2geocodesearch)
   - [6.2 Geocoding inverso](#62-geocoding-inverso-get-apiv2geocodereverse)
7. [Endpoint: Admin](#7-admin)
   - [7.1 Regioni](#71-regioni-get-apiv2adminregions)
   - [7.2 Province](#72-province-get-apiv2adminprovinces)
   - [7.3 Comuni](#73-comuni-get-apiv2adminmunicipalities)
8. [Sezioni dettaglio particella](#8-sezioni-dettaglio-particella)
9. [Fonti dati](#9-fonti-dati)
10. [Codici di errore](#10-codici-di-errore)
11. [Esempi completi](#11-esempi-completi)

---

## 1. Autenticazione

Tutti gli endpoint (tranne `/health`) richiedono un header:

| Header | Valore | Descrizione |
|---|---|---|
| `x-api-key` | `zrn_<64_hex_chars>` | Token API personale dell'utente |

**Token API:** ottenibile su [https://app.zornade.com/api](https://app.zornade.com/api). Ha formato `zrn_` seguito da 64 caratteri esadecimali.

**Scopes del token:** ogni token ha uno o più scopes che determinano quali endpoint può accedere:

| Scope | Endpoint abilitati |
|---|---|
| `parcels:read` | `/parcels/*` |
| `geocoding:read` | `/geocode/*` |
| `admin_data:read` | `/admin/*` |

**Esempio richiesta:**
```bash
curl -H "x-api-key: zrn_bdc6a659..." \
     "https://api.zornade.com/api/v2/parcels/28009975"
```

**Protezione brute-force:** dopo 20 tentativi di autenticazione falliti dallo stesso IP in 15 minuti, l'IP viene bloccato per 15 minuti.

---

## 2. Rate Limiting

| Limite | Valore |
|---|---|
| Richieste per ora | 1000 |

Ogni risposta autenticata include header di rate limiting:

| Header | Descrizione |
|---|---|
| `X-RateLimit-Limit` | Limite massimo per ora (1000) |
| `X-RateLimit-Remaining` | Richieste rimanenti nell'ora corrente |
| `X-RateLimit-Reset` | Timestamp epoch (secondi) del prossimo reset |

Quando il limite è raggiunto, la risposta è:
```json
{
  "error": "RATE_LIMITED",
  "message": "Rate limit exceeded: 1000 requests/hour. Try again later.",
  "retry_after_seconds": 60,
  "limit": 1000
}
```

---

## 3. Formato risposte ed errori

**Successo (HTTP 200):**
```json
{
  "data": { ... },
  "meta": { ... }
}
```

**Errore:**
```json
{
  "error": "ERROR_CODE",
  "message": "Descrizione leggibile dell'errore."
}
```

Tutti i metodi accettano solo `GET`. Risposte in `application/json`. CORS abilitato (`Access-Control-Allow-Origin: *`).

---

## 4. Health

```
GET /api/v2/health
```

Non richiede autenticazione. Restituisce stato e versione API.

**Risposta:**
```json
{
  "status": "ok",
  "version": "2.4.0",
  "timestamp": "2026-04-16T09:55:24.469Z",
  "auth": "All endpoints require an API key via x-api-key header. Free keys at https://app.zornade.com/api",
  "rate_limit": "1000 requests/hour",
  "endpoints": [
    "GET /api/v2/geocode/search",
    "GET /api/v2/geocode/reverse",
    "GET /api/v2/admin/{regions,provinces,municipalities}",
    "GET /api/v2/parcels/{id}",
    "GET /api/v2/parcels/search",
    "GET /api/v2/parcels/locate"
  ]
}
```

---

## 5. Parcels

Scope richiesto: `parcels:read`

### 5.1 Dettaglio particella: `GET /api/v2/parcels/{id}`

Restituisce il profilo arricchito completo di una particella catastale.

**Parametri URL:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `id` | intero o stringa | sì | FID numerico (es. `28009975`) oppure GML ID (es. `CadastralParcel.IT.AGE.PLA.H501A048100.A`) |

**Parametri query:**

| Parametro | Tipo | Default | Descrizione |
|---|---|---|---|
| `include` | stringa | `all` | Sezioni da includere, separate da virgola. Valori: `basic`, `cadastral`, `address`, `addresses`, `risk`, `subsidence`, `terrain`, `population`, `buildings`, `economics`, `demographics`, `land_cover`, `land_use`, `valuation`, `valuation_history`, `coastal_erosion`, `cultural_heritage`, `poi`, `solar`, `nightlights`. Oppure `all` per tutte. `basic` è sempre incluso. |

**Risposta completa (include=all):**

```json
{
  "data": {
    "fid": 28009975,
    "gml_id": "CadastralParcel.IT.AGE.PLA.H501A048100.A",
    "label": "A",
    "cadastral_reference": null,
    "area_m2": 1919.81,
    "centroid": {
      "lat": 41.9026974828564,
      "lng": 12.4962433583539
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[12.496, 41.902], ...]]
    },
    "municipality": {
      "code": "H501",
      "name": "Roma",
      "province": "Roma",
      "region": "Lazio"
    },
    "cadastral": { ... },
    "address": { ... },
    "addresses": [ ... ],
    "risk": { ... },
    "subsidence": { ... },
    "terrain": { ... },
    "population": { ... },
    "buildings": { ... },
    "economics": { ... },
    "demographics": { ... },
    "land_cover": { ... },
    "land_use": { ... },
    "valuation": [ ... ],
    "valuation_history": { ... },
    "coastal_erosion": [ ... ],
    "cultural_heritage": [ ... ],
    "poi": [ ... ],
    "solar": { ... },
    "nightlights": { ... }
  },
  "meta": {
    "sections_included": ["basic", "cadastral", "address", "addresses", "risk", "subsidence", "terrain", "population", "buildings", "economics", "demographics", "land_cover", "land_use", "valuation", "valuation_history", "coastal_erosion", "cultural_heritage", "solar", "poi", "nightlights"]
  }
}
```

Consulta la [Sezione 8](#8-sezioni-dettaglio-particella) per la struttura dettagliata di ogni sezione.

---

### 5.2 Ricerca catastale: `GET /api/v2/parcels/search`

Cerca particelle per riferimento catastale (comune, foglio, particella).

**Parametri query:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `comune` | stringa | sì | Nome del comune (es. `Roma`, `Milano`). Supporta ricerca fuzzy. |
| `foglio` | stringa | no | Numero foglio catastale (es. `481`) |
| `label` | stringa | no | Etichetta particella (es. `A`, `123`) |
| `sezione` | stringa | no | Sezione amministrativa (es. `A`) |
| `limit` | intero | 20 | Max risultati (max 100) |

**Risposta:**
```json
{
  "data": [
    {
      "fid": 28007896,
      "label": "1",
      "municipality": "Roma",
      "foglio": "481",
      "sezione": "A",
      "area_m2": 149.28,
      "centroid": {
        "lat": 41.904996405,
        "lng": 12.4983429906189
      }
    }
  ],
  "meta": {
    "comune": "Roma",
    "foglio": "481",
    "label": null,
    "count": 1
  }
}
```

---

### 5.3 Localizzazione: `GET /api/v2/parcels/locate`

Trova particelle catastali per coordinate geografiche o bounding box. Tre modalità:

#### Modalità 1: Punto singolo

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `lat` | float | sì | Latitudine (WGS84, range 35.5–47.5) |
| `lng` | float | sì | Longitudine (WGS84, range 6.0–19.0) |
| `limit` | intero | 50 | Max risultati (max 200) |

```
GET /api/v2/parcels/locate?lat=41.9028&lng=12.4964&limit=1
```

#### Modalità 2: Punti multipli

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `points` | stringa | sì | Coppie lat,lng separate da `;` (max 10 punti) |
| `limit` | intero | 50 | Max risultati per punto (max 200) |

```
GET /api/v2/parcels/locate?points=41.9028,12.4964;45.4642,9.1900&limit=1
```

#### Modalità 3: Bounding box

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `bbox` | stringa | sì | Formato: `minLng,minLat,maxLng,maxLat` |
| `limit` | intero | 50 | Max risultati (max 200) |

**Vincolo:** massimo 0.05° per lato (~5.5 km).

```
GET /api/v2/parcels/locate?bbox=12.494,41.900,12.498,41.905&limit=10
```

**Risposta (identica per tutte le modalità):**
```json
{
  "data": [
    {
      "fid": 28009975,
      "gml_id": "CadastralParcel.IT.AGE.PLA.H501A048100.A",
      "label": "A",
      "cadastral_reference": null,
      "municipality": {
        "code": "H501",
        "name": "Roma",
        "province": "Roma",
        "region": "Lazio"
      },
      "area_m2": 1919.81,
      "centroid": {
        "lat": 41.9026974828564,
        "lng": 12.4962433583539
      }
    }
  ],
  "meta": {
    "mode": "point",
    "lat": 41.9028,
    "lng": 12.4964,
    "count": 1
  }
}
```

---

## 6. Geocoding

Scope richiesto: `geocoding:read`

Database di 18.7+ milioni di indirizzi ANNCSU (Archivio Nazionale dei Numeri Civici e delle Strade Urbane).

### 6.1 Ricerca indirizzo: `GET /api/v2/geocode/search`

Geocoding diretto: da indirizzo a coordinate.

**Parametri query:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `q` | stringa | sì | Testo da cercare (min 2 caratteri). Es. `Via del Corso` |
| `city` | stringa | no | Filtra per nome comune (es. `Roma`) |
| `limit` | intero | 10 | Max risultati (max 50) |

**Risposta:**
```json
{
  "data": [
    {
      "address_id": 1107361,
      "street_name": "Via Del Corso",
      "street_number": "1",
      "locality": "",
      "municipality_code": "H501",
      "municipality_name": "Roma",
      "province": "Roma",
      "region": "Lazio",
      "latitude": 41.9097928,
      "longitude": 12.4768308,
      "formatted_address": "Via Del Corso 1, , Roma"
    }
  ],
  "meta": {
    "query": "Via del Corso",
    "city": "Roma",
    "count": 1
  }
}
```

---

### 6.2 Geocoding inverso: `GET /api/v2/geocode/reverse`

Da coordinate a indirizzi vicini.

**Parametri query:**

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `lat` | float | sì | Latitudine (WGS84, range 35.5–47.5) |
| `lng` | float | sì | Longitudine (WGS84, range 6.0–19.0) |
| `radius` | intero | 100 | Raggio di ricerca in metri (max 500) |
| `limit` | intero | 5 | Max risultati (max 20) |

**Risposta:**
```json
{
  "data": [
    {
      "address_id": 960481,
      "street_name": "Piazza Della Repubblica",
      "street_number": "11",
      "locality": "",
      "municipality_code": "H501",
      "municipality_name": "Roma",
      "province": "Roma",
      "latitude": 41.90318,
      "longitude": 12.4965448,
      "distance_meters": 43.88,
      "formatted_address": "Piazza Della Repubblica 11, , Roma"
    }
  ],
  "meta": {
    "lat": 41.9028,
    "lng": 12.4964,
    "radius_m": 100,
    "count": 1
  }
}
```

---

## 7. Admin

Scope richiesto: `admin_data:read`

Dati amministrativi italiani. Risposte cachate per 1 ora (`Cache-Control: public, max-age=3600`).

### 7.1 Regioni: `GET /api/v2/admin/regions`

```json
{
  "data": [
    {
      "id": 13,
      "code": 13,
      "name": "Abruzzo",
      "area_km2": 10830.62
    }
  ]
}
```

### 7.2 Province: `GET /api/v2/admin/provinces`

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `region` | stringa o intero | no | Filtra per nome regione (es. `Lazio`) o codice ISTAT (es. `12`) |

```json
{
  "data": [
    {
      "id": 60,
      "code": 60,
      "name": "Frosinone",
      "abbreviation": "FR",
      "region_code": 12
    }
  ]
}
```

### 7.3 Comuni: `GET /api/v2/admin/municipalities`

| Parametro | Tipo | Obbligatorio | Descrizione |
|---|---|---|---|
| `province` | stringa | no | Filtra per nome provincia (es. `Roma`) |
| `region` | stringa | no | Filtra per nome regione (es. `Lazio`) |

```json
{
  "data": [
    {
      "id": 5602,
      "name": "Affile",
      "province": "Roma",
      "region": "Lazio",
      "postal_code": "00021",
      "fiscal_code": "A062"
    }
  ]
}
```

---

## 8. Sezioni dettaglio particella

Ogni sezione del dettaglio particella (`GET /api/v2/parcels/{id}`) è descritta qui con la struttura esatta dei campi, il tipo, e la descrizione. Tutti i campi possono essere `null` se il dato non è disponibile per quella particella.

### 8.1 `basic` (sempre incluso)

Campi di primo livello nella risposta (non annidati sotto una chiave "basic"):

| Campo | Tipo | Descrizione |
|---|---|---|
| `fid` | integer | ID univoco della particella nel database |
| `gml_id` | string | Identificativo GML (es. `CadastralParcel.IT.AGE.PLA.H501A048100.A`) |
| `label` | string | Etichetta della particella (numero/lettera, es. `A`, `123`) |
| `cadastral_reference` | string\|null | Riferimento catastale nazionale (NCR) |
| `area_m2` | float | Superficie in metri quadri |
| `centroid.lat` | float | Latitudine del centroide (WGS84) |
| `centroid.lng` | float | Longitudine del centroide (WGS84) |
| `geometry` | GeoJSON | Geometria poligonale completa della particella (GeoJSON Polygon) |
| `municipality.code` | string | Codice Belfiore del comune (es. `H501` per Roma) |
| `municipality.name` | string | Nome del comune |
| `municipality.province` | string | Nome della provincia |
| `municipality.region` | string | Nome della regione |

### 8.2 `cadastral`

| Campo | Tipo | Descrizione |
|---|---|---|
| `foglio` | string\|null | Numero foglio catastale |
| `sezione_urbana` | string\|null | Sezione urbana catastale |
| `comune_code` | string\|null | Codice Belfiore del comune |
| `postal_code` | string\|null | CAP (codice avviamento postale subcomunale) |

### 8.3 `address`

Indirizzo primario (il primo trovato intersecando la geometria della particella):

| Campo | Tipo | Descrizione |
|---|---|---|
| `street` | string | Nome strada (odonimo) |
| `number` | string\|null | Numero civico |

Valore `null` se nessun indirizzo interseca la particella.

### 8.4 `addresses`

Lista completa di tutti gli indirizzi ANNCSU che intersecano la geometria della particella (massimo 20):

```json
[
  {
    "street": "VIA SANT'ANSELMO",
    "number": "9",
    "exponent": "",
    "locality": ""
  }
]
```

| Campo | Tipo | Descrizione |
|---|---|---|
| `street` | string | Nome strada (odonimo) |
| `number` | string\|null | Numero civico |
| `exponent` | string\|null | Esponente del civico (es. `A`, `BIS`) |
| `locality` | string\|null | Località/frazione |

### 8.5 `risk`

Rischi naturali aggregati:

| Campo | Tipo | Descrizione |
|---|---|---|
| `seismic_zone` | integer\|null | Zona sismica INGV (1=più pericolosa, 4=meno pericolosa) |
| `pga` | float\|null | Peak Ground Acceleration — accelerazione massima al suolo (g) |
| `flood_level` | string\|null | Livello rischio alluvioni ISPRA. Valori: `HPH` (elevata), `MPH` (media), `LPH` (bassa) |
| `landslide_level` | string\|null | Livello rischio frane ISPRA. Valori: `P4` (molto elevata), `AA` (attenzione), `P3` (elevata), `P2` (media), `P1` (moderata) |

### 8.6 `subsidence`

Dati subsidenza dal programma EGMS (European Ground Motion Service):

| Campo | Tipo | Descrizione |
|---|---|---|
| `velocity_mm_year` | float\|null | Velocità media di subsidenza in mm/anno (negativo = abbassamento) |
| `acceleration` | float\|null | Accelerazione del moto in mm/anno² |
| `risk_class` | integer\|null | Classe di rischio (1–5) |
| `risk_label` | string\|null | Etichetta rischio (es. `Stabile`, `Attenzione`, `Critico`) |
| `risk_index` | float\|null | Indice di rischio composito (0–1) |
| `direction` | string\|null | Direzione prevalente del moto (es. `vertical`, `east-west`) |
| `trend` | string\|null | Tendenza negli ultimi anni (es. `stable`, `accelerating`, `decelerating`) |

### 8.7 `terrain`

Dati orografici derivati da DEM TINItaly/01 (risoluzione 10m):

| Campo | Tipo | Descrizione |
|---|---|---|
| `elevation_min` | float\|null | Quota minima (m s.l.m.) |
| `elevation_max` | float\|null | Quota massima (m s.l.m.) |
| `elevation_mean` | float\|null | Quota media (m s.l.m.) |
| `elevation_std` | float\|null | Deviazione standard dell'elevazione |
| `ruggedness_index` | float\|null | Indice di rugosità del terreno (TRI, in metri) |
| `slope_mean` | float\|null | Pendenza media (gradi) |
| `slope_max` | float\|null | Pendenza massima (gradi) |
| `tri_mean` | float\|null | TRI (Terrain Ruggedness Index) medio |
| `aspect_predominant` | string\|null | Esposizione predominante (es. `N`, `NE`, `S`, `SW`) |
| `source` | string\|null | Fonte dati (es. `tinitaly_1.1`) |

### 8.8 `population`

Stima della popolazione residente sulla particella:

| Campo | Tipo | Descrizione |
|---|---|---|
| `estimated` | float\|null | Popolazione stimata (valore finale migliore) |
| `sum` | float\|null | Somma dei pixel WorldPop intersecanti |
| `pixel_count` | integer\|null | Numero pixel WorldPop intersecanti |
| `mean` | float\|null | Media dei pixel WorldPop |
| `dasymetric` | float\|null | Stima dasymetrica (basata su edifici residenziali) |
| `estimation_method` | string\|null | Metodo di stima (es. `worldpop_constrained`, `dasymetric`, `legacy`) |
| `estimation_confidence` | float\|null | Confidenza della stima (0–1) |
| `municipality_total` | float\|null | Popolazione totale del comune (per contesto) |
| `source` | string\|null | Fonte dati |

### 8.9 `buildings`

Edifici presenti all'interno della particella (da OpenStreetMap):

| Campo | Tipo | Descrizione |
|---|---|---|
| `count` | integer\|null | Numero totale di edifici |
| `footprint_m2` | float\|null | Superficie coperta totale (m²) |
| `residential_count` | integer\|null | Numero edifici residenziali |
| `residential_footprint_m2` | float\|null | Superficie coperta residenziale (m²) |
| `source` | string\|null | Fonte (es. `openstreetmap`) |

### 8.10 `economics`

Dati economici/reddituali dalla dichiarazione IRPEF (MEF — Dipartimento delle Finanze):

| Campo | Tipo | Descrizione |
|---|---|---|
| `average_income` | float\|null | Reddito medio (€/anno) nella zona CAP subcomunale |
| `taxpayers` | integer\|null | Numero contribuenti nella zona |
| `total_income` | integer\|null | Reddito complessivo della zona (€) |
| `net_tax` | integer\|null | Imposta netta totale (€) |
| `tax_year` | integer\|null | Anno d'imposta (es. 2023) |
| `gini_index` | float\|null | Indice di Gini della distribuzione dei redditi (0=uguaglianza perfetta, 1=disuguaglianza massima). Calcolato con approssimazione trapezoidale della curva di Lorenz. |
| `affordability_index` | float\|null | Indice di accessibilità abitativa (PIR: Price-to-Income Ratio). Numero di anni di reddito medio necessari per acquistare un appartamento di 80 m² al prezzo OMI medio residenziale della zona. |
| `avg_residential_price_m2` | float\|null | Prezzo OMI medio residenziale (€/m²) |
| `affordability_apt_size_m2` | integer | Dimensione dell'appartamento di riferimento (fisso: 80 m²) |
| `income_brackets` | object | Distribuzione contribuenti per fascia di reddito: |
| `income_brackets.lte_zero` | integer\|null | ≤ 0 € |
| `income_brackets.from_0_to_10k` | integer\|null | 0–10.000 € |
| `income_brackets.from_10k_to_15k` | integer\|null | 10.000–15.000 € |
| `income_brackets.from_15k_to_26k` | integer\|null | 15.000–26.000 € |
| `income_brackets.from_26k_to_55k` | integer\|null | 26.000–55.000 € |
| `income_brackets.from_55k_to_75k` | integer\|null | 55.000–75.000 € |
| `income_brackets.from_75k_to_120k` | integer\|null | 75.000–120.000 € |
| `income_brackets.over_120k` | integer\|null | > 120.000 € |
| `source` | string\|null | Fonte e anno (es. `MEF — Dipartimento delle Finanze, IRPEF 2023`) |

### 8.11 `demographics`

Dati demografici dal Censimento permanente ISTAT 2021, a livello di sezione di censimento:

| Campo | Tipo | Descrizione |
|---|---|---|
| `population_total` | integer\|null | Popolazione totale della sezione di censimento |
| `male` | integer\|null | Popolazione maschile |
| `female` | integer\|null | Popolazione femminile |
| `age_brackets` | object | Distribuzione per fasce d'età: |
| `age_brackets.0_4` | integer\|null | 0–4 anni |
| `age_brackets.5_9` | integer\|null | 5–9 anni |
| `age_brackets.10_14` | integer\|null | 10–14 anni |
| `age_brackets.15_19` | integer\|null | 15–19 anni |
| `age_brackets.20_24` | integer\|null | 20–24 anni |
| `age_brackets.25_29` | integer\|null | 25–29 anni |
| `age_brackets.30_34` | integer\|null | 30–34 anni |
| `age_brackets.35_39` | integer\|null | 35–39 anni |
| `age_brackets.40_44` | integer\|null | 40–44 anni |
| `age_brackets.45_49` | integer\|null | 45–49 anni |
| `age_brackets.50_54` | integer\|null | 50–54 anni |
| `age_brackets.55_59` | integer\|null | 55–59 anni |
| `age_brackets.60_64` | integer\|null | 60–64 anni |
| `age_brackets.65_69` | integer\|null | 65–69 anni |
| `age_brackets.70_74` | integer\|null | 70–74 anni |
| `age_brackets.75_plus` | integer\|null | 75+ anni |
| `education` | object | Titolo di studio: |
| `education.no_title` | integer\|null | Senza titolo di studio |
| `education.elementary` | integer\|null | Licenza elementare |
| `education.middle_school` | integer\|null | Licenza media |
| `education.high_school` | integer\|null | Diploma superiore |
| `education.university` | integer\|null | Laurea o titolo superiore |
| `employed` | integer\|null | Occupati |
| `foreigners.total` | integer\|null | Stranieri residenti (totale) |
| `foreigners.eu` | integer\|null | Stranieri comunitari (UE) |
| `foreigners.non_eu` | integer\|null | Stranieri extracomunitari |
| `households` | object | Nuclei familiari per dimensione: |
| `households.1_member` | integer\|null | Famiglie di 1 componente |
| `households.2_members` | integer\|null | Famiglie di 2 componenti |
| `households.3_members` | integer\|null | Famiglie di 3 componenti |
| `households.4_members` | integer\|null | Famiglie di 4 componenti |
| `households.5_members` | integer\|null | Famiglie di 5 componenti |
| `households.6_plus_members` | integer\|null | Famiglie di 6+ componenti |
| `households.total` | integer\|null | Totale famiglie |
| `dwellings` | object | Abitazioni: |
| `dwellings.total` | integer\|null | Totale abitazioni |
| `dwellings.occupied` | integer\|null | Abitazioni occupate |
| `dwellings.vacant` | integer\|null | Abitazioni vuote |
| `source` | string\|null | Fonte (es. `ISTAT — Censimento permanente della popolazione 2021`) |

**Nota:** `demographics` può essere `null` se il centroide della particella non cade in una sezione di censimento con dati disponibili.

### 8.12 `land_cover`

Copertura del suolo CORINE Land Cover 2018:

| Campo | Tipo | Descrizione |
|---|---|---|
| `code` | string | Codice CLC (es. `112`) |
| `class` | string | Livello 1 CLC (es. `1` = Superfici artificiali) |
| `subclass` | string | Livello 2 CLC (es. `11` = Zone urbanizzate) |
| `description` | string | Livello 3 CLC (es. `112` = Tessuto urbanizzato discontinuo) |
| `source` | string | Fonte (es. `CORINE Land Cover 2018 — Copernicus/EEA`) |

Valore `null` se nessun poligono CLC interseca il centroide.

### 8.13 `land_use`

Uso del suolo Urban Atlas 2018:

| Campo | Tipo | Descrizione |
|---|---|---|
| `code` | string | Codice Urban Atlas |
| `class` | string | Classe Urban Atlas |
| `level1` | string | Livello 1 UA |
| `level2` | string | Livello 2 UA |
| `source` | string | Fonte (es. `Urban Atlas 2018 — Copernicus/EEA`) |

Valore `null` se non coperto da Urban Atlas (disponibile solo per Functional Urban Areas).

### 8.14 `valuation`

Quotazioni immobiliari OMI (Osservatorio del Mercato Immobiliare, Agenzia delle Entrate). Array di oggetti, uno per ogni combinazione tipologia/stato conservativo nella zona OMI:

```json
[
  {
    "zone": "B29",
    "zone_description": "VIMINALE (VIA TORINO)",
    "fascia": "B",
    "microzona": 8,
    "municipality": "ROMA",
    "property_type": "Abitazioni signorili",
    "condition": "NORMALE",
    "purchase": {
      "min_eur_m2": 5200,
      "max_eur_m2": 7100
    },
    "rental": {
      "min_eur_m2": 17.3,
      "max_eur_m2": 23.8
    },
    "previous_semester": {
      "purchase": {
        "min_eur_m2": 4800,
        "max_eur_m2": 6600
      },
      "rental": {
        "min_eur_m2": 15.8,
        "max_eur_m2": 22.8
      }
    }
  }
]
```

| Campo | Tipo | Descrizione |
|---|---|---|
| `zone` | string | Codice zona OMI (es. `B29`) |
| `zone_description` | string | Descrizione della zona OMI |
| `fascia` | string | Fascia (es. `B` = semicentrale, `C` = periferica, `D` = suburbana, `R` = rurale) |
| `microzona` | integer\|null | Numero microzona catastale |
| `municipality` | string | Nome comune |
| `property_type` | string | Tipologia immobiliare (es. `Abitazioni civili`, `Abitazioni signorili`, `Box`, `Negozi`) |
| `condition` | string | Stato conservativo (es. `NORMALE`, `OTTIMO`, `SCADENTE`) |
| `purchase.min_eur_m2` | float\|null | Prezzo compravendita minimo (€/m²) |
| `purchase.max_eur_m2` | float\|null | Prezzo compravendita massimo (€/m²) |
| `rental.min_eur_m2` | float\|null | Canone locazione minimo (€/m²/mese) |
| `rental.max_eur_m2` | float\|null | Canone locazione massimo (€/m²/mese) |
| `previous_semester.purchase.min_eur_m2` | float\|null | Min compravendita semestre precedente |
| `previous_semester.purchase.max_eur_m2` | float\|null | Max compravendita semestre precedente |
| `previous_semester.rental.min_eur_m2` | float\|null | Min locazione semestre precedente |
| `previous_semester.rental.max_eur_m2` | float\|null | Max locazione semestre precedente |

Array vuoto `[]` se la particella non è coperta da zone OMI.

### 8.15 `coastal_erosion`

Dati erosione costiera ISPRA (fino a 5 segmenti nel raggio di 1 km dal centroide):

| Campo | Tipo | Descrizione |
|---|---|---|
| `dynamic` | string\|null | Dinamica 2006–2020 (es. `Arretramento`, `Avanzamento`, `Stabile`) |
| `avg_change_m_year` | float\|null | Variazione media (m/anno, negativo = erosione) |
| `max_change_m_year` | float\|null | Variazione massima (m/anno) |
| `severity_index` | float\|null | Indice di severità dell'erosione |
| `coast_type` | integer\|null | Tipo di costa (codice numerico) |
| `lithology` | string\|null | Litologia costiera |
| `distance_m` | float | Distanza dal centroide della particella (m) |

Array vuoto `[]` se la particella è lontana dalla costa (oltre 1 km).

### 8.16 `cultural_heritage`

Vincoli culturali (beni architettonici/storici tutelati) che intersecano la geometria della particella (max 20):

| Campo | Tipo | Descrizione |
|---|---|---|
| `id` | integer | ID del bene nel database MiBACT |
| `name` | string\|null | Denominazione del bene |
| `type` | string\|null | Tipo bene (es. `Architettura religiosa`, `Villa`) |
| `class` | string\|null | Classe di vincolo |
| `address` | string\|null | Indirizzo del bene |
| `municipality` | string\|null | Comune |
| `province` | string\|null | Provincia |
| `catalog_code` | string\|null | Codice ICCD (Istituto Centrale per il Catalogo e la Documentazione) |

Array vuoto `[]` se nessun vincolo interseca la particella.

### 8.17 `poi`

Punti di interesse Foursquare (attivi, non chiusi) che intersecano la geometria della particella (max 50):

| Campo | Tipo | Descrizione |
|---|---|---|
| `id` | string | Foursquare Place ID |
| `name` | string | Nome del luogo |
| `categories` | string\|null | Categorie Foursquare (stringa con label separate da virgola) |
| `address` | string\|null | Indirizzo |
| `locality` | string\|null | Località |
| `coordinates.lat` | float | Latitudine |
| `coordinates.lng` | float | Longitudine |

Array vuoto `[]` se nessun POI è presente nella particella.

### 8.18 `solar`

Potenziale fotovoltaico aggregato a livello di particella, calcolato sugli edifici presenti (modello JRC PVGIS-SARAH3 + metodologia Zornade v1.1).

Se non sono disponibili dati solari per la particella, l'oggetto è `{ "available": false, "methodology_version": "v1.1" }`.

Quando `available` è `true`:

| Campo | Tipo | Descrizione |
|---|---|---|
| `available` | boolean | `true` se sono disponibili stime solari |
| `n_buildings` | integer | Numero di edifici analizzati nella particella |
| `kwp_max_total` | float | Potenza di picco massima installabile totale (kWp) |
| `pvout_modern_kwh_year_total` | float | Produzione annua attesa con moduli moderni (kWh/anno) |
| `pvout_pessimistic_kwh_year_total` | float | Produzione annua in scenario pessimistico (kWh/anno) |
| `roof_pitch_avg_deg` | float | Inclinazione media delle falde (gradi) |
| `roof_aspect_avg_deg` | float | Esposizione media delle falde (gradi, 180 = sud) |
| `viability_class_max` | string | Classe di viabilità massima (es. `alta`, `media`, `bassa`) |
| `capex_eur_total` | float | Investimento stimato totale (€) |
| `npv_20y_eur_total` | float | Valore attuale netto a 20 anni (€) |
| `payback_years_simple_avg` | float | Tempo di ritorno semplice medio (anni) |
| `lcoe_eur_per_kwh_avg` | float | Costo livellato dell'energia medio (€/kWh) |
| `data_version` | string | Versione del dataset (es. `pvgis:v5.3;sarah3:2025-10;model:v1.1`) |
| `methodology_version` | string | Versione della metodologia (es. `v1.1`) |
| `source` | string | Fonte (es. `JRC PVGIS-SARAH3 v5.3 + Zornade methodology v1.1`) |
| `updated_at` | string | Timestamp ISO 8601 dell'ultimo aggiornamento |
| `buildings` | array | Dettaglio per singolo edificio (vedi sotto) |

Ogni elemento di `buildings` contiene: `building_fid`, `roof_shape`, `roof_pitch_deg`, `roof_aspect_deg`, `roof_area_real_m2`, `kwp_max`, `pvout_modern_kwh_year`, `capex_eur`, `npv_20y_eur`, `payback_years_simple`, `lcoe_eur_per_kwh`, `viability_class`, `confidence_level`, `exclusion_reason`, `bipv_eligible`.

### 8.19 `nightlights`

Luminosità notturna derivata dalle immagini satellitari VIIRS Black Marble (VNP46A4).

Se non disponibile, l'oggetto è `{ "available": false }`.

Quando `available` è `true`:

| Campo | Tipo | Descrizione |
|---|---|---|
| `available` | boolean | `true` se sono disponibili dati di luminosità |
| `ntl_parcel` | float | Radianza notturna stimata sulla particella |
| `ntl_density` | float | Densità di radianza (per unità di superficie) |
| `ntl_class` | string | Classe di luminosità: `dark`, `dim`, `medium`, `bright`, `very_bright` |
| `ntl_share` | float | Quota della radianza comunale attribuita alla particella |
| `ntl_mean_comune` | float | Radianza media del comune (riferimento) |
| `estimation_method` | string | Metodo di stima: `dasymetric` o `uniform` |
| `ntl_year` | integer | Anno dei dati (es. `2023`) |
| `source` | string | Fonte (es. `viirs_vnp46a4_c2_2023`) |
| `updated_at` | string | Timestamp ISO 8601 dell'ultimo aggiornamento |

### 8.20 `valuation_history`

Serie storica semestrale delle quotazioni immobiliari OMI (Osservatorio del Mercato Immobiliare) per la zona della particella. Tipo immobiliare di riferimento: `Abitazioni civili`, stato `NORMALE`.

`null` se la particella non è arricchita con lo storico OMI.

| Campo | Tipo | Descrizione |
|---|---|---|
| `zone_current` | string | Zona OMI corrente (es. `B29`) |
| `municipality_code` | string | Codice catastale del comune |
| `property_type` | string | Tipo immobiliare (es. `Abitazioni civili`) |
| `condition` | string | Stato conservativo (es. `NORMALE`) |
| `semesters` | array | Serie storica semestrale (vedi sotto) |
| `metrics` | object\|null | Metriche aggregate calcolate (può essere `null`) |
| `annotations` | object\|null | Annotazioni (può essere `null`) |
| `data_version` | string | Versione del dataset (es. `omi_2015_1..2025_2_v1`) |
| `source` | string | Fonte (es. `omi_historical_enrichment`) |
| `updated_at` | string | Timestamp ISO 8601 dell'ultimo aggiornamento |

Ogni elemento di `semesters`:

| Campo | Tipo | Descrizione |
|---|---|---|
| `semester` | string | Semestre nel formato `AAAA_N` (es. `2015_1`, `2025_2`) |
| `zone` | string | Zona OMI del semestre |
| `purchase.min_eur_m2` | float | Quotazione acquisto minima (€/m²) |
| `purchase.max_eur_m2` | float | Quotazione acquisto massima (€/m²) |
| `purchase.mid_eur_m2` | float | Quotazione acquisto media (€/m²) |
| `rental.min_eur_m2` | float | Canone locazione minimo (€/m²/mese) |
| `rental.max_eur_m2` | float | Canone locazione massimo (€/m²/mese) |
| `rental.mid_eur_m2` | float | Canone locazione medio (€/m²/mese) |
| `gross_yield_pct` | float | Rendimento lordo da locazione (%) |

---

## 9. Fonti dati

| Sezione | Fonte | Aggiornamento |
|---|---|---|
| Particelle catastali | Agenzia delle Entrate (WFS AdE) | Continuo |
| Indirizzi | ANNCSU (ISTAT/Agenzia delle Entrate) | 2026 |
| Rischio sismico | INGV — Zone sismiche e PGA | 2024 |
| Alluvioni | ISPRA — Mappa pericolosità alluvioni | 2024 |
| Frane | ISPRA — Inventario fenomeni franosi | 2024 |
| Subsidenza | EGMS — European Ground Motion Service | 2023 |
| Terreno | TINItaly/01 DEM (10m) — INGV | v1.1 |
| Popolazione | WorldPop + dasymetry | 2020–2023 |
| Edifici | OpenStreetMap | Continuo |
| Redditi/Economia | MEF — Dipartimento delle Finanze (IRPEF) | 2023 |
| Dati demografici | ISTAT — Censimento permanente 2021 | 2021 |
| Copertura suolo | CORINE Land Cover 2018 — Copernicus/EEA | 2018 |
| Uso del suolo | Urban Atlas 2018 — Copernicus/EEA | 2018 |
| Quotazioni immobiliari | OMI — Agenzia delle Entrate | 2° sem. 2025 (con confronto 1° sem. 2025) |
| Storico quotazioni (OMI) | OMI — Agenzia delle Entrate (serie semestrale) | 2015–2025 |
| Erosione costiera | ISPRA — Dinamica litorale | 2006–2020 |
| Vincoli culturali | MiBACT — Vincoli in rete | 2024 |
| Punti di interesse | Foursquare Places | 2024 |
| Potenziale fotovoltaico | JRC PVGIS-SARAH3 v5.3 + metodologia Zornade v1.1 | 2025 |
| Luci notturne | NASA VIIRS Black Marble (VNP46A4) | 2023 |
| CAP subcomunali | Poste Italiane / ISTAT | 2025 |

---

## 10. Codici di errore

| Codice | HTTP | Descrizione |
|---|---|---|
| `API_KEY_REQUIRED` | 401 | Header `x-api-key` mancante |
| `INVALID_API_KEY` | 401 | Token non valido o scaduto |
| `INSUFFICIENT_SCOPE` | 403 | Token privo dello scope necessario |
| `RATE_LIMITED` | 429 | Superato il limite di 1000 richieste/ora |
| `TOO_MANY_ATTEMPTS` | 429 | Troppi tentativi di autenticazione falliti (IP bloccato per 15 min) |
| `INVALID_PARAMS` | 400 | Parametri mancanti o non validi |
| `OUT_OF_BOUNDS` | 400 | Coordinate fuori dall'Italia (lat 35.5–47.5, lng 6.0–19.0) |
| `BBOX_TOO_LARGE` | 400 | Bounding box troppo grande (max 0.05° per lato) |
| `NOT_FOUND` | 404 | Risorsa non trovata |
| `METHOD_NOT_ALLOWED` | 405 | Solo GET è supportato |
| `QUERY_ERROR` | 502 | Errore nel database |
| `SERVICE_UNAVAILABLE` | 503 | Database temporaneamente non disponibile |
| `INTERNAL_ERROR` | 500 | Errore interno del server |

---

## 11. Esempi completi

### Python (urllib — compatibile QGIS senza dipendenze esterne)

```python
import json
import urllib.request
import urllib.parse

BASE_URL = "https://api.zornade.com/api/v2"
API_KEY = "zrn_YOUR_API_KEY_HERE"


def api_get(endpoint, params=None):
    """Esegue una richiesta GET autenticata all'API Zornade."""
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None}
        )

    req = urllib.request.Request(url, method="GET")
    req.add_header("x-api-key", API_KEY)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "ZornadeQGISPlugin/3.0")

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --- Esempio 1: Dettaglio completo di una particella ---
result = api_get("parcels/28009975", {"include": "all"})
parcel = result["data"]
print(f"FID: {parcel['fid']}")
print(f"Comune: {parcel['municipality']['name']}")
print(f"Area: {parcel['area_m2']} m²")
print(f"Zona sismica: {parcel['risk']['seismic_zone']}")
print(f"Reddito medio: {parcel['economics']['average_income']} €")

# --- Esempio 2: Solo alcune sezioni ---
result = api_get("parcels/28009975", {"include": "risk,economics,terrain"})

# --- Esempio 3: Localizza particella da coordinate ---
result = api_get("parcels/locate", {"lat": 41.9028, "lng": 12.4964, "limit": 1})
fid = result["data"][0]["fid"]
# Poi richiedi il dettaglio:
detail = api_get(f"parcels/{fid}", {"include": "all"})

# --- Esempio 4: Ricerca per foglio/particella ---
result = api_get("parcels/search", {
    "comune": "Roma", "foglio": "481", "limit": 10
})

# --- Esempio 5: Geocoding diretto ---
result = api_get("geocode/search", {"q": "Via del Corso", "city": "Roma", "limit": 5})

# --- Esempio 6: Geocoding inverso ---
result = api_get("geocode/reverse", {"lat": 41.9028, "lng": 12.4964, "radius": 100})

# --- Esempio 7: Bounding box ---
result = api_get("parcels/locate", {
    "bbox": "12.494,41.900,12.498,41.905", "limit": 50
})

# --- Esempio 8: Elenco comuni di una provincia ---
result = api_get("admin/municipalities", {"province": "Roma"})
```

### cURL

```bash
# Variabili
KEY="zrn_YOUR_API_KEY"
BASE="https://api.zornade.com/api/v2"

# Dettaglio particella completo
curl -H "x-api-key: $KEY" \
  "$BASE/parcels/28009975?include=all"

# Solo rischio e economia
curl -H "x-api-key: $KEY" \
  "$BASE/parcels/28009975?include=risk,economics"

# Localizza da coordinate
curl -H "x-api-key: $KEY" \
  "$BASE/parcels/locate?lat=41.9028&lng=12.4964&limit=1"

# Ricerca catastale
curl -H "x-api-key: $KEY" \
  "$BASE/parcels/search?comune=Roma&foglio=481&limit=5"

# Geocoding
curl -H "x-api-key: $KEY" \
  "$BASE/geocode/search?q=Via+del+Corso&city=Roma&limit=5"
```

---

## Note per lo sviluppatore del plugin QGIS

1. **Autenticazione:** un solo header obbligatorio, `x-api-key`, con il token personale.

2. **Geometria:** il campo `geometry` nella risposta è un oggetto GeoJSON standard (`Polygon`). In QGIS può essere convertito direttamente in `QgsGeometry` con `QgsGeometry.fromWkt(ogr.CreateGeometryFromJson(json.dumps(geom)).ExportToWkt())` o tramite `QgsJsonUtils`.

3. **Sezioni selettive:** per ridurre payload e latenza, specificare solo le sezioni necessarie nel parametro `include`. Esempio: `include=basic,risk,economics` anziché `all`.

4. **Rate limiting:** con 1000 richieste/ora, un workflow tipico (locate + detail per ogni particella) consuma 2 richieste per particella. Gestire `429` con retry dopo il tempo indicato in `retry_after_seconds`.

5. **Null handling:** tutti i campi delle sezioni possono essere `null`. Il plugin deve gestire i `null` gracefully (non fare `.get()` senza default su campi annidati).

6. **User-Agent:** usare un User-Agent identificativo (es. `ZornadeQGISPlugin/3.0`) per tracking analytics.

7. **Timeout:** consigliato 30 secondi per le richieste di dettaglio particella e geocoding.

8. **Simple Analytics tracking (opzionale):** per tracciare l'utilizzo del plugin su Simple Analytics, inviare un evento server-side:
   ```python
   import urllib.request, json
   data = json.dumps({
       "type": "event",
       "hostname": "app.zornade.com",
       "event": "qgis_api_call",
       "path": "/api/v2/parcels/" + str(fid),
       "ua": "ZornadeQGISPlugin/3.0",
       "source": "qgis-plugin"
   }).encode()
   req = urllib.request.Request(
       "https://queue.simpleanalyticscdn.com/events",
       data=data, method="POST"
   )
   req.add_header("Content-Type", "application/json")
   try:
       urllib.request.urlopen(req, timeout=5)
   except:
       pass  # Non bloccare il flusso
   ```
