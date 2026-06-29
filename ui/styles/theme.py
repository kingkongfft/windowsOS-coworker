"""Color constants, font sizes, and spacing — Deep Blue 3D theme."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Blue palette — dark navy base, vibrant blue accents
# ---------------------------------------------------------------------------

# App-level backgrounds (layered for depth)
BG_APP = "#0B1120"  # deepest layer — window base
BG_SIDEBAR = "#0F1729"  # sidebar panel
BG_SIDEBAR_HOVER = "#1A2540"
BG_SIDEBAR_ACTIVE = "#1E3A6E"
BG_MAIN = "#111827"  # main chat background
BG_HEADER = "#0F1729"  # chat header bar
BG_INPUT_AREA = "#0F1729"  # input container
BG_INPUT = "#1A2540"  # input field normal
BG_INPUT_FOCUSED = "#1E2E50"

# Card / bubble surfaces
BG_USER_BUBBLE = "#1E3A8A"  # rich blue card
BG_ASSISTANT_BUBBLE = "#1A2540"  # slightly lighter card
BG_CODE_BLOCK = "#0B1120"  # deepest for code
BG_THINKING = "#1A2E5A"
BG_WELCOME_CHIP = "#1A2540"
BG_WELCOME_CHIP_HOVER = "#1E3A6E"

# Text
TEXT_PRIMARY = "#E8F0FE"  # near-white with blue tint
TEXT_SECONDARY = "#7FA3D4"  # muted blue-grey
TEXT_PLACEHOLDER = "#4A6A9A"
TEXT_CODE = "#93C5FD"  # light blue for code
TEXT_LINK = "#60A5FA"

# Accents
ACCENT = "#3B82F6"  # bright blue
ACCENT_HOVER = "#2563EB"
ACCENT_PRESSED = "#1D4ED8"
ACCENT_LIGHT = "#1E3A8A"
ACCENT_GLOW = "#60A5FA"  # lighter for glow effects

# Borders — layered for 3D depth
BORDER = "#1E3A6E"  # standard border
BORDER_BRIGHT = "#2563EB"  # accent border (focus, active)
BORDER_CARD = "#1E2E50"  # subtle card outline
BORDER_INPUT = "#2A4080"

# Divider
DIVIDER_RED = "#EF4444"

# Risk
RISK_MEDIUM = "#F59E0B"
RISK_MEDIUM_BG = "#1C1500"
RISK_HIGH = "#EF4444"
RISK_HIGH_BG = "#1C0000"
RISK_LOW = "#22C55E"

# Scrollbar
SCROLLBAR_BG = "transparent"
SCROLLBAR_HANDLE = "#1E3A6E"
SCROLLBAR_HANDLE_HOVER = "#3B82F6"

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

FONT_FAMILY = "Segoe UI, Microsoft YaHei UI, Arial, sans-serif"
FONT_FAMILY_CODE = "Cascadia Code, Consolas, Courier New, monospace"

FONT_SIZE_XS = 11
FONT_SIZE_SM = 12
FONT_SIZE_BASE = 13
FONT_SIZE_MD = 14
FONT_SIZE_LG = 16
FONT_SIZE_XL = 20
FONT_SIZE_TITLE = 24

# ---------------------------------------------------------------------------
# Spacing / sizing
# ---------------------------------------------------------------------------

SIDEBAR_WIDTH = 240
INPUT_HEIGHT_MIN = 52
INPUT_HEIGHT_MAX = 160
BUBBLE_MAX_WIDTH = 720
BUBBLE_RADIUS = 14
BUBBLE_PADDING_H = 16
BUBBLE_PADDING_V = 12
WINDOW_MIN_W = 900
WINDOW_MIN_H = 600
WINDOW_DEFAULT_W = 1200
WINDOW_DEFAULT_H = 760

# ---------------------------------------------------------------------------
# Avatar colours
# ---------------------------------------------------------------------------

AVATAR_USER_BG = ACCENT
AVATAR_USER_FG = "#FFFFFF"
AVATAR_BOT_BG = "#6D28D9"  # violet — contrasts nicely with blue
AVATAR_BOT_FG = "#FFFFFF"
