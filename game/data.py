import pygame as pg

from typing import Tuple

# ---------- PANEL ----------
PANEL_WIDTH: int = 620

# ---------- GAME ----------
BACKGROUND_COLOR: Tuple[int, int, int] = (0, 200, 255)

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
CONSOLE_BUILD: bool = False

# ---------- DEBUG ----------
DEBUG_BOUNDARY_LOADING: bool = False

# ---------- ABOUT ----------
GAME_NAME: str = "Farm CEO"
GAME_VERSION: str = "0.1.0"
CONTRIBUTORS: Tuple[str] = ("Slotho101", "TobyHall633", "Sean", "Yesn't", "Rascam")