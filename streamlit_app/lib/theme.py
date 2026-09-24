"""Design tokens — the same validated categorical palette and surface/ink
roles used by the (now retired) Next.js frontend, kept for visual
consistency and because the categorical order has already been run
through the accessibility validator (see dataviz skill: fixed hue order,
CVD-safe adjacent pairs)."""

ACCENT = "#2a78d6"
ACCENT_INK = "#ffffff"

SERIES = {
    1: "#2a78d6",  # blue
    2: "#eb6834",  # orange
    3: "#1baf7a",  # aqua
    4: "#eda100",  # yellow
    5: "#e87ba4",  # magenta
    6: "#008300",  # green
    7: "#4a3aa7",  # violet
    8: "#e34948",  # red
}

GOOD = "#0ca30c"
WARNING = "#fab219"
SERIOUS = "#ec835a"
CRITICAL = "#d03b3b"

BACKGROUND = "#f9f9f7"
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
BORDER = "rgba(11, 11, 11, 0.10)"
GRIDLINE = "#e1e0d9"
MUTED = TEXT_MUTED  # back-compat alias for existing chart code
