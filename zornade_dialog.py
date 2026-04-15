"""
Zornade Dialog — Interfaccia Qt6 per ricerca e download particelle.

UI nativa QGIS, ricerca multi-modale (coordinate, bbox, catastale),
mappa picking, tabella risultati, progress bar, gestione token.
"""

import json
import math
from typing import Optional, List, Dict, Any

from qgis.PyQt.QtCore import Qt, QSettings, QUrl, QVariant
from qgis.PyQt.QtGui import QDesktopServices
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox,
    QTabWidget, QWidget, QGroupBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QComboBox,
    QMessageBox, QApplication,
    QAbstractItemView,
)
from qgis.core import (
    Qgis, QgsApplication, QgsMessageLog, QgsTask,
    QgsProject, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsVectorLayer, QgsFeature,
    QgsGeometry, QgsField, QgsFields,
)
from qgis.gui import QgsMapToolEmitPoint

from .zornade_api import ZornadeApiClient, ZornadeApiError
from .zornade_sketching import (
    apply_sketching, STYLE_OPTIONS, STYLE_CLASSIFICATION,
)


# ======================================================================
# Settings Keys
# ======================================================================

SETTINGS_TOKEN_KEY = "zornade/api_token"
SETTINGS_STYLE_KEY = "zornade/default_style"




# ======================================================================
# Download Task (QgsTask — QGIS best practice)
# ======================================================================

class DownloadTask(QgsTask):
    """QgsTask per il download asincrono delle particelle arricchite.

    Usa QgsTask invece di QThread come da best practice QGIS:
    - run() eseguito in background, restituisce True/False
    - finished() eseguito sul thread principale (sicuro per GUI)
    - isCanceled() per annullamento cooperativo
    - setProgress() per aggiornamento progressi
    """

    def __init__(self, description: str, api: ZornadeApiClient,
                 parcel_ids: list):
        super().__init__(description, QgsTask.CanCancel)
        self.api = api
        self.parcel_ids = parcel_ids
        self.results: list = []
        self.error_msg: Optional[str] = None

    MAX_RETRIES = 3
    RETRY_WAIT = 2  # seconds between retries

    def run(self):
        import time
        total = len(self.parcel_ids)
        for i, pid in enumerate(self.parcel_ids):
            if self.isCanceled():
                return False
            last_exc = None
            for attempt in range(self.MAX_RETRIES):
                if self.isCanceled():
                    return False
                try:
                    resp = self.api.get_parcel_detail(pid)
                    data = resp.get("data", resp)
                    self.results.append(data)
                    self.setProgress((i + 1) * 100.0 / total)
                    last_exc = None
                    break
                except ZornadeApiError as exc:
                    last_exc = exc
                    if exc.status >= 500 and attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_WAIT * (attempt + 1))
                        continue
                    self.error_msg = (
                        f"Errore particella {pid}: {exc} "
                        f"(HTTP {exc.status})")
                    return False
                except Exception as exc:
                    self.error_msg = f"Errore imprevisto per {pid}: {exc}"
                    return False
        return True

    def finished(self, result):
        pass  # Gestito tramite taskCompleted / taskTerminated


# ======================================================================
# Main Dialog
# ======================================================================

class ZornadeDialog(QDialog):
    """Dialog principale per ricerca e download particelle catastali."""

    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setWindowTitle("Zornade — Particelle Catastali")
        self.setMinimumSize(580, 600)
        self.resize(620, 680)

        self._api: Optional[ZornadeApiClient] = None
        self._task: Optional[DownloadTask] = None
        self._search_results: List[Dict] = []
        self._map_tool: Optional[QgsMapToolEmitPoint] = None
        self._prev_map_tool = None

        self._build_ui()
        self._load_settings()
        self._update_api_client()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(10, 10, 10, 10)

        # ── Token section (collapsible) ──
        token_header = QHBoxLayout()
        self.btn_toggle_token_section = QPushButton("Token API Zornade")
        self.btn_toggle_token_section.setFlat(True)
        self.btn_toggle_token_section.setCursor(
            Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_token_section.clicked.connect(
            self._toggle_token_section)
        token_header.addWidget(self.btn_toggle_token_section)
        self.token_status = QLabel("")
        token_header.addWidget(self.token_status)
        token_header.addStretch()
        link_btn = QPushButton("Genera token")
        link_btn.setFlat(True)
        link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        link_btn.setStyleSheet("color: #14b8a6; text-decoration: underline;")
        link_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://app.zornade.com")))
        token_header.addWidget(link_btn)
        root.addLayout(token_header)

        self.token_content = QWidget()
        tc_lay = QHBoxLayout(self.token_content)
        tc_lay.setContentsMargins(0, 0, 0, 0)
        tc_lay.setSpacing(4)
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText(
            "zrn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.textChanged.connect(self._on_token_changed)
        tc_lay.addWidget(self.token_input, 1)
        self.btn_toggle_token = QPushButton("Mostra")
        self.btn_toggle_token.setFixedWidth(60)
        self.btn_toggle_token.clicked.connect(self._toggle_token_visibility)
        tc_lay.addWidget(self.btn_toggle_token)
        self.btn_save_token = QPushButton("Salva")
        self.btn_save_token.clicked.connect(self._save_token)
        tc_lay.addWidget(self.btn_save_token)
        self.btn_verify_token = QPushButton("Verifica")
        self.btn_verify_token.clicked.connect(self._verify_token)
        tc_lay.addWidget(self.btn_verify_token)
        root.addWidget(self.token_content)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        # ── Search section ──
        search_group = QGroupBox("Ricerca Particelle")
        sg_lay = QVBoxLayout(search_group)
        sg_lay.setSpacing(6)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_coords_tab(), "Coordinate")
        self.tabs.addTab(self._create_extent_tab(), "Vista Mappa")
        self.tabs.addTab(self._create_cadastral_tab(), "Catastale")
        sg_lay.addWidget(self.tabs)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Max risultati:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 1000)
        self.limit_spin.setValue(500)
        search_row.addWidget(self.limit_spin)
        search_row.addStretch()
        self.btn_search = QPushButton("Cerca Particelle")
        self.btn_search.clicked.connect(self._do_search)
        search_row.addWidget(self.btn_search)
        sg_lay.addLayout(search_row)

        root.addWidget(search_group)

        # ── Results section ──
        results_group = QGroupBox("Risultati")
        rg_lay = QVBoxLayout(results_group)
        rg_lay.setSpacing(4)

        toolbar_row = QHBoxLayout()
        self.btn_select_all = QPushButton("Seleziona tutti")
        self.btn_select_all.clicked.connect(self._select_all)
        toolbar_row.addWidget(self.btn_select_all)
        self.btn_deselect_all = QPushButton("Deseleziona tutti")
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        toolbar_row.addWidget(self.btn_deselect_all)
        toolbar_row.addStretch()
        self.results_count = QLabel("Nessun risultato")
        toolbar_row.addWidget(self.results_count)
        rg_lay.addLayout(toolbar_row)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(
            ["", "FID", "Comune", "Etichetta", "Area m\u00b2"])
        hh = self.results_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.results_table.setColumnWidth(0, 30)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setMinimumHeight(140)
        rg_lay.addWidget(self.results_table, 1)  # stretch factor

        root.addWidget(results_group, 1)  # results group takes stretch

        # ── Options row ──
        opts_row = QHBoxLayout()
        opts_row.addWidget(QLabel("Layer:"))
        self.layer_name_input = QLineEdit("Zornade Particelle")
        opts_row.addWidget(self.layer_name_input, 1)
        opts_row.addWidget(QLabel("Simbologia:"))
        self.style_combo = QComboBox()
        for key, label in STYLE_OPTIONS.items():
            self.style_combo.addItem(label, key)
        opts_row.addWidget(self.style_combo)
        root.addLayout(opts_row)

        # ── Progress ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        root.addWidget(self.status_label)

        # ── Bottom buttons ──
        btn_row = QHBoxLayout()
        self.btn_download = QPushButton("Scarica Selezionate")
        self.btn_download.setEnabled(False)
        self.btn_download.clicked.connect(self._do_download)
        btn_row.addWidget(self.btn_download)

        self.btn_cancel = QPushButton("Annulla Download")
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_download)
        btn_row.addWidget(self.btn_cancel)

        btn_row.addStretch()

        btn_close = QPushButton("Chiudi")
        btn_close.clicked.connect(self.close)
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)

    # ---------- Tab: Coordinates ----------

    def _create_coords_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(8)
        form.setContentsMargins(8, 12, 8, 8)

        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("es. 41.9028")
        form.addRow("Latitudine:", self.lat_input)

        self.lng_input = QLineEdit()
        self.lng_input.setPlaceholderText("es. 12.4964")
        form.addRow("Longitudine:", self.lng_input)

        btns = QHBoxLayout()
        btn_map_center = QPushButton("Centro mappa")
        btn_map_center.setToolTip(
            "Usa il centro della vista mappa corrente")
        btn_map_center.clicked.connect(self._use_map_center)
        btns.addWidget(btn_map_center)

        btn_pick_map = QPushButton("Prendi dalla mappa")
        btn_pick_map.setToolTip(
            "Clicca sulla mappa per selezionare un punto")
        btn_pick_map.clicked.connect(self._pick_from_map)
        btns.addWidget(btn_pick_map)
        btns.addStretch()
        form.addRow("", btns)

        return w

    # ---------- Tab: Map Extent ----------

    def _create_extent_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(8)
        form.setContentsMargins(8, 12, 8, 8)

        info = QLabel(
            "Cerca tutte le particelle nell'area visibile\n"
            "della mappa (griglia multi-punto sul bbox).")
        info.setWordWrap(True)
        form.addRow(info)

        self.extent_info = QLabel("")
        self.extent_info.setEnabled(False)
        form.addRow("Estensione:", self.extent_info)

        btn_refresh = QPushButton("Aggiorna dal canvas")
        btn_refresh.setToolTip(
            "Legge l'estensione della vista mappa attuale")
        btn_refresh.clicked.connect(self._refresh_extent_info)
        form.addRow("", btn_refresh)

        return w

    def _refresh_extent_info(self):
        extent = self._get_canvas_extent_4326()
        if extent:
            self.extent_info.setText(
                f"{extent.yMinimum():.4f}, {extent.xMinimum():.4f}  -  "
                f"{extent.yMaximum():.4f}, {extent.xMaximum():.4f}")

    def _get_canvas_extent_4326(self):
        """Restituisce l'estensione del canvas in EPSG:4326."""
        canvas = self.iface.mapCanvas()
        extent = canvas.extent()
        crs_src = canvas.mapSettings().destinationCrs()
        crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
        if crs_src != crs_dst:
            transform = QgsCoordinateTransform(
                crs_src, crs_dst, QgsProject.instance())
            extent = transform.transformBoundingBox(extent)
        return extent

    # ---------- Tab: Cadastral Reference ----------

    def _create_cadastral_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(8)
        form.setContentsMargins(8, 12, 8, 8)

        self.municipality_input = QLineEdit()
        self.municipality_input.setPlaceholderText(
            "es. H501 (codice Belfiore)")
        form.addRow("Codice Comune*:", self.municipality_input)

        self.sheet_input = QLineEdit()
        self.sheet_input.setPlaceholderText("opzionale")
        form.addRow("Foglio:", self.sheet_input)

        self.parcel_input = QLineEdit()
        self.parcel_input.setPlaceholderText("opzionale")
        form.addRow("Particella:", self.parcel_input)

        info = QLabel("* Codice catastale (Belfiore) obbligatorio")
        info.setEnabled(False)
        form.addRow("", info)

        return w

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _load_settings(self):
        s = QSettings()
        token = s.value(SETTINGS_TOKEN_KEY, "")
        if token:
            self.token_input.setText(token)
            # Auto-collapse token section when already configured
            self.token_content.setVisible(False)
        style_key = s.value(SETTINGS_STYLE_KEY, STYLE_CLASSIFICATION)
        idx = self.style_combo.findData(style_key)
        if idx >= 0:
            self.style_combo.setCurrentIndex(idx)

    def _save_token(self):
        token = self.token_input.text().strip()
        QSettings().setValue(SETTINGS_TOKEN_KEY, token)
        self._update_api_client()
        self.token_status.setText("Token salvato")
        self.token_status.setStyleSheet("color: #059669;")

    def _toggle_token_section(self):
        vis = not self.token_content.isVisible()
        self.token_content.setVisible(vis)

    def _toggle_token_visibility(self):
        if self.token_input.echoMode() == QLineEdit.EchoMode.Password:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_token.setText("Nascondi")
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_token.setText("Mostra")

    def _on_token_changed(self):
        self.token_status.setText("")
        self._update_api_client()

    def _update_api_client(self):
        token = self.token_input.text().strip()
        if token:
            self._api = ZornadeApiClient(token)
        else:
            self._api = None

    def _verify_token(self):
        if not self._api:
            self.token_status.setText("Inserisci un token")
            self.token_status.setStyleSheet("color: #DC2626;")
            return
        self.token_status.setText("Verifica in corso...")
        self.token_status.setStyleSheet("color: #64748b;")
        QApplication.processEvents()
        try:
            self._api.geocode_search("Roma", limit=1)
            self.token_status.setText("Token valido")
            self.token_status.setStyleSheet("color: #059669;")
        except ZornadeApiError as exc:
            if exc.status in (401, 403):
                self.token_status.setText(
                    f"Token non valido ({exc.code or exc.status})")
            else:
                self.token_status.setText(
                    f"Errore API: {exc} (HTTP {exc.status})")
            self.token_status.setStyleSheet("color: #DC2626;")
        except Exception as exc:
            self.token_status.setText(f"Errore rete: {exc}")
            self.token_status.setStyleSheet("color: #DC2626;")

    # ------------------------------------------------------------------
    # Map Tools
    # ------------------------------------------------------------------

    def _use_map_center(self):
        canvas = self.iface.mapCanvas()
        center = canvas.center()
        crs_src = canvas.mapSettings().destinationCrs()
        crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
        if crs_src != crs_dst:
            transform = QgsCoordinateTransform(
                crs_src, crs_dst, QgsProject.instance())
            center = transform.transform(center)
        self.lat_input.setText(f"{center.y():.6f}")
        self.lng_input.setText(f"{center.x():.6f}")
        self.tabs.setCurrentIndex(0)

    def _pick_from_map(self):
        canvas = self.iface.mapCanvas()
        self._prev_map_tool = canvas.mapTool()
        self._map_tool = QgsMapToolEmitPoint(canvas)
        self._map_tool.canvasClicked.connect(self._on_map_clicked)
        canvas.setMapTool(self._map_tool)
        self.hide()
        self.iface.messageBar().pushInfo(
            "Zornade",
            "Clicca sulla mappa per selezionare un punto, "
            "poi il dialog si riaprirà.")

    def _on_map_clicked(self, point, button):
        canvas = self.iface.mapCanvas()
        crs_src = canvas.mapSettings().destinationCrs()
        crs_dst = QgsCoordinateReferenceSystem("EPSG:4326")
        if crs_src != crs_dst:
            transform = QgsCoordinateTransform(
                crs_src, crs_dst, QgsProject.instance())
            point = transform.transform(point)
        self.lat_input.setText(f"{point.y():.6f}")
        self.lng_input.setText(f"{point.x():.6f}")
        # Restore previous tool
        if self._prev_map_tool:
            canvas.setMapTool(self._prev_map_tool)
        self._prev_map_tool = None
        self._map_tool = None
        self.tabs.setCurrentIndex(0)
        self.show()
        self.activateWindow()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _do_search(self):
        if not self._api:
            QMessageBox.warning(
                self, "Token mancante",
                "Inserisci e salva un token API valido prima "
                "di effettuare ricerche.\n\n"
                "Genera il tuo token su app.zornade.com")
            return

        self.status_label.setText("Ricerca in corso...")
        self.btn_search.setEnabled(False)
        QApplication.processEvents()

        try:
            tab_idx = self.tabs.currentIndex()
            limit = self.limit_spin.value()

            if tab_idx == 0:  # Coordinates
                lat_text = self.lat_input.text().strip()
                lng_text = self.lng_input.text().strip()
                if not lat_text or not lng_text:
                    QMessageBox.warning(
                        self, "Errore",
                        "Inserisci latitudine e longitudine.")
                    return
                try:
                    lat = float(lat_text)
                    lng = float(lng_text)
                except ValueError:
                    QMessageBox.warning(
                        self, "Errore",
                        "Latitudine e longitudine devono essere numeri.")
                    return
                resp = self._api.locate_parcels(lat, lng, limit)

            elif tab_idx == 1:  # Map Extent (bbox multi-point)
                extent = self._get_canvas_extent_4326()
                if not extent or extent.isEmpty():
                    QMessageBox.warning(
                        self, "Errore",
                        "Impossibile leggere l'estensione della mappa.")
                    return
                self.extent_info.setText(
                    f"{extent.yMinimum():.4f}, {extent.xMinimum():.4f}  -  "
                    f"{extent.yMaximum():.4f}, {extent.xMaximum():.4f}")
                resp = self._bbox_multi_search(extent, limit)

            elif tab_idx == 2:  # Cadastral
                municipality = self.municipality_input.text().strip()
                if not municipality:
                    QMessageBox.warning(
                        self, "Errore",
                        "Il codice catastale del comune è obbligatorio.")
                    return
                sheet = self.sheet_input.text().strip() or None
                parcel = self.parcel_input.text().strip() or None
                resp = self._api.search_parcels(
                    municipality, sheet, parcel, limit)
            else:
                return

            self._process_search_results(resp)

        except ZornadeApiError as exc:
            self.status_label.setText(f"Errore: {exc}")
            QgsMessageLog.logMessage(
                f"Errore ricerca: {exc} (HTTP {exc.status})",
                "Zornade", Qgis.MessageLevel.Warning)
            if exc.status == 401:
                QMessageBox.warning(
                    self, "Accesso negato",
                    "Token non valido o scaduto.\n"
                    "Genera un nuovo token su app.zornade.com")
        except Exception as exc:
            self.status_label.setText(f"Errore: {exc}")
            QgsMessageLog.logMessage(
                f"Errore imprevisto ricerca: {exc}",
                "Zornade", Qgis.MessageLevel.Critical)
        finally:
            self.btn_search.setEnabled(True)

    def _bbox_multi_search(self, extent, limit: int) -> Dict:
        """Cerca particelle con bbox nativa e subdivide adattivamente.

        L'API supporta GET /parcels/locate?bbox=minLng,minLat,maxLng,maxLat
        con max 0.05 deg per lato e max 200 risultati per tile.

        Algoritmo quadtree adattivo:
        1. Divide l'extent in tile iniziali da max 0.05 deg per lato
        2. Per ogni tile satura (200 risultati = API cap), la subdivide
           in 4 quadranti e ripete la query
        3. Continua finche' nessuna tile e' satura o si raggiunge
           la dimensione minima (0.0005 deg ~ 55m)
        4. Deduplica per fid
        """
        x_min = extent.xMinimum()
        x_max = extent.xMaximum()
        y_min = extent.yMinimum()
        y_max = extent.yMaximum()

        MAX_SIDE = 0.05     # max degrees per side (API constraint)
        TILE_LIMIT = 200    # max results per tile (API cap)
        MIN_SIDE = 0.0005   # minimum tile side (~55m) to avoid infinite recursion
        MAX_QUERIES = 500   # safety limit (rate limit: 1000 req/hr)

        # Build initial tile grid (each tile <= MAX_SIDE)
        dx = x_max - x_min
        dy = y_max - y_min
        nx = max(1, math.ceil(dx / MAX_SIDE))
        ny = max(1, math.ceil(dy / MAX_SIDE))
        tile_dx = dx / nx
        tile_dy = dy / ny

        # Queue of tiles to process: (xmin, ymin, xmax, ymax)
        tile_queue = []
        for j in range(ny):
            for i in range(nx):
                tile_queue.append((
                    x_min + i * tile_dx,
                    y_min + j * tile_dy,
                    x_min + (i + 1) * tile_dx,
                    y_min + (j + 1) * tile_dy,
                ))

        seen_fids = set()
        merged = []
        tiles_queried = 0

        QgsMessageLog.logMessage(
            f"Bbox search: {dx:.5f}x{dy:.5f} deg, "
            f"{nx}x{ny}={len(tile_queue)} tile iniziali",
            "Zornade", Qgis.MessageLevel.Info)

        while tile_queue and len(merged) < limit and tiles_queried < MAX_QUERIES:
            t_xmin, t_ymin, t_xmax, t_ymax = tile_queue.pop(0)
            tiles_queried += 1

            self.status_label.setText(
                f"Scansione ({tiles_queried} query, "
                f"{len(tile_queue)} in coda)... "
                f"{len(merged)} particelle trovate")
            QApplication.processEvents()

            try:
                resp = self._api.locate_parcels_bbox(
                    t_xmin, t_ymin, t_xmax, t_ymax, TILE_LIMIT)
                data = resp.get("data", [])
                count = len(data)

                # Collect results from this tile
                for item in data:
                    fid = item.get("fid")
                    if fid is None:
                        fid = item.get("id")
                    if fid is not None and fid not in seen_fids:
                        seen_fids.add(fid)
                        merged.append(item)

                # If tile is saturated and can still be subdivided,
                # split into 4 quadrants and re-queue
                tw = t_xmax - t_xmin
                th = t_ymax - t_ymin
                if count >= TILE_LIMIT and tw > MIN_SIDE and th > MIN_SIDE:
                    mid_x = (t_xmin + t_xmax) / 2
                    mid_y = (t_ymin + t_ymax) / 2
                    tile_queue.extend([
                        (t_xmin, t_ymin, mid_x, mid_y),   # SW
                        (mid_x,  t_ymin, t_xmax, mid_y),  # SE
                        (t_xmin, mid_y,  mid_x, t_ymax),  # NW
                        (mid_x,  mid_y,  t_xmax, t_ymax), # NE
                    ])
                    QgsMessageLog.logMessage(
                        f"Tile satura ({count}), subdivisa in 4 "
                        f"({tw:.5f}x{th:.5f} -> {tw/2:.5f}x{th/2:.5f})",
                        "Zornade", Qgis.MessageLevel.Info)

            except ZornadeApiError as exc:
                QgsMessageLog.logMessage(
                    f"Tile {tiles_queried} fallita: {exc}",
                    "Zornade", Qgis.MessageLevel.Warning)

        # Trim to user limit
        if len(merged) > limit:
            merged = merged[:limit]

        if tiles_queried >= MAX_QUERIES and tile_queue:
            QgsMessageLog.logMessage(
                f"Limite query raggiunto ({MAX_QUERIES}). "
                f"{len(tile_queue)} tile non processate. "
                f"Riduci l'area di ricerca per risultati completi.",
                "Zornade", Qgis.MessageLevel.Warning)

        QgsMessageLog.logMessage(
            f"Bbox search completata: {len(merged)} particelle uniche "
            f"da {tiles_queried} query API",
            "Zornade", Qgis.MessageLevel.Info)

        return {"data": merged,
                "meta": {"mode": "bbox", "count": len(merged)}}

    def _process_search_results(self, resp: Dict):
        """Popola la tabella risultati dalla risposta API."""
        raw_data = resp.get("data", [])

        self._search_results = []
        parsed = []

        for item in raw_data:
            if isinstance(item, dict):
                parsed.append(item)
            elif isinstance(item, (int, float)):
                parsed.append({"fid": int(item)})

        self._search_results = parsed

        # Populate table
        self.results_table.setRowCount(len(parsed))
        for row, item in enumerate(parsed):
            # Checkbox
            cb = QTableWidgetItem()
            cb.setFlags(Qt.ItemFlag.ItemIsUserCheckable |
                        Qt.ItemFlag.ItemIsEnabled)
            cb.setCheckState(Qt.CheckState.Checked)
            self.results_table.setItem(row, 0, cb)

            # FID
            fid = item.get("fid") or item.get("id") or "?"
            self.results_table.setItem(
                row, 1, QTableWidgetItem(str(fid)))

            # Municipality (from locate/search: dict with name)
            mun_raw = item.get("municipality")
            if isinstance(mun_raw, dict):
                mun = mun_raw.get("name", "--")
            else:
                mun = mun_raw or "--"
            self.results_table.setItem(
                row, 2, QTableWidgetItem(str(mun)))

            # Label (particella label from API v2)
            label = item.get("label") or item.get("cadastral_reference") or "--"
            self.results_table.setItem(
                row, 3, QTableWidgetItem(str(label)))

            # Area m2
            area = item.get("area_m2")
            area_str = f"{float(area):,.0f}" if area else "--"
            self.results_table.setItem(
                row, 4, QTableWidgetItem(area_str))

        count = len(parsed)
        self.results_count.setText(
            f"Trovate {count} particell{'a' if count == 1 else 'e'}")
        self.btn_download.setEnabled(count > 0)
        self.status_label.setText(
            f"Ricerca completata: {count} risultat"
            f"{'o' if count == 1 else 'i'}")

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _select_all(self):
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _get_selected_ids(self) -> list:
        """Restituisce i FID/ID delle particelle selezionate."""
        ids = []
        for row in range(self.results_table.rowCount()):
            cb = self.results_table.item(row, 0)
            if cb and cb.checkState() == Qt.CheckState.Checked:
                if row >= len(self._search_results):
                    continue
                item = self._search_results[row]
                # Use 'is not None' to handle fid=0 correctly
                pid = item.get("fid")
                if pid is None:
                    pid = item.get("id")
                if pid is None:
                    pid = item.get("parcel_id")
                if pid is not None:
                    ids.append(pid)
        return ids

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def _do_download(self):
        if not self._api:
            QMessageBox.warning(self, "Errore", "Token API non configurato.")
            return

        ids = self._get_selected_ids()
        if not ids:
            QMessageBox.information(
                self, "Nessuna selezione",
                "Seleziona almeno una particella da scaricare.")
            return

        # Save style preference
        QSettings().setValue(
            SETTINGS_STYLE_KEY,
            self.style_combo.currentData())

        # UI state
        self.btn_download.setEnabled(False)
        self.btn_search.setEnabled(False)
        self.btn_cancel.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        # Start task (QgsTask via task manager)
        task = DownloadTask(
            "Zornade - Download particelle", self._api, ids)
        task.progressChanged.connect(self._on_task_progress)
        task.taskCompleted.connect(
            lambda: self._on_download_completed())
        task.taskTerminated.connect(
            lambda: self._on_download_terminated())
        self._task = task
        QgsApplication.taskManager().addTask(task)

    def _cancel_download(self):
        if self._task:
            self._task.cancel()
        self._reset_download_ui()
        self.status_label.setText("Download annullato")

    def _on_task_progress(self, progress: float):
        if self._task:
            total = len(self._task.parcel_ids)
            current = round(progress * total / 100.0)
            self.progress_bar.setValue(int(progress))
            self.status_label.setText(
                f"Download particella {current}/{total}...")

    def _on_download_terminated(self):
        """Chiamato quando il task fallisce o viene annullato."""
        task = self._task
        self._reset_download_ui()
        if task and task.error_msg:
            QgsMessageLog.logMessage(
                task.error_msg, "Zornade", Qgis.MessageLevel.Critical)
            self.status_label.setText(f"Download fallito: {task.error_msg}")
        else:
            self.status_label.setText("Download annullato")

    def _on_download_completed(self):
        """Chiamato quando il task completa con successo."""
        task = self._task
        results = task.results if task else []
        self._reset_download_ui()
        if not results:
            self.status_label.setText("Nessun dato ricevuto")
            return

        try:
            layer = self._create_layer(results)
            if layer and layer.isValid():
                style_key = self.style_combo.currentData()
                apply_sketching(layer, style_key)
                QgsProject.instance().addMapLayer(layer)
                # Zoom to layer: CRS transform + 5% buffer
                self._zoom_to_layer(layer)
                count = layer.featureCount()
                self.status_label.setText(
                    f"Layer creato con {count} "
                    f"particell{'a' if count == 1 else 'e'}")
                QgsMessageLog.logMessage(
                    f"Layer '{layer.name()}' creato con {count} feature",
                    "Zornade", Qgis.MessageLevel.Info)
            else:
                self.status_label.setText("Impossibile creare il layer")
                QgsMessageLog.logMessage(
                    "Creazione layer fallita — layer non valido",
                    "Zornade", Qgis.MessageLevel.Warning)
        except Exception as exc:
            QgsMessageLog.logMessage(
                f"Errore creazione layer: {exc}",
                "Zornade", Qgis.MessageLevel.Critical)
            self.status_label.setText(f"Errore creazione layer: {exc}")

    def _zoom_to_layer(self, layer: QgsVectorLayer):
        """Zoom alla estensione del layer con margine e trasformazione CRS."""
        if layer.featureCount() == 0:
            return
        extent = layer.extent()
        if extent.isEmpty():
            return
        canvas = self.iface.mapCanvas()
        canvas_crs = canvas.mapSettings().destinationCrs()
        layer_crs = layer.crs()
        if canvas_crs != layer_crs:
            transform = QgsCoordinateTransform(
                layer_crs, canvas_crs, QgsProject.instance())
            extent = transform.transformBoundingBox(extent)
        # Add 5% buffer for visual padding
        extent.scale(1.05)
        canvas.setExtent(extent)
        canvas.refresh()

    def _reset_download_ui(self):
        self.btn_download.setEnabled(True)
        self.btn_search.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.progress_bar.setVisible(False)
        self._task = None

    # ------------------------------------------------------------------
    # Layer Creation
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_float(val) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _geojson_to_geometry(geojson: dict) -> QgsGeometry:
        """Converte un GeoJSON dict in QgsGeometry (MultiPolygon)."""
        from osgeo import ogr
        ogr_geom = ogr.CreateGeometryFromJson(json.dumps(geojson))
        if ogr_geom:
            geom = QgsGeometry.fromWkt(ogr_geom.ExportToWkt())
            if geom and not geom.isNull():
                geom.convertToMultiType()
                return geom
        return QgsGeometry()

    def _flatten_parcel(self, data: dict) -> dict:
        """Appiattisce la struttura annidata dell'API v2 in un dict piatto.

        Risposta API v2 /parcels/{id}:
          fid, gml_id, label, cadastral_reference, area_m2,
          centroid: {lat, lng},
          geometry: {type, coordinates},
          municipality: {code, name, province, region},
          cadastral: {foglio, sezione_urbana, comune_code, postal_code},
          risk: {seismic_zone, pga, flood_level, landslide_level},
          subsidence: {velocity_mm_year, risk_class, risk_label, ...},
          land_cover: {code, class, subclass, description, source},
          valuation: [{zone, zone_description, property_type, ...}, ...],
          address, land_use, coastal_erosion, cultural_heritage, poi
        """
        flat = {}

        # -- Identifiers --
        flat["parcel_id"] = data.get("fid")
        flat["gml_id"] = data.get("gml_id")
        flat["label"] = data.get("label")
        flat["cadastral_reference"] = data.get("cadastral_reference")

        # -- Municipality --
        mun = data.get("municipality")
        if isinstance(mun, dict):
            flat["municipality"] = mun.get("name")
            flat["municipality_code"] = mun.get("code")
            flat["province"] = mun.get("province")
            flat["region"] = mun.get("region")
        else:
            flat["municipality"] = mun
            flat["municipality_code"] = None
            flat["province"] = None
            flat["region"] = None

        # -- Area & centroid --
        flat["area_m2"] = self._safe_float(data.get("area_m2"))
        centroid = data.get("centroid")
        if isinstance(centroid, dict):
            flat["centroid_lat"] = self._safe_float(centroid.get("lat"))
            flat["centroid_lng"] = self._safe_float(centroid.get("lng"))
        else:
            flat["centroid_lat"] = None
            flat["centroid_lng"] = None

        # -- Cadastral --
        cad = data.get("cadastral")
        if isinstance(cad, dict):
            flat["foglio"] = cad.get("foglio")
            flat["sezione_urbana"] = cad.get("sezione_urbana")
            flat["postal_code"] = cad.get("postal_code")
        else:
            flat["foglio"] = None
            flat["sezione_urbana"] = None
            flat["postal_code"] = None

        # -- Address --
        flat["address"] = data.get("address")

        # -- Risk --
        risk = data.get("risk")
        if isinstance(risk, dict):
            flat["seismic_zone"] = risk.get("seismic_zone")
            flat["pga"] = self._safe_float(risk.get("pga"))
            flat["flood_level"] = risk.get("flood_level")
            flat["landslide_level"] = risk.get("landslide_level")
        else:
            flat["seismic_zone"] = None
            flat["pga"] = None
            flat["flood_level"] = None
            flat["landslide_level"] = None

        # -- Subsidence --
        sub = data.get("subsidence")
        if isinstance(sub, dict):
            flat["subsidence_velocity"] = self._safe_float(
                sub.get("velocity_mm_year"))
            flat["subsidence_risk_class"] = sub.get("risk_class")
            flat["subsidence_risk_label"] = sub.get("risk_label")
            flat["subsidence_direction"] = sub.get("direction")
        else:
            flat["subsidence_velocity"] = None
            flat["subsidence_risk_class"] = None
            flat["subsidence_risk_label"] = None
            flat["subsidence_direction"] = None

        # -- Land cover --
        lc = data.get("land_cover")
        if isinstance(lc, dict):
            flat["land_cover_code"] = lc.get("code")
            flat["land_cover_class"] = lc.get("class")
            flat["land_cover_subclass"] = lc.get("subclass")
            flat["land_cover_desc"] = lc.get("description")
        else:
            flat["land_cover_code"] = None
            flat["land_cover_class"] = None
            flat["land_cover_subclass"] = None
            flat["land_cover_desc"] = None

        # -- Valuation (first entry, typically residential) --
        val_list = data.get("valuation")
        if isinstance(val_list, list) and val_list:
            v = val_list[0]
            flat["val_zone"] = v.get("zone")
            flat["val_zone_desc"] = v.get("zone_description")
            flat["val_property_type"] = v.get("property_type")
            purchase = v.get("purchase")
            if isinstance(purchase, dict):
                flat["val_purchase_min"] = self._safe_float(
                    purchase.get("min_eur_m2"))
                flat["val_purchase_max"] = self._safe_float(
                    purchase.get("max_eur_m2"))
            else:
                flat["val_purchase_min"] = None
                flat["val_purchase_max"] = None
            rental = v.get("rental")
            if isinstance(rental, dict):
                flat["val_rental_min"] = self._safe_float(
                    rental.get("min_eur_m2"))
                flat["val_rental_max"] = self._safe_float(
                    rental.get("max_eur_m2"))
            else:
                flat["val_rental_min"] = None
                flat["val_rental_max"] = None
        else:
            flat["val_zone"] = None
            flat["val_zone_desc"] = None
            flat["val_property_type"] = None
            flat["val_purchase_min"] = None
            flat["val_purchase_max"] = None
            flat["val_rental_min"] = None
            flat["val_rental_max"] = None

        return flat

    def _extract_geometry(self, data: dict) -> QgsGeometry:
        """Estrae la geometria dalla risposta API v2.

        API v2: geometry è al livello top del dict.
        """
        geom_data = data.get("geometry")
        if geom_data and isinstance(geom_data, dict):
            return self._geojson_to_geometry(geom_data)
        return QgsGeometry()

    # Field definitions: (attr_name, QVariant_type, alias)
    PARCEL_FIELDS = [
        # Identifiers
        ("parcel_id",           QVariant.LongLong, "FID"),
        ("gml_id",              QVariant.String,   "GML ID"),
        ("label",               QVariant.String,   "Etichetta"),
        ("cadastral_reference", QVariant.String,   "Rif. Catastale"),
        # Municipality
        ("municipality",        QVariant.String,   "Comune"),
        ("municipality_code",   QVariant.String,   "Cod. Comune"),
        ("province",            QVariant.String,   "Provincia"),
        ("region",              QVariant.String,   "Regione"),
        # Area
        ("area_m2",             QVariant.Double,   "Area (m\u00b2)"),
        ("centroid_lat",        QVariant.Double,   "Centroide Lat"),
        ("centroid_lng",        QVariant.Double,   "Centroide Lng"),
        # Cadastral
        ("foglio",              QVariant.String,   "Foglio"),
        ("sezione_urbana",      QVariant.String,   "Sezione Urbana"),
        ("postal_code",         QVariant.String,   "CAP"),
        ("address",             QVariant.String,   "Indirizzo"),
        # Risk
        ("seismic_zone",        QVariant.Int,      "Zona Sismica"),
        ("pga",                 QVariant.Double,   "PGA"),
        ("flood_level",         QVariant.String,   "Livello Alluvione"),
        ("landslide_level",     QVariant.String,   "Livello Frana"),
        # Subsidence
        ("subsidence_velocity", QVariant.Double,   "Subsidenza (mm/a)"),
        ("subsidence_risk_class", QVariant.Int,    "Classe Rischio Sub."),
        ("subsidence_risk_label", QVariant.String, "Rischio Subsidenza"),
        ("subsidence_direction", QVariant.String,  "Direzione Sub."),
        # Land cover
        ("land_cover_code",     QVariant.String,   "Cod. Uso Suolo"),
        ("land_cover_class",    QVariant.String,   "Classe Uso Suolo"),
        ("land_cover_subclass", QVariant.String,   "Sottoclasse Uso Suolo"),
        ("land_cover_desc",     QVariant.String,   "Descr. Uso Suolo"),
        # Valuation (first entry)
        ("val_zone",            QVariant.String,   "Zona OMI"),
        ("val_zone_desc",       QVariant.String,   "Descr. Zona OMI"),
        ("val_property_type",   QVariant.String,   "Tipo Immobile"),
        ("val_purchase_min",    QVariant.Double,   "Acquisto Min (\u20ac/m\u00b2)"),
        ("val_purchase_max",    QVariant.Double,   "Acquisto Max (\u20ac/m\u00b2)"),
        ("val_rental_min",      QVariant.Double,   "Affitto Min (\u20ac/m\u00b2)"),
        ("val_rental_max",      QVariant.Double,   "Affitto Max (\u20ac/m\u00b2)"),
    ]

    def _create_layer(self, results: list) -> Optional[QgsVectorLayer]:
        """Crea un QgsVectorLayer dalle particelle arricchite."""
        layer_name = (self.layer_name_input.text().strip()
                      or "Zornade Particelle")

        # Create memory layer
        layer = QgsVectorLayer(
            "MultiPolygon?crs=EPSG:4326",
            layer_name,
            "memory",
        )
        if not layer.isValid():
            return None

        # Add fields
        dp = layer.dataProvider()
        fields = QgsFields()
        for name, var_type, alias in self.PARCEL_FIELDS:
            fields.append(QgsField(name, var_type))
        dp.addAttributes(fields)
        layer.updateFields()

        # Set field aliases
        for i, (name, _, alias) in enumerate(self.PARCEL_FIELDS):
            layer.setFieldAlias(i, alias)

        # Add features
        features = []
        for parcel_data in results:
            flat = self._flatten_parcel(parcel_data)
            geom = self._extract_geometry(parcel_data)

            feat = QgsFeature(layer.fields())
            if not geom.isEmpty():
                feat.setGeometry(geom)

            for name, var_type, _ in self.PARCEL_FIELDS:
                val = flat.get(name)
                if val is not None:
                    try:
                        if var_type == QVariant.LongLong:
                            val = int(val)
                        elif var_type == QVariant.Int:
                            val = int(val)
                        elif var_type == QVariant.Double:
                            val = float(val)
                        elif var_type == QVariant.String:
                            val = str(val)
                    except (ValueError, TypeError):
                        val = None
                    if val is not None:
                        feat.setAttribute(name, val)

            features.append(feat)

        ok, added = dp.addFeatures(features)
        if not ok:
            err = dp.lastError()
            QgsMessageLog.logMessage(
                f"addFeatures batch failed for {len(features)} features: {err}",
                "Zornade", Qgis.MessageLevel.Warning)
            # Fallback: add one-by-one to salvage what we can
            for i, feat in enumerate(features):
                ok2, _ = dp.addFeatures([feat])
                if not ok2 and i < 3:
                    attrs = {f.name(): feat[f.name()] for f in layer.fields()
                             if feat[f.name()] is not None
                             and str(feat[f.name()]) != "NULL"}
                    QgsMessageLog.logMessage(
                        f"Feature {i} rejected — geom wkbType={feat.geometry().wkbType()}, "
                        f"attrs={attrs}, err={dp.lastError()}",
                        "Zornade", Qgis.MessageLevel.Warning)
        layer.updateExtents()

        return layer

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _clear_results(self):
        """Pulisce la tabella risultati e lo stato."""
        self._search_results = []
        self.results_table.setRowCount(0)
        self.results_count.setText("Nessun risultato")
        self.btn_download.setEnabled(False)
        self.status_label.setText("")
        self.progress_bar.setVisible(False)

    def closeEvent(self, event):
        if self._task:
            self._task.cancel()
        self._clear_results()
        # Restore map tool if needed
        if self._prev_map_tool:
            self.iface.mapCanvas().setMapTool(self._prev_map_tool)
        super().closeEvent(event)
