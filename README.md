# Zornade Particelle Catastali per QGIS

[![QGIS](https://img.shields.io/badge/QGIS-3.28%2B-3b9c3b)](https://plugins.qgis.org/plugins/zornade_parcel_downloader/)
[![Plugin](https://img.shields.io/badge/Plugin%20ID-3930-blue)](https://plugins.qgis.org/plugins/zornade_parcel_downloader/)
[![Licenza](https://img.shields.io/badge/Licenza-GPL--2.0--or--later-lightgrey)](LICENSE)

Scarica le particelle catastali italiane già arricchite: rischio sismico,
idrogeologico e di subsidenza, quotazioni OMI, uso del suolo, demografia,
redditi, potenziale fotovoltaico. Funziona per coordinate, per indirizzo, per
vista mappa o per riferimento catastale, e restituisce un layer pronto da
simbolizzare.

Serve a geometri, uffici tecnici, studi che fanno due diligence immobiliare, e a
chiunque debba mettere su una mappa un'area senza passare dal portale
dell'Agenzia delle Entrate.

Il plugin è nel repository ufficiale di QGIS (ID 3930), con oltre 4.300 download
a novembre 2026.

## Installazione

**Dal Plugin Manager di QGIS**, che è la via normale.

1. QGIS → **Plugin → Gestisci e installa plugin**
2. Cerca `Zornade`
3. **Installa plugin**
4. L'icona compare nella toolbar, e la voce in **Web → Zornade → Particelle Catastali**

Installazione da file ZIP, per una versione non ancora pubblicata:

1. Scarica l'ultima release da [GitHub Releases](https://github.com/zornade/zornade-parcel-downloader/releases)
2. QGIS → **Plugin → Gestisci e installa plugin → Installa da ZIP**
3. Seleziona il file scaricato

Da sorgente, per chi sviluppa:

```bash
git clone https://github.com/zornade/zornade-parcel-downloader.git
cd zornade-parcel-downloader
make deploy
```

## Token gratuito

Il plugin interroga le API Zornade, che sono gratuite con 10.000 richieste
all'ora per token.

1. Registrati su [app.zornade.com](https://app.zornade.com)
2. Genera un token con gli scope `parcels:read` e `geocoding:read`
3. Incolla il token nel campo del plugin e premi **Salva**

## Come si cerca

| Modalità | Come | Quando serve |
|---|---|---|
| Coordinate | latitudine e longitudine, o clic sulla mappa | quando le coordinate sono note |
| Indirizzo | geocoding integrato | quando si parte da una via e un civico |
| Vista mappa | riquadro corrente, suddiviso con un quadtree adattivo | per un'area intera |
| Riferimento catastale | comune (ricerca fuzzy), foglio, particella, sezione | quando si ha la visura in mano |

## Cosa arriva con ogni particella

Ogni particella porta **oltre 110 campi, in 20 sezioni**. Questi sono i gruppi
principali.

| Gruppo | Cosa contiene |
|---|---|
| Geometria e identificativi | poligono o multipoligono, foglio, particella, sezione urbana, `gml_id`, riferimento catastale, comune, provincia, regione, area in m² |
| Rischio | zona sismica da 1 a 4 e PGA, pericolosità alluvioni e frane ISPRA, subsidenza con velocità, accelerazione, classe e direzione |
| Valutazione | quotazioni OMI di acquisto e affitto min/max in €/m², semestre precedente, serie storica dal 2015 al 2025 con rendimento lordo |
| Territorio | quota, pendenza, esposizione, rugosità, uso del suolo CORINE, Urban Atlas, erosione costiera, beni culturali |
| Popolazione e edifici | stime HRSL e WorldPop, censimento 2021 per età, istruzione, occupazione, stranieri, famiglie, abitazioni |
| Economia | reddito medio, indice di Gini, indice di accessibilità PIR, fasce di reddito |
| Fotovoltaico | potenza installabile, resa annua, tempo di ritorno, VAN, LCOE, classe di convenienza (JRC PVGIS-SARAH3) |
| Luce notturna | radianza e classe VIIRS Black Marble |

L'elenco completo dei campi, sezione per sezione, è nella documentazione delle
API: [zornade.com/api-particelle-catastali](https://zornade.com/api-particelle-catastali).

## Simbologia inclusa

| Simbologia | Campo | Classi |
|---|---|---|
| Uso del suolo CORINE | `land_cover_class` | 5 classi di primo livello |
| Zona sismica | `seismic_zone` | 4 classi |
| Rischio subsidenza | `subsidence_risk_class` | 5 classi |

## Costi e licenze

**Il dato è gratuito.** Consultare, analizzare e stampare non costa nulla: 10.000
richieste all'ora per token, cinque token per utente. Sul piano gratuito resta
visibile l'attribuzione «Dati elaborati da Zornade».

**La ridistribuzione no.** Chi rivende il dato o lo integra in un prodotto
proprio ha bisogno della [licenza commerciale](https://zornade.com/licenza-commerciale).
Le attribuzioni delle fonti (Agenzia delle Entrate, ISPRA, INGV, ISTAT,
OpenStreetMap) restano obbligatorie in ogni caso.

**Il codice del plugin** è GPL-2.0-or-later, vedi [LICENSE](LICENSE).
Copyright (C) 2024-2026 Zornade. Il testo integrale della licenza è nel file
LICENSE, senza modifiche, come richiesto dai termini stessi della GPL.

## Link

- Scheda nel repository QGIS, con il pulsante di installazione: [plugins.qgis.org/plugins/zornade_parcel_downloader](https://plugins.qgis.org/plugins/zornade_parcel_downloader/)
- Documentazione delle API: [zornade.com/documentation](https://zornade.com/documentation)
- Modifiche per versione: [CHANGELOG.md](CHANGELOG.md). Lo stesso elenco lo mostra il Plugin Manager alla prima apertura dopo un aggiornamento.
- Problemi e richieste: [GitHub Issues](https://github.com/zornade/zornade-parcel-downloader/issues)
- Dataset aperti scaricabili: [zornade.com/data-downloads](https://zornade.com/data-downloads)

## Endpoint usati

- `GET /api/v2/parcels/locate` per coordinate o riquadro
- `GET /api/v2/parcels/search` per riferimento catastale
- `GET /api/v2/parcels/{id}` per il profilo arricchito
- `GET /api/v2/geocode/search` e `GET /api/v2/geocode/reverse` per il geocoding
