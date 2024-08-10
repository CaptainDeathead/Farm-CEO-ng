import pygame as pg
import logging

from resource_manager import ResourceManager
from events import Events

from UI.panel import Panel

from data import *

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)

class Map:
    def __init__(self, screen: pg.Surface, surface: pg.Surface) -> None:
        self.screen: pg.Surface = screen

        self.SCREEN_WIDTH: int = self.screen.get_width()
        self.SCREEN_HEIGHT: int = self.screen.get_height()

        self.surface: pg.Surface = surface
        self.rect = self.surface.get_rect()
        self._fit_image()

        self.x: int = PANEL_WIDTH
        self.y: int = 0

    def _fit_image(self) -> None:
        scale = (self.SCREEN_WIDTH - PANEL_WIDTH) / self.rect.w
        self.surface = pg.transform.scale(self.surface, (self.rect.w * scale, self.rect.h * scale))
        self.rect = self.surface.get_rect()

    def render(self) -> None:
        self.screen.blit(self.surface, (self.x, self.y))

class FarmCEO:
    RESOURCE_MANAGER: ResourceManager = ResourceManager()

    def __init__(self, screen: pg.Surface, clock: pg.time.Clock, events: Events) -> None:
        self.screen: pg.Surface = screen

        self.WIDTH: int = self.screen.get_width()
        self.HEIGHT: int = self.screen.get_height()

        self.clock: pg.time.Clock = clock
        self.events: Events = events

        self.map: Map = Map(self.screen, self.RESOURCE_MANAGER.load_image("map.png", (self.WIDTH, self.HEIGHT))) # map estimated to be almost screen size

        self.panel: Panel = Panel(self.screen, events)

    def background_render(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)
        self.map.render()

    def simulate(self) -> None:
        ...

    def foreground_render(self) -> None:
        ...

    def ui_render(self) -> None:
        self.panel.draw()