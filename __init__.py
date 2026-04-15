"""
Zornade — Plugin QGIS per Particelle Catastali Arricchite.

Scarica particelle catastali italiane arricchite con dati geografici,
demografici, economici e di rischio tramite le API v2 di Zornade.

https://zornade.com
Licenza: GPL-2.0-or-later
"""


def classFactory(iface):
    from .zornade_parcel_downloader import ZornadeParcelDownloader
    return ZornadeParcelDownloader(iface)
