import pygame as pg

from events import Events
from sellpoint_manager import SellpointManager

from UI.pygame_gui import Table
from copy import deepcopy
from data import *

class Grain:
    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect, sellpoint_manager: SellpointManager) -> None:
        self.parent_surface = parent_surface
        self.events = events
        self.rect = rect

        self.sellpoint_manager = sellpoint_manager

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        self.active = False

        self.last_sellpoint_prices = []
        self.last_silo_contents = {}

        self.rebuild()

    def rebuild(self) -> None:
        self.rendered_surface.fill(UI_BACKGROUND_COLOR)

        self.last_sellpoint_prices = []
        self.last_silo_contents = {}

        row = [""]
        row.extend([crop_type.capitalize() for crop_type in CROP_TYPES])
        grid = [row]

        for i, sellpoint in enumerate(self.sellpoint_manager.sellpoints):
            if sellpoint.silo: continue

            row = [sellpoint.name]
            row.extend([f"${sellpoint.prices[crop_type]:.0f}/T" for crop_type in CROP_TYPES])
            grid.append(row)

            self.last_sellpoint_prices.append(deepcopy(sellpoint.prices))

        row = [self.sellpoint_manager.silo.name]
        row.extend([f"{self.sellpoint_manager.silo.contents.get(crop_type, 0):.1f}T" for crop_type in CROP_TYPES])
        grid.append(row)

        self.last_silo_contents = deepcopy(self.sellpoint_manager.silo.contents)

        Table(self.rendered_surface, 10, 0, self.rect.w - 20, self.rect.w - 20, len(CROP_TYPES) + 1, len(self.sellpoint_manager.sellpoints) + 1, UI_MAIN_COLOR, UI_ACTIVE_COLOR, 40, grid).draw()

        self.redraw_required = True

    def draw(self) -> None:
        self.parent_surface.blit(self.rendered_surface, (0, self.rect.y))

    def update(self) -> bool:
        for i, sellpoint in enumerate(self.sellpoint_manager.sellpoints):
            if sellpoint.silo: continue

            if self.last_sellpoint_prices[i] != sellpoint.prices:
                self.rebuild()
                return True

        if self.sellpoint_manager.silo.contents != self.last_silo_contents:
            self.rebuild()
            return True
        
        if self.redraw_required:
            self.redraw_required = False
            return True
        
        return False
