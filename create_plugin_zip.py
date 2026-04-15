#!/usr/bin/env python3
"""Crea lo ZIP di installazione per il plugin QGIS Zornade."""

import zipfile
from pathlib import Path


def create_plugin_zip():
    plugin_name = "zornade_parcel_downloader"

    files = [
        "__init__.py",
        "zornade_parcel_downloader.py",
        "zornade_dialog.py",
        "zornade_api.py",
        "zornade_sketching.py",
        "metadata.txt",
        "icon.png",
        "README.md",
        "LICENSE",
    ]

    plugin_dir = Path(__file__).parent
    zip_path = plugin_dir / f"{plugin_name}.zip"

    print(f"Creazione ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in files:
            fp = plugin_dir / filename
            if fp.exists():
                zf.write(fp, f"{plugin_name}/{filename}")
                print(f"  + {filename}")
            else:
                print(f"  ⚠ Non trovato: {filename}")

    print(f"\n✅ ZIP creato: {zip_path}")
    print("Installa in QGIS: Plugin → Gestisci e Installa → Installa da ZIP")
    return zip_path


if __name__ == "__main__":
    create_plugin_zip()
