import pygame as pg
import logging

from time import time
from math import sin, cos

from resource_manager import ResourceManager, SaveManager
from events import Events

from UI.panel import Panel

from paddock import Paddock
from utils import utils

from typing import Dict, List, Iterable
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

class PaddockManager:
    def __init__(self, map_image: pg.Surface, paddocks: Dict[int, any], scale: float) -> None:
        self.map_image = map_image
        self.scale = scale

        self.paddocks = self.parse_paddocks(paddocks)
        self.init_paddocks()

    def parse_paddocks(self, paddocks: Dict[str, any]) -> List[Paddock]:
        pdk_list = []
        for paddock in paddocks:
            pdk_list.append(Paddock(paddocks[paddock], paddock, self.scale))
        
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

class LayableRenderObj:
    def render0(self) -> None: ...
    def render1(self) -> None: ...
    def render2(self) -> None: ...

    def render(self) -> None:
        self.render0(); self.render1(); self.render2()

class Shed(LayableRenderObj):
    def __init__(self, screen: pg.Surface, rect: pg.Rect, rotation: float) -> None:        
        self.screen = screen

        self.rect = rect
        self.rect.x += PANEL_WIDTH

        self.rotation = rotation
        self.color = pg.Color(175, 195, 255)
        self.pad_color = pg.Color(213, 207, 207)
        self.surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        # shading for roof
        large_shadow_map = ResourceManager.load_image("Lighting/shed_shadow_map.png", (1000, 1000)) # Already converted
        self.shadow_map = pg.transform.scale(large_shadow_map, (rect.w, rect.h*2/3))
        self.shadow_map.set_alpha(128)

        self.rebuild()

    def rebuild(self) -> None:
        self.surface.fill((0, 0, 0, 255))

        # Shed
        pg.draw.rect(self.surface, self.color, pg.Rect(0, 0, self.rect.w, self.rect.h*2/3))
        self.surface.blit(self.shadow_map, (0, 0))

        # Concrete pad in front of shed
        pg.draw.rect(self.surface, self.pad_color, pg.Rect(0, self.rect.h*2/3, self.rect.w, self.rect.h/3))

    def render2(self) -> None:
        utils.blit_centered(self.screen, self.surface, (self.rect.x, self.rect.y), (self.rect.w/2, self.rect.h/2), self.rotation)

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

        self.time: float = self.save_manager.get_attr("time") # time / 24 = *n* days

        self.shed = Shed(self.screen, pg.Rect(self.map.map_cfg["shed"]["rect"]), self.map.map_cfg["shed"]["rotation"])

        self.panel = Panel(self.screen, events)

    def background_render(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)
        self.map.render()

    def simulate(self) -> None:
        ...

    def foreground_render(self) -> None:
        # Vehicles and trailers
        ...

        # Buildings
        self.shed.render()

    def ui_render(self) -> None:
        self.panel.draw()