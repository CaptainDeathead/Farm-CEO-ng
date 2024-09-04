import pygame as pg

from resource_manager import ResourceManager

from machinary import Vehicle, Tool

from utils import utils
from data import *

from typing import List

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

        self.vehicles: List[Vehicle] = []
        self.tools: List[Tool] = []

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