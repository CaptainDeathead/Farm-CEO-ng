import pygame as pg
import logging

from time import time

from resource_manager import ResourceManager, SaveManager
from paddock_manager import PaddockManager
from events import Events

from UI.panel import Panel

from utils import utils
from farm import Shed
from data import *
from typing import Dict, List, Iterable

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

class FarmCEO:
    RESOURCE_MANAGER: ResourceManager = ResourceManager()

    def __init__(self, screen: pg.Surface, clock: pg.time.Clock, events: Events) -> None:
        self.screen: pg.Surface = screen

        self.WIDTH: int = self.screen.get_width()
        self.HEIGHT: int = self.screen.get_height()

        self.clock = clock
        self.events = events

        self.map = Map(self.screen, self.RESOURCE_MANAGER.load_map("Green_Spring_cfg.json")) # map estimated to be almost screen size

        self.save_manager = SaveManager()
        self.save_manager.init(self.map.map_cfg)

        self.paddock_manager = PaddockManager()
        self.paddock_manager.init(self.screen, self.map.surface, self.save_manager.get_paddocks(), self.map.scale)

        self.time: float = self.save_manager.get_attr("time") # time / 24 = *n* days
        self.last_update_time = 0.0

        self.shed = Shed(self.screen, utils.scale_rect(pg.Rect(self.map.map_cfg["shed"]["rect"]), self.map.scale), self.map.map_cfg["shed"]["rotation"])

        self.panel = Panel(self.screen, events, self.shed)

    def background_render(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)
        self.map.render()

        self.paddock_manager.draw_paddock_numbers()

    def simulate(self) -> None:
        if time() - self.last_update_time >= 1:
            self.last_update_time = time()
            self.time += TIMESCALE

    def foreground_render(self) -> None:
        # Vehicles and trailers
        ...

        # Buildings
        self.shed.render()

    def ui_render(self) -> None:
        self.panel.draw()