"""
Zornade Sketching — Simbologia QGIS per particelle catastali.

Applica simbologia con colori Zornade, renderer categorizzati/graduati,
e labeling scale-dependent.

Classificazione basata su CORINE Land Cover (classi italiane livello 1/2).
"""

from qgis.PyQt.QtGui import QColor, QFont
from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer,
    QgsRendererCategory,
    QgsRendererRange,
    QgsFillSymbol,
    QgsVectorLayerSimpleLabeling,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayer,
)

# ======================================================================
# Zornade Design Tokens
# ======================================================================

ZORNADE_TEAL = "#14b8a6"
ZORNADE_TEAL_DARK = "#0d9488"
ZORNADE_TEAL_DEEPER = "#0f766e"
ZORNADE_SLATE_900 = "#0f172a"

# ======================================================================
# CORINE Land Cover — Classi italiane livello 1
# Valori reali restituiti da land_cover.class nell'API v2
# ======================================================================

LAND_COVER_COLORS = {
    "Superfici artificiali":                    "#374151",  # Slate gray
    "Superfici agricole":                       "#059669",  # Emerald
    "Territori boscati e ambienti semi-naturali": "#166534",  # Green-900
    "Zone umide":                               "#0891B2",  # Cyan
    "Corpi idrici":                             "#0284C7",  # Sky-600
}

# Colori per zona sismica (1 = massimo rischio, 4 = minimo)
SEISMIC_ZONE_COLORS = [
    (1, "#DC2626", "Zona 1 — Pericolosità alta"),
    (2, "#F59E0B", "Zona 2 — Pericolosità media"),
    (3, "#84CC16", "Zona 3 — Pericolosità bassa"),
    (4, "#22C55E", "Zona 4 — Pericolosità molto bassa"),
]

# Colori per classe rischio subsidenza (1-5)
SUBSIDENCE_RISK_COLORS = [
    (1, "#22C55E", "1 — Trascurabile"),
    (2, "#84CC16", "2 — Basso"),
    (3, "#F59E0B", "3 — Medio"),
    (4, "#EF4444", "4 — Alto"),
    (5, "#991B1B", "5 — Molto alto"),
]


# ======================================================================
# Renderer Factories
# ======================================================================

def _make_fill_symbol(fill_color: str, stroke_color: str,
                      stroke_width: float = 0.4,
                      opacity: float = 0.65) -> QgsFillSymbol:
    """Crea un simbolo di riempimento."""
    symbol = QgsFillSymbol.createSimple({
        "color": fill_color,
        "outline_color": stroke_color,
        "outline_width": str(stroke_width),
        "outline_style": "solid",
    })
    symbol.setOpacity(opacity)
    return symbol


def _darken(hex_color: str, factor: float = 0.3) -> str:
    """Scurisce un colore hex."""
    c = QColor(hex_color)
    r = max(0, int(c.red() * (1 - factor)))
    g = max(0, int(c.green() * (1 - factor)))
    b = max(0, int(c.blue() * (1 - factor)))
    return QColor(r, g, b).name()


def create_land_cover_renderer() -> QgsCategorizedSymbolRenderer:
    """Renderer categorizzato per CORINE Land Cover (classe livello 1)."""
    categories = []
    for cls_name, color in LAND_COVER_COLORS.items():
        symbol = _make_fill_symbol(color, _darken(color), 0.4, 0.65)
        cat = QgsRendererCategory(cls_name, symbol, cls_name)
        categories.append(cat)

    # Default per valori NULL o non classificati
    default_symbol = _make_fill_symbol("#9CA3AF", "#6B7280", 0.3, 0.45)
    default_cat = QgsRendererCategory(
        "", default_symbol, "Non classificato")
    categories.append(default_cat)

    return QgsCategorizedSymbolRenderer("land_cover_class", categories)


def create_seismic_renderer() -> QgsCategorizedSymbolRenderer:
    """Renderer categorizzato per zona sismica (1-4)."""
    categories = []
    for zone, color, label in SEISMIC_ZONE_COLORS:
        symbol = _make_fill_symbol(color, _darken(color), 0.4, 0.60)
        cat = QgsRendererCategory(zone, symbol, label)
        categories.append(cat)

    default_symbol = _make_fill_symbol("#9CA3AF", "#6B7280", 0.3, 0.45)
    default_cat = QgsRendererCategory(
        "", default_symbol, "Zona non definita")
    categories.append(default_cat)

    return QgsCategorizedSymbolRenderer("seismic_zone", categories)


def create_subsidence_renderer() -> QgsCategorizedSymbolRenderer:
    """Renderer categorizzato per classe rischio subsidenza (1-5)."""
    categories = []
    for cls, color, label in SUBSIDENCE_RISK_COLORS:
        symbol = _make_fill_symbol(color, _darken(color), 0.4, 0.60)
        cat = QgsRendererCategory(cls, symbol, label)
        categories.append(cat)

    default_symbol = _make_fill_symbol("#9CA3AF", "#6B7280", 0.3, 0.45)
    default_cat = QgsRendererCategory(
        "", default_symbol, "Dato non disponibile")
    categories.append(default_cat)

    return QgsCategorizedSymbolRenderer(
        "subsidence_risk_class", categories)


# ======================================================================
# Label Configuration
# ======================================================================

def create_parcel_labeling() -> QgsVectorLayerSimpleLabeling:
    """Crea labeling scale-dependent per particelle catastali."""
    settings = QgsPalLayerSettings()
    settings.fieldName = (
        "CASE "
        "WHEN \"foglio\" IS NOT NULL "
        "THEN \"label\" || ' — F.' || \"foglio\" "
        "ELSE coalesce(\"label\", to_string(\"parcel_id\")) "
        "END"
    )
    settings.isExpression = True

    text_format = QgsTextFormat()
    font = QFont("Inter", 8)
    font.setWeight(QFont.Weight.DemiBold)
    text_format.setFont(font)
    text_format.setSize(8)
    text_format.setColor(QColor(ZORNADE_SLATE_900))

    buffer_settings = QgsTextBufferSettings()
    buffer_settings.setEnabled(True)
    buffer_settings.setSize(1.2)
    buffer_settings.setColor(QColor(255, 255, 255, 210))
    text_format.setBuffer(buffer_settings)

    settings.setFormat(text_format)

    settings.placement = QgsPalLayerSettings.Placement.OverPoint
    settings.centroidWhole = True
    settings.priority = 5

    settings.scaleVisibility = True
    settings.minimumScale = 25000
    settings.maximumScale = 500

    return QgsVectorLayerSimpleLabeling(settings)


# ======================================================================
# Main Styling Function
# ======================================================================

STYLE_CLASSIFICATION = "land_cover"
STYLE_SEISMIC = "seismic_zone"
STYLE_SUBSIDENCE = "subsidence"

STYLE_OPTIONS = {
    STYLE_CLASSIFICATION:  "Uso Suolo (CORINE)",
    STYLE_SEISMIC:         "Zona Sismica",
    STYLE_SUBSIDENCE:      "Rischio Subsidenza",
}


def apply_sketching(layer: QgsVectorLayer,
                     style: str = STYLE_CLASSIFICATION) -> None:
    """Applica simbologia Zornade completa al layer."""
    if style == STYLE_SEISMIC:
        renderer = create_seismic_renderer()
    elif style == STYLE_SUBSIDENCE:
        renderer = create_subsidence_renderer()
    else:
        renderer = create_land_cover_renderer()

    layer.setRenderer(renderer)
    layer.setLabeling(create_parcel_labeling())
    layer.setLabelsEnabled(True)
    layer.triggerRepaint()
