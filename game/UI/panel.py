import pygame as pg
import logging

from resource_manager import ResourceManager
from events import Events

from farm import Shed
from sellpoint_manager import SellpointManager

from UI.pygame_gui import Button
from UI.navbar import NavBar

from UI.Menus.shop import Shop
from UI.Menus.equipment import Equipment
from UI.Menus.contracts import Contracts
from UI.Menus.grain import Grain
from UI.Menus.guide import Guide

from data import *

class Panel:
    NAVBAR_HEIGHT = NAVBAR_HEIGHT

    def __init__(self, screen: pg.Surface, events: Events, set_popup: callable, shed: Shed, sellpoint_manager: SellpointManager, map_funcs: dict[str, object]) -> None:
        self.screen: pg.Surface = screen
        self.events: Events = events
        self.set_popup = set_popup

        self.SCREEN_WIDTH: int = self.screen.get_width()
        self.SCREEN_HEIGHT: int = self.screen.get_height()

        self.rect: pg.Rect = pg.Rect(0, 0, PANEL_WIDTH, self.SCREEN_HEIGHT)
        self.rendered_surface: pg.Surface = pg.Surface((PANEL_WIDTH, self.SCREEN_HEIGHT))

        self.nav_bar: NavBar = NavBar(self.rendered_surface, self.events, pg.Rect(0, 0, PANEL_WIDTH, self.NAVBAR_HEIGHT), self.force_draw_page)

        page_height = pg.Rect(0, self.NAVBAR_HEIGHT - 20, PANEL_WIDTH, self.SCREEN_HEIGHT - self.NAVBAR_HEIGHT - 20)

        self.shop = Shop(self.rendered_surface, self.events, page_height, map_funcs)
        self.equipment = Equipment(self.rendered_surface, self.events, self.set_popup, page_height, shed, sellpoint_manager, map_funcs)
        self.contracts = Contracts(self.rendered_surface, self.events, page_height, self.set_popup)
        self.grain = Grain(self.rendered_surface, self.events, page_height, sellpoint_manager)
        self.guide = Guide(self.rendered_surface, self.events, page_height, 1)

        self.rebuild()

    def rebuild(self) -> None:
        logging.info("Rebuilding panel...")

        self.rendered_surface.fill(UI_BACKGROUND_COLOR)

        self.nav_bar.draw()
        
        self.shop.rebuild()
        self.equipment.rebuild()
        self.grain.rebuild()

    def reset_actives(self) -> None:
        self.shop.active = False
        self.equipment.active = False
        self.contracts.active = False
        self.grain.active = False
        self.guide.active = False

        self.contracts.redraw_required = True

    def draw_shop(self, force: bool = False) -> None:
        self.reset_actives()
        self.shop.active = True

        redraw_shop = self.shop.update()
        if redraw_shop or force: self.shop.draw()

    def draw_equipment(self, force: bool = False) -> None:
        self.reset_actives()
        self.equipment.active = True

        redraw_equipment = self.equipment.update()
        if redraw_equipment or force: self.equipment.draw()

    def draw_contracts(self, force: bool = False) -> None:
        self.reset_actives()
        self.contracts.active = True

        redraw_contracts = self.contracts.update()
        if redraw_contracts or force: self.contracts.draw()

    def draw_grain(self, force: bool = False) -> None:
        self.reset_actives()
        self.grain.active = True

        redraw_grain = self.grain.update()
        if redraw_grain or force: self.grain.draw()

    def draw_guide(self, force: bool = False) -> None:
        self.reset_actives()
        self.guide.active = True

        redraw_guide = self.guide.update()
        if redraw_guide or force: self.guide.draw()

    def draw(self) -> None:
        self.screen.blit(self.rendered_surface, (0, 0))

        self.contracts.check_paddocks_fulfillment() # This one wants to know if paddock state changes happen each tick

        redraw_nav_bar = self.nav_bar.update()
        if redraw_nav_bar: self.nav_bar.draw()

        match self.nav_bar.get_selected():
            case 0: self.draw_shop()
            case 1: self.draw_equipment()
            case 2: self.draw_contracts()
            case 3: self.draw_grain()
            case 4: self.draw_guide()

    def force_draw_page(self) -> None:
        if self.shop.in_paddock_menu:
            self.shop.paddock_buy_menu.cancel_buy_paddock()

        if self.equipment.showing_destination_picker:
            self.equipment.cancel_task_assign()

        match self.nav_bar.get_selected():
            case 0: self.draw_shop(force=True)
            case 1: self.draw_equipment(force=True)
            case 3: self.draw_grain(force=True)
            case 4: self.draw_guide(force=True)