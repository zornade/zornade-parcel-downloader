# Zornade — Particelle Catastali per QGIS

Plugin QGIS professionale per scaricare **particelle catastali italiane arricchite** tramite le [API v2 gratuite di Zornade](https://zornade.com/api-particelle-catastali).

![Zornade](icon.png)

## Funzionalità

- **Ricerca multi-modale**: per coordinate GPS, indirizzo (geocoding integrato), vista mappa (bbox adattivo con quadtree), o riferimento catastale (codice Belfiore + foglio + particella)
- **Map picking**: clicca direttamente sulla mappa per selezionare il punto di ricerca
- **Dati arricchiti per ogni particella** (35 campi):
  - Geometria accurata (Polygon/MultiPolygon)
  - Uso suolo CORINE Land Cover (codice, classe, sottoclasse, descrizione)
  - Dati catastali (foglio, sezione urbana, CAP, indirizzo)
  - Rischio sismico (zona 1–4, PGA), alluvione e frana
  - Subsidenza (velocità mm/anno, classe di rischio, direzione)
  - Valutazione immobiliare OMI (prezzo acquisto e affitto min/max €/m²)
- **Simbologia professionale**: renderer categorizzato per uso suolo CORINE (5 classi L1), zona sismica (4 classi), subsidenza (5 classi)
- **Download asincrono**: QgsTask con progress bar, retry automatico su errori server
- **Interfaccia Qt6**: branding Zornade, UX pulita e intuitiva

## Requisiti

- **QGIS** 3.28+
- **Token API Zornade** (gratuito) — generalo su [app.zornade.com](https://app.zornade.com)

## Installazione

### Da ZIP

1. Scarica l'ultima release `.zip` da [GitHub Releases](https://github.com/menimenocchio/zornade-parcel-downloader/releases)
2. In QGIS: **Plugin → Gestisci e Installa Plugin → Installa da ZIP**
3. Seleziona il file `.zip` scaricato

### Da sorgente

```bash
git clone https://github.com/menimenocchio/zornade-parcel-downloader.git
cd zornade-parcel-downloader
make deploy
```

## Guida Rapida

1. **Ottieni un token**: registrati su [app.zornade.com](https://app.zornade.com) e genera un token API con scope `parcels:read` e `geocoding:read`
2. **Apri il plugin**: clicca sull'icona Zornade nella toolbar o vai su **Web → Zornade → Particelle Catastali**
3. **Inserisci il token**: incolla il token nel campo dedicato e clicca "Salva"
4. **Cerca**: scegli il metodo di ricerca (coordinate, indirizzo, o catastale) e clicca "Cerca Particelle"
5. **Seleziona e scarica**: spunta le particelle desiderate e clicca "Scarica Selezionate"
6. Il layer viene creato automaticamente con simbologia Zornade

## Simbologia Disponibile

| Modalità | Campo | Descrizione |
|---|---|---|
| **Uso Suolo (CORINE)** | `land_cover_class` | 5 classi Level 1: Superfici artificiali, agricole, boscate, zone umide, corpi idrici |
| **Zona Sismica** | `seismic_zone` | Zone 1–4 (1 = rischio massimo, 4 = minimo) |
| **Rischio Subsidenza** | `subsidence_risk_class` | Classi 1–5 con scala cromatica graduata |

## Attributi Particella

| Campo | Tipo | Descrizione |
|---|---|---|
| `fid` | Integer | ID univoco particella |
| `gml_id` | String | Identificativo GML |
| `label` | String | Etichetta catastale |
| `cadastral_reference` | String | Riferimento catastale completo |
| `municipality` | String | Nome comune |
| `municipality_code` | String | Codice comune (Belfiore) |
| `province` | String | Provincia |
| `region` | String | Regione |
| `area_m2` | Double | Superficie in m² |
| `centroid_lat` | Double | Latitudine centroide |
| `centroid_lng` | Double | Longitudine centroide |
| `foglio` | String | Foglio catastale |
| `sezione_urbana` | String | Sezione urbana |
| `postal_code` | String | CAP |
| `address` | String | Indirizzo |
| `seismic_zone` | Integer | Zona sismica (1–4) |
| `pga` | Double | Accelerazione di picco al suolo |
| `flood_level` | String | Livello rischio alluvione |
| `landslide_level` | String | Livello rischio frana |
| `subsidence_velocity` | Double | Velocità subsidenza (mm/anno) |
| `subsidence_risk_class` | Integer | Classe rischio subsidenza (1–5) |
| `subsidence_risk_label` | String | Etichetta rischio subsidenza |
| `subsidence_direction` | String | Direzione subsidenza |
| `land_cover_code` | String | Codice CORINE uso suolo |
| `land_cover_class` | String | Classe CORINE Level 1 |
| `land_cover_subclass` | String | Sottoclasse uso suolo |
| `land_cover_desc` | String | Descrizione uso suolo |
| `val_zone` | String | Zona OMI |
| `val_zone_desc` | String | Descrizione zona OMI |
| `val_property_type` | String | Tipo immobile |
| `val_purchase_min` | Double | Prezzo acquisto minimo (€/m²) |
| `val_purchase_max` | Double | Prezzo acquisto massimo (€/m²) |
| `val_rental_min` | Double | Affitto minimo (€/m²) |
| `val_rental_max` | Double | Affitto massimo (€/m²) |

## API Zornade v2

Le API sono **100% gratuite** con 1.000 richieste/ora. Endpoint utilizzati:

- `GET /api/v2/parcels/locate` — Localizza particelle per coordinate
- `GET /api/v2/parcels/search` — Cerca per riferimento catastale
- `GET /api/v2/parcels/{id}` — Profilo arricchito particella
- `GET /api/v2/geocode/search` — Geocoding diretto
- `GET /api/v2/geocode/reverse` — Geocoding inverso

Documentazione completa: [zornade.com/api-particelle-catastali](https://zornade.com/api-particelle-catastali)

## Licenza

GPL-2.0-or-later — [LICENSE](LICENSE)

## Supporto

- **Issues**: [GitHub Issues](https://github.com/menimenocchio/zornade-parcel-downloader/issues)
- **Documentazione API**: [zornade.com/documentation](https://zornade.com/documentation)
- **Contatti**: [zornade.com/servizi-sviluppo-software#contact](https://zornade.com/servizi-sviluppo-software#contact)

---

**Zornade** — L'ecosistema completo per dati territoriali italiani. 83M+ particelle catastali.
