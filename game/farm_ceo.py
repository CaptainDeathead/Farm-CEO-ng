import pygame as pg
import logging

from random import randint

from resource_manager import ResourceManager
from events import Events

from UI.panel import Panel

from typing import Dict, List
from data import *

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)

class Map:
    def __init__(self, screen: pg.Surface, map_image_with_cfg: Tuple[pg.Surface, Dict[str, any]]) -> None:
        self.screen: pg.Surface = screen

        self.SCREEN_WIDTH: int = self.screen.get_width()
        self.SCREEN_HEIGHT: int = self.screen.get_height()

        self.original_surface: pg.Surface = map_image_with_cfg[0]
        self.surface: pg.Surface = self.original_surface

        self.map_cfg: Dict[str, any] = map_image_with_cfg[1]

        self.rect = self.surface.get_rect()
        
        self.scale = 1.0
        self._fit_image()

        self.x: int = PANEL_WIDTH
        self.y: int = 0

    def _fit_image(self) -> None:
        self.scale = (self.SCREEN_WIDTH - PANEL_WIDTH) / self.rect.w
        self.surface = pg.transform.scale(self.original_surface, (self.rect.w * self.scale, self.rect.h * self.scale))
        self.rect = self.surface.get_rect()

    def render(self) -> None:
        self.screen.blit(self.surface, (self.x, self.y))

class Paddock:
    def __init__(self, attrs: Dict[int, any], num: int, scale: float) -> None:
        self.attrs = attrs
        self.num = num
        self.scale = scale
        self.state: int = attrs.get("state", randint(0, 5))

        cx, cy = attrs["center"]
        gx, gy = attrs["gate"]

        self.center = (int(cx * scale), int(cy * scale))
        self.gate = (int(gx * scale), int(gy * scale))

        self.boundary: List[Tuple] = attrs.get("boundary", [])

    def __dict__(self) -> Dict[str, any]:
        return {
            "center": self.attrs["center"],
            "gate": self.attrs["gate"],
            "state": self.state
        }
    
    def set_boundary(self, boundary: List[Tuple]) -> None:
        self.boundary = boundary

class SaveManager:
    SAVE_PATH: str = "./farmceo_savegame.json"

    def __new__(cls, map_config: Dict[str, any], new_save: bool = False) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(SaveManager, cls).__new__(cls)
            cls.instance.init(map_config, new_save)

        return cls.instance
    
    def init(self, map_config: Dict[str, any], new_save: bool) -> None:
        if new_save: self.init_savefile(map_config)
        
        self.save = ResourceManager.load_json(self.SAVE_PATH)
        if self.save == {}: self.init_savefile(map_config)

    def _load_paddocks_from_conf(self, map_config: Dict[str, any]) -> Dict[int, any]:
        new_paddocks = {}
        for pdk in map_config["paddocks"]:
            new_paddocks[int(pdk)] = map_config["paddocks"][pdk]

        return new_paddocks

    def init_savefile(self, map_config: Dict[str, any]) -> None:
        self.new_savefile = True

        if map_config == {}:
            raise Exception("Map configuration is EMPTY! Please provide a valid map config in the arguments when creating a new save.")
        
        new_save = {
            "map_name": map_config["name"],
            "money": 500_000.0, # Starting money
            "debt": 0.0 # No dept to start with
        }

        new_save["paddocks"] = self._load_paddocks_from_conf(map_config)

        ResourceManager.write_json(new_save, self.SAVE_PATH)
        self.save = ResourceManager.load_json(self.SAVE_PATH)

    def save_game(self) -> None:
        ResourceManager.write_json(self.save, self.SAVE_PATH)

    def get_paddocks(self) -> Dict[int, any]:
        return self.save["paddocks"]
    
    def set_paddocks(self, paddocks: List[Paddock]) -> None:
        paddocks_dict = {}

        for paddock in paddocks:
            paddocks_dict[paddock.num] = paddock.__dict__()

        self.save["paddocks"] = paddocks_dict

class PaddockManager:
    def __init__(self, map_image: pg.Surface, paddocks: Dict[int, any], scale: float) -> None:
        self.map_image = map_image
        self.scale = scale

        self.paddocks = self.parse_paddocks(paddocks)
        self.init_paddocks()

    def parse_paddocks(self, paddocks: Dict[str, any]) -> List[Paddock]:
        pdk_list = []
        for paddock in paddocks:
            pdk_list.append(Paddock(paddocks[paddock], int(paddock)+1, self.scale))
        
        return pdk_list

    def locate_paddock_boundary(self, paddock: Paddock) -> None:
        def rgb_darker_than(rgb: Tuple[int, int, int], brightness: int) -> bool:
            if rgb[0] < brightness and rgb[1] < brightness and rgb[2] < brightness: return True
            return False
        
        darkness = 110
        
        def get_adj_edge(pos: Tuple[int, int]) -> Tuple[int, int]:
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if x == 0 and y == 0: continue

                    nx, ny = pos[0] + x, pos[1] + y
                    if not rgb_darker_than(self.map_image.get_at((nx, ny)), darkness): return (nx, ny)
            
            return (-1, -1)
        
        if DEBUG_BOUNDARY_LOADING: pg.display.update(pg.display.get_surface().blit(self.map_image, (0, 0)))

        boundary = []

        # Starting at center
        cx, cy = paddock.center

        start_x = cx
        start_y = 0

        # find boundary start from center
        y = cy
        while 1:
            if not rgb_darker_than(self.map_image.get_at((cx, y)), darkness):
                start_y = y
                break
            y += 1
        
        # trace boundary
        curr_x = start_x
        curr_y = start_y

        while 1:
            if DEBUG_BOUNDARY_LOADING: pg.display.update(pg.draw.circle(pg.display.get_surface(), (255, 255, 255), (curr_x, curr_y), 1))
            found_new_px = False

            # get adjacent paddock squares (black)
            for x in range(-1, 2):
                if found_new_px: continue
                
                for y in range(-1, 2):
                    if (x == 0 and y == 0) or found_new_px: continue
                    
                    nx, ny = curr_x + x, curr_y + y

                    if (nx, ny) == (start_x, start_y): # Back to start (Done)
                        if len(boundary) < 2: continue

                        paddock.set_boundary(boundary)
                        return
                    
                    if (nx, ny) in boundary: continue

                    if rgb_darker_than(self.map_image.get_at((nx, ny)), darkness):
                        edge = get_adj_edge((nx, ny))

                        if edge != (-1, -1):
                            found_new_px = True
                            boundary.append((nx, ny))
                            curr_x, curr_y = nx, ny
                        else:
                            if DEBUG_BOUNDARY_LOADING: pg.display.update(pg.draw.circle(pg.display.get_surface(), (255, 0, 0), (nx, ny), 1))

            if DEBUG_BOUNDARY_LOADING: pg.display.update(pg.draw.circle(pg.display.get_surface(), (255, 0, 0), (nx, ny), 1))

    def fill_paddock(self, paddock: Paddock, color: pg.Color) -> None:
        boundary = paddock.boundary
        pg.draw.polygon(self.map_image, color, boundary)

    def load_paddock_state(self, paddock: Paddock) -> None:
        self.fill_paddock(paddock, STATE_COLORS[paddock.state])

    def set_paddock_state(self, paddock_number: int, state: int) -> None:
        self.paddocks[paddock_number-1].state = state
        self.load_paddock_state(self.paddocks[paddock_number-1])

    def init_paddocks(self) -> None:
        for paddock in self.paddocks:
            self.locate_paddock_boundary(paddock)
            self.load_paddock_state(paddock)

        save_manager = SaveManager({})
        save_manager.set_paddocks(self.paddocks)
        save_manager.save_game()

class FarmCEO:
    RESOURCE_MANAGER: ResourceManager = ResourceManager()

    def __init__(self, screen: pg.Surface, clock: pg.time.Clock, events: Events) -> None:
        self.screen: pg.Surface = screen

        self.WIDTH: int = self.screen.get_width()
        self.HEIGHT: int = self.screen.get_height()

        self.clock = clock
        self.events = events

        self.map = Map(self.screen, self.RESOURCE_MANAGER.load_map("Green_Spring_cfg.json")) # map estimated to be almost screen size
        self.save_manager = SaveManager(self.map.map_cfg)
        self.paddock_manager = PaddockManager(self.map.surface, self.save_manager.get_paddocks(), self.map.scale)

        self.panel = Panel(self.screen, events)

    def background_render(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)
        self.map.render()

    def simulate(self) -> None:
        ...

    def foreground_render(self) -> None:
        ...

    def ui_render(self) -> None:
        self.panel.draw()