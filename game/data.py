

from typing import Tuple

# ---------- PANEL ----------
PANEL_WIDTH: int = 620

# ---------- GAME ----------
BACKGROUND_COLOR: Tuple[int, int, int] = (0, 200, 255)

# ---------- CONFIG ----------
BUILD: bool = False
SUPPORTED_PLATFORMS: Tuple[str] = ("android_x86_64", "android_v7a", "android_v8a", "Linux", "Windows")
PLATFORM: str = "android_v8a"