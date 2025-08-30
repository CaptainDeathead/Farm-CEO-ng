import pygame as pg
import logging

from time import time
from math import floor

from resource_manager import ResourceManager, FontManager
from save_manager import SaveManager

from paddock_manager import PaddockManager
from sellpoint_manager import SellpointManager
from events import Events

from UI.panel import Panel
from UI.popups import PopupType, OKPopup, OKCancelPopup

from utils import utils, VarsSingleton
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

        logging.info(f"Global scale set to: {self.scale}x!")

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

class HUD:
    save_manager = SaveManager()

    def __init__(self, game_surface: pg.Surface) -> None:
        self.game_surface = game_surface

        self.WIDTH = self.game_surface.width
        self.HEIGHT = self.game_surface.height

        self.money_icon = pg.transform.smoothscale(ResourceManager().load_image("Icons/currency.png"), (50, 50))
        self.rebuild_money()

        self.xp_icon = pg.transform.smoothscale(ResourceManager().load_image("Icons/xp.png"), (50, 50))
        self.rebuild_xp()

        self.last_money = self.save_manager.money
        self.last_xp = self.save_manager.xp

    def rebuild_money(self) -> None:
        self.money_text = ResourceManager().font_manager.get_sysfont(None, 70).render(f"{self.save_manager.money:,.2f}", True, (255, 255, 255))
        self.money_surface = pg.Surface((self.money_icon.width + self.money_text.width + 10, max(self.money_icon.height, self.money_text.height)), pg.SRCALPHA)

        self.money_surface.blit(self.money_icon, (0, 0))
        self.money_surface.blit(self.money_text, (self.money_icon.width + 5, 0))

    def rebuild_xp(self) -> None:
        self.xp_text = ResourceManager().font_manager.get_sysfont(None, 70).render(f"{floor(self.save_manager.xp):.0f}", True, (255, 255, 255))
        self.xp_surface = pg.Surface((self.xp_icon.width + self.xp_text.width + 10, max(self.xp_icon.height, self.xp_text.height)), pg.SRCALPHA)

        self.xp_surface.blit(self.xp_icon, (0, 0))
        self.xp_surface.blit(self.xp_text, (self.xp_icon.width + 5, 0))

    def draw(self) -> None:
        if self.save_manager.money != self.last_money:
            self.rebuild_money()
        if self.save_manager.xp != self.last_xp:
            self.rebuild_xp()

        self.game_surface.blit(self.money_surface, (self.WIDTH - self.money_surface.width - 30, 10))
        self.game_surface.blit(self.xp_surface, (self.WIDTH - self.money_surface.width - 30 - self.xp_surface.width - 30, 10))

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

        FontManager().init()

        self.paddock_manager: PaddockManager = PaddockManager()

        self.sellpoint_manager = SellpointManager(self.game_surface, self.map.scale)
        
        self.shed = Shed(
            self.game_surface, self.events, utils.scale_rect(pg.Rect(self.map.map_cfg["shed"]["rect"]), self.map.scale), self.map.map_cfg["shed"]["rotation"], self.map.map_cfg["roads"],
            self.map.scale, None, self.request_sleep, self.paddock_manager, self.sellpoint_manager) # Silo will be set later (not None)

        self.save_manager: SaveManager = SaveManager()
        self.save_manager.init(self.map.map_cfg, self.shed.vehicles, self.shed.tools, self.shed.add_vehicle, self.shed.add_tool, [], self.shed.rect.center) # WARNING: Patch paddocks immediately
                                                                                                                                               #
        self.paddock_manager.init(self.screen, self.map.surface, self.map.paddocks_surface, self.save_manager.get_paddocks(), self.map.scale)  #
        self.save_manager.paddocks = self.paddock_manager.paddocks                                                                             # HERE

        self.sellpoint_manager.init(self.save_manager.get_sellpoints())
        self.shed.set_silo(self.sellpoint_manager.silo)
        self.shed.check_trailer_fills(self.save_manager.add_money)
        self.shed.clean_silo(self.save_manager.add_money)

        self.shed.fully_load_destinations()
        self.shed.fully_load_jobs()

        self.hud = HUD(self.game_surface)

        self.time: float = self.save_manager.get_attr("time") # time / 24 = *n* days
        self.last_update_time = 0.0

        self.vars_singleton = VarsSingleton()
        self.vars_singleton.init(shed=self.shed)

        equipment_map_funcs = {
            "map_lighten": self.map.disable_dark_overlay,
            "map_darken": self.map.enable_dark_overlay,
            "set_location_click_callback": self.set_location_click_callback,
            "destroy_location_click_callback": self.destroy_location_click_callback,
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

    def set_location_click_callback(self, callback: object) -> None:
        self.paddock_manager.set_location_click_callback(callback)
        self.sellpoint_manager.set_location_click_callback(callback)

        logging.debug("Location click callbacks set for paddock and sellpoint managers.")

    def destroy_location_click_callback(self) -> None:
        self.paddock_manager.destroy_location_click_callback()
        self.sellpoint_manager.destroy_location_click_callback()

        logging.debug("Location click callbacks destroyed for paddock and sellpoint managers.")
    
    def sleep(self) -> None:
        logging.info("Sleeping...")

        self.panel.contracts.check_paddocks_fulfillment(fail_if_not_done=True)

        for paddock in self.paddock_manager.get_paddocks():
            if paddock.state in GROWTH_STAGES:
                paddock.set_state(paddock.state + 1, True, skip_contract_check=True)
            elif paddock.owned_by == "npc":
                paddock.set_state((paddock.state + 1) % 6, True, skip_contract_check=True)
            else:
                paddock.set_state(paddock.state, True, skip_contract_check=True)

        self.panel.contracts.generate_contracts()
        self.sellpoint_manager.generate_all_sellpoint_prices()

    def request_sleep(self) -> None:
        logging.info("Sleep requested.")

        for vehicle in self.shed.vehicles:
            if vehicle.active:
                self.set_popup(OKPopup(self.events, self.remove_popup, "Cannot Sleep Now!", "You cannot sleep until all machinery is in the shed."))
                return
        
        for tool in self.shed.tools:
            if tool.active:
                self.set_popup(OKPopup(self.events, self.remove_popup, "Cannot Sleep Now!", "You cannot sleep until all machinery is in the shed."))
                return

        self.set_popup(OKCancelPopup(self.events, self.remove_popup, self.sleep, "Sleep Request", "Are you sure you want to sleep?\nAll crops will advance to the next growth stage."))

    def background_render(self) -> None:
        self.map.render()
        self.paddock_manager.draw_paddock_numbers()

        self.game_surface.fill((0, 0, 0, 0))

    def simulate(self, dt: float) -> None:
        if time() - self.last_update_time >= 1:
            self.last_update_time = time()
            self.time += TIMESCALE

        self.paddock_manager.update(self.events.mouse_just_released)
        self.sellpoint_manager.update(self.events.mouse_just_released)
        self.shed.simulate(dt)

    def foreground_render(self) -> None:
        self.sellpoint_manager.render_grids()

        # Vehicles and trailers
        ...

        # Buildings
        self.shed.render()
        self.sellpoint_manager.render_silos()

        self.hud.draw()
        self.screen.blit(self.game_surface, (PANEL_WIDTH, 0))

    def ui_render(self) -> None:
        self.panel.draw()

        # WARNING: THIS HAS TO BE LAST
        if self.popup is not None:
            self.popup.update()

            if self.popup is not None:
                self.screen.blit(self.popup.surface, (self.popup.x, self.popup.y))