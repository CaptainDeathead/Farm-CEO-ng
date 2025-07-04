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

MACHINARY_SCALE = 0.75
VEHICLE_SCALE: float = 0.75*MACHINARY_SCALE # Base value 0.75
TOOL_SCALE: float = 1.25*MACHINARY_SCALE # Base value 1.25

STATE_NAMES = {
    0: "Harvested",
    1: "Tilled",
    2: "Growing 1",
    3: "Growing 2",
    4: "Growing 3",
    5: "Ready to harvest",
    6: "Blank"
}

STATE_COLORS = {
    0: (200, 0, 200), # 0: Harvested.   1: Cultivated.   2: Growing 1.   3: Growing 2.   4: Growing 3.   5: Ready To Harvest.   6: Blank.
    1: (150, 150, 150),
    2: (0, 255, 0),
    3: (0, 200, 0),
    4: (0, 100, 0),
    5: (200, 200, 0),
    6: (0, 0, 0)
}

GROWTH_STAGES = [2, 3, 4]

TOOL_STATES = {
    "Cultivators": (1,),
    "Seeders": (2,),
    "Spreaders": (0, 1, 2, 3, 4),
    "Sprayers": (0, 2, 3, 4),
    "Trailers": (0, 1, 2, 3, 4, 5, 6),
    "Headers": (6,)
}

FIELD_TOOLS = ["Cultivators", "Seeders", "Spreaders", "Sprayers"]

TOOL_ACTIVE_NAMES = {
    "Cultivators": "cultivating",
    "Seeders": "seeding",
    "Spreaders": "spreading",
    "Sprayers": "spraying",
    "Headers": "harvesting",
    "Trailers": "delivering",
}

CROP_TYPES = ["wheat", "barley", "oat", "canola"]

CROP_IDS = {
    "wheat": 0,
    "barley": 1,
    "oat": 2,
    "canola": 3
}

LIME_STAGES = (0, 1, 2)
FERTILISER_STAGES = (2, 3, 4)
FERTILISERS = ("lime", "super", "urea")
FERTILISER_PRICES = {
    "lime": 30,
    "super": 300,
    "urea": 700
}

CHEMICAL_STAGES = (3, 4)
CHEMICALS = ("liquid-super", "liquid-urea", "herbicide")
CHEMICAL_PRICES = {
    "liquid-super": 400,
    "liquid-urea": 800,
    "herbicide": 300
}

FILL_TYPES = []
FILL_TYPES.extend(CROP_TYPES)
FILL_TYPES.extend(FERTILISERS)
FILL_TYPES.extend(CHEMICALS)

BASE_CROP_PRICES = {
    0: 300,
    1: 400,
    2: 800,
    3: 600
}

TIMESCALE = 24 # 144 mins every min = 2.4 min every second
MINS_IN_DAY = TIMESCALE * 60

JOB_TYPES = {
    "transporting_to": 0,
    "transporting_from": 1,
    "travelling_to": 2,
    "working": 3,
    "travelling_from": 4
}

END_JOB_STAGES = [JOB_TYPES["transporting_from"], JOB_TYPES["travelling_from"]]

MAX_TURN_SPEED: int = 8
PAINT_RECT_HEIGHT: int = 4
PAINT_RECT_DIST: int = 2

EQUIPMENT_RATES = {
    # Less is more
    "Seeders": 100_000,
    "Spreaders": 100_000,
    "Sprayers": 100_000,
    "Headers": 50_000
}

FILL_TOOLS = {
    "Seeders": True,
    "Spreaders": True,
    "Sprayers": True,
    "Headers": True,
    "Trailers": False, # dont want its fill changing while its in a paddock
    "Cultivators": False
}

PAINT_TOOLS = ["Seeders", "Spreaders", "Sprayers", "Headers", "Cultivators"]

EXCLUDE_SELLPOINT_TOOLS = {
    "Seeders": True,
    "Spreaders": True,
    "Sprayers": True,
    "Headers": True,
    "Cultivators": False
}

# ---------- CONFIG ----------
BUILD: bool = False
TARGET_FPS: int = 1200
SUPPORTED_PLATFORMS: Tuple[str] = ("android_x86_64", "android_v7a", "arm64-v8a", "Linux", "Windows")
PLATFORM: str = "arm64-v8a"
BUILD_TYPE: str = "Devlopment"
CONSOLE_BUILD: bool = not BUILD
UNLOCK_ALL_PADDOCKS: bool = False

# ---------- DEBUG ----------
DEBUG_BOUNDARY_LOADING: bool = False
DEBUG_PATH_GENERATION: bool = False
DEBUG_PATH_MASK_COLLISION: bool = False
DEBUG_PATHS: bool = False
DEBUG_ROADS: bool = False
DEBUG_PAINT: bool = False
DEBUG_MOUSE_EVENTS: bool = False

# ---------- ABOUT ----------
GAME_NAME: str = "Farm CEO"
GAME_VERSION: str = "0.1.0"
TRADEMARK_MESSAGE: str = "This game is not affiliated with or endorsed by ANY of the brands used!!!\nAll trademarks and logos are the property of their respective owners.\nMachinary specifications are not a direct reflection of the real thing, as they are heavily tweaked by us to work with the game."
CONTRIBUTORS: Tuple[str] = ("Slotho101", "TobyHall633", "Mum & Gaz", "Dad", "Sean & Andrea", "Yesn't", "Rascam", "Ryan Mansell")