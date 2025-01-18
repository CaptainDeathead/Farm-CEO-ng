import pygame as pg

from typing import Tuple

# ---------- PANEL ----------
PANEL_WIDTH: int = 620
NAVBAR_HEIGHT: int = 110

# ---------- GAME ----------
BACKGROUND_COLOR: Tuple[int, int, int] = (0, 200, 255)

UI_BACKGROUND_COLOR: Tuple[int, int, int] = (52, 52, 52)
UI_MAIN_COLOR: Tuple[int, int, int] = (67, 163, 134)
UI_ACTIVE_COLOR: Tuple[int, int, int] = (67*2, 200, 160)
UI_TEXT_COLOR: Tuple[int, int, int] = (255, 255, 255)
UI_TOOL_BUTTON_COLOR: Tuple[int, int, int] = (150, 0, 255)

STATE_COLORS = {
    0: (200, 0, 200), # 0: Harvested.   1: Cultervated.   2: Growing 3.   3: Growing 2.   4: Growing 1.   5: Ready To Harvest.   6: Blank.
    1: (150, 150, 150),
    2: (0, 100, 0),
    3: (0, 200, 0),
    4: (0, 255, 0),
    5: (200, 200, 0),
    6: (0, 0, 0)
}

CROP_TYPES = ["wheat", "barley", "oat", "canola"]

CROP_IDS = {
    "wheat": 0,
    "barley": 1,
    "oat": 2,
    "canola": 3
}

BASE_CROP_PRICES = {
    0: 300,
    1: 400,
    2: 800,
    3: 600
}

TIMESCALE = 24 # 144 mins every min = 2.4 min every second
MINS_IN_DAY = TIMESCALE * 60

# ---------- CONFIG ----------
BUILD: bool = False
SUPPORTED_PLATFORMS: Tuple[str] = ("android_x86_64", "android_v7a", "arm64-v8a", "Linux", "Windows")
PLATFORM: str = "arm64-v8a"
BUILD_TYPE: str = "Devlopment"
CONSOLE_BUILD: bool = not BUILD

# ---------- DEBUG ----------
DEBUG_BOUNDARY_LOADING: bool = False

# ---------- ABOUT ----------
GAME_NAME: str = "Farm CEO"
GAME_VERSION: str = "0.1.0"
TRADEMARK_MESSAGE: str = "This game is not affiliated with or endorsed by ANY of the brands used!!!\nAll trademarks and logos are the property of their respective owners.\nMachinary specifications are not a direct reflection of the real thing, as they are heavily tweaked by us to work with the game."
CONTRIBUTORS: Tuple[str] = ("Slotho101", "TobyHall633", "Mum & Gaz", "Dad", "Sean & Andrea", "Yesn't", "Rascam")