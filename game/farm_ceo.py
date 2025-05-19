import pygame as pg
import logging

from time import time

from resource_manager import ResourceManager
from save_manager import SaveManager

from paddock_manager import PaddockManager
from sellpoint_manager import SellpointManager
from events import Events

from UI.panel import Panel
from UI.popups import PopupType

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

        dark = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        dark.fill((0, 0, 0, 128))

        self.dark_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        self.dark_surface.blit(self.surface, (0, 0))
        self.dark_surface.blit(dark, (0, 0), special_flags=pg.BLEND_RGBA_SUB)

        self.active_surface = self.surface
        self.paddocks_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.dark_overlay_enabled = True
        self.disable_dark_overlay()

    def _fit_image(self) -> None:
        self.scale = (self.SCREEN_WIDTH - PANEL_WIDTH) / self.rect.w
        self.surface = pg.transform.scale(self.original_surface, (self.rect.w * self.scale, self.rect.h * self.scale))
        self.rect = self.surface.get_rect()

    def enable_dark_overlay(self) -> None:
        self.active_surface = self.dark_surface
        self.dark_overlay_enabled = True

    def disable_dark_overlay(self) -> None:
        self.active_surface = self.surface
        self.dark_overlay_enabled = False

    def render(self) -> None:
        if self.dark_overlay_enabled:
            self.screen.fill((0, 0, 0), (self.x, self.y, self.rect.w, self.rect.h))

        self.screen.blit(self.active_surface, (self.x, self.y))
        self.screen.blit(self.paddocks_surface, (self.x, self.y))

class FarmCEO:
    RESOURCE_MANAGER: ResourceManager = ResourceManager()

    def __init__(self, screen: pg.Surface, clock: pg.time.Clock, events: Events) -> None:
        self.screen: pg.Surface = screen
        self.screen.fill(UI_BACKGROUND_COLOR)

        self.WIDTH: int = self.screen.get_width()
        self.HEIGHT: int = self.screen.get_height()

        self.clock = clock
        self.events = events

        self.map = Map(self.screen, self.RESOURCE_MANAGER.load_map("Green_Spring_cfg.json")) # map estimated to be almost screen size
        self.game_surface = pg.Surface((self.map.rect.w, self.map.rect.h), pg.SRCALPHA)
        
        self.shed = Shed(self.game_surface, utils.scale_rect(pg.Rect(self.map.map_cfg["shed"]["rect"]), self.map.scale), self.map.map_cfg["shed"]["rotation"], self.map.map_cfg["roads"], self.map.scale, None) # Silo will be set later (not None)

        self.save_manager: SaveManager = SaveManager()
        self.save_manager.init(self.map.map_cfg, self.shed.vehicles, self.shed.tools, self.shed.add_vehicle, self.shed.add_tool)

        self.paddock_manager: PaddockManager = PaddockManager()
        self.paddock_manager.init(self.screen, self.map.surface, self.map.paddocks_surface, self.save_manager.get_paddocks(), self.map.scale)

        self.sellpoint_manager = SellpointManager(self.game_surface, self.map.scale, self.save_manager.get_sellpoints())
        self.shed.set_silo(self.sellpoint_manager.silo)

        self.time: float = self.save_manager.get_attr("time") # time / 24 = *n* days
        self.last_update_time = 0.0

        equipment_map_funcs = {
            "map_lighten": self.map.disable_dark_overlay,
            "map_darken": self.map.enable_dark_overlay,
            "set_location_click_callback": self.paddock_manager.set_location_click_callback,
            "destroy_location_click_callback": self.paddock_manager.destroy_location_click_callback,
            "fill_all_paddocks": self.paddock_manager.fill_all_paddocks,
            "get_paddocks": self.paddock_manager.get_paddocks
        }

        self.panel = Panel(self.screen, events, self.set_popup, self.shed, self.sellpoint_manager, equipment_map_funcs)

        self.paddock_manager.fill_all_paddocks()

        self.popup = None
        
        # TODO: THIS IS JUST AN EXAMPLE
        #self.background_render()
        #for i in range(9): self.shed.task_manager.test_make_job(self.paddock_manager.paddocks[i])

        #for pdk in range(9):
        #    for i, point in enumerate(self.shed.task_manager.test_make_job(self.paddock_manager.paddocks[pdk])):
        #        c = pg.draw.circle(self.screen, (i%255, i**2%255, 0), (point[0] + PANEL_WIDTH, point[1]), 3)
        #        pg.display.update(c)
        #        pg.time.wait(5)

        #input()

    def enable_cheats(self) -> None:
        logging.warning("Cheats enabled! Money and XP set to 1,000,000,000,000")
        self.save_manager.set_money(1_000_000_000_000)
        self.save_manager.set_xp(1_000_000_000_000)

    def set_popup(self, popup: PopupType) -> None:
        if popup is None:
            return self.remove_popup()

        self.events.set_override(False)
        self.events.set_override_authority_requirement(True)

        self.popup = popup

    def remove_popup(self) -> None:
        self.events.set_override_authority_requirement(False)
        self.popup = None

    def background_render(self) -> None:
        self.map.render()
        self.paddock_manager.draw_paddock_numbers()

        self.game_surface.fill((0, 0, 0, 0))

    def simulate(self, dt: float) -> None:
        if time() - self.last_update_time >= 1:
            self.last_update_time = time()
            self.time += TIMESCALE

        self.paddock_manager.update(self.events.mouse_just_released)
        self.shed.simulate(dt)

    def foreground_render(self) -> None:
        self.sellpoint_manager.render_grids()

        # Vehicles and trailers
        ...

        # Buildings
        self.shed.render()
        self.sellpoint_manager.render_silos()

        self.screen.blit(self.game_surface, (PANEL_WIDTH, 0))

    def ui_render(self) -> None:
        self.panel.draw()


        # WARNING: THIS HAS TO BE LAST
        if self.popup is not None:
            self.popup.update()

            if self.popup is not None:
                self.screen.blit(self.popup.surface, (self.popup.x, self.popup.y))