"""
Zornade — Plugin QGIS per Particelle Catastali Arricchite.

Plugin class principale: gestisce toolbar, menu e apertura del dialog.
Usa le API v2 gratuite di Zornade (https://zornade.com).
"""

import os

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


class ZornadeParcelDownloader:
    """Plugin QGIS per particelle catastali arricchite via Zornade API v2."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "&Zornade"
        self.dialog = None

    @staticmethod
    def tr(message):
        return QCoreApplication.translate("ZornadeParcelDownloader", message)

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        icon = QIcon(icon_path)
        action = QAction(
            icon,
            self.tr("Zornade — Particelle Catastali"),
            self.iface.mainWindow(),
        )
        action.setStatusTip(
            self.tr("Scarica particelle catastali arricchite"))
        action.setWhatsThis(
            self.tr(
                "Scarica particelle catastali italiane arricchite "
                "con dati geografici, demografici, economici e di rischio "
                "tramite le API v2 gratuite di Zornade."))
        action.triggered.connect(self.run)
        self.iface.addToolBarIcon(action)
        self.iface.addPluginToWebMenu(self.menu, action)
        self.actions.append(action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginWebMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        if self.dialog:
            self.dialog.close()
            self.dialog = None

    def run(self):
        from .zornade_dialog import ZornadeDialog

        if self.dialog is None or not self.dialog.isVisible():
            self.dialog = ZornadeDialog(self.iface)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
