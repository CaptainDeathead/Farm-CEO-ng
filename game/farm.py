import pygame as pg

from resource_manager import ResourceManager
from save_manager import SaveManager

from machinary import Tractor, Header, Tool
from utils import utils
from data import *

from copy import deepcopy
from typing import List, Dict

class LayableRenderObj:
    def render0(self) -> None: ...
    def render1(self) -> None: ...
    def render2(self) -> None: ...

    def render(self) -> None:
        self.render0(); self.render1(); self.render2()

class Shed(LayableRenderObj):
    def __init__(self, game_surface: pg.Surface, rect: pg.Rect, rotation: float) -> None:        
        self.game_surface = game_surface

        self.rect = rect

        self.rotation = rotation
        self.color = pg.Color(175, 195, 255)
        self.pad_color = pg.Color(213, 207, 207)
        self.surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.vehicles: List[Tractor | Header] = []
        self.tools: List[Tool] = []

        # shading for roof
        large_shadow_map = ResourceManager.load_image("Lighting/shed_shadow_map.png", (1000, 1000)) # Already converted
        self.shadow_map = pg.transform.scale(large_shadow_map, (rect.w, rect.h*2/3))
        self.shadow_map.set_alpha(128)

        self.rebuild()

    def add_vehicle(self, save_attrs: Dict[str, any]) -> None:
        if save_attrs["header"]: vehicle_type = "Harvesters"
        else: vehicle_type = "Tractors"

        attrs = deepcopy(SaveManager().STATIC_VEHICLES_DICT[vehicle_type][save_attrs["brand"]][save_attrs["model"]])
        attrs.update(save_attrs)

        if attrs["header"]: vehicle = Header(self.game_surface, self.rect, attrs)
        else: vehicle = Tractor(self.game_surface, self.rect, attrs)

        self.vehicles.append(vehicle)

    def add_tool(self, save_attrs: Dict[str, any]) -> None:
        attrs = deepcopy(SaveManager().STATIC_TOOLS_DICT)
        attrs.update(save_attrs)

        ...

    def rebuild(self) -> None:
        self.surface.fill((0, 0, 0, 255))

        # Shed
        pg.draw.rect(self.surface, self.color, pg.Rect(0, 0, self.rect.w, self.rect.h*2/3))
        self.surface.blit(self.shadow_map, (0, 0))

        # Line in middle of shed
        pg.draw.line(self.surface, (150, 150, 200), (0, self.rect.h/3), (self.rect.w, self.rect.h/3), 2)

        # Concrete pad in front of shed
        pg.draw.rect(self.surface, self.pad_color, pg.Rect(0, self.rect.h*2/3, self.rect.w, self.rect.h/3))

    def render2(self) -> None:
        utils.blit_centered(self.game_surface, self.surface, (self.rect.x, self.rect.y), (self.rect.w/2, self.rect.h/2), self.rotation)