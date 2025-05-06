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

        page_height = pg.Rect(0, self.NAVBAR_HEIGHT, PANEL_WIDTH, self.SCREEN_HEIGHT - self.NAVBAR_HEIGHT)

        self.shop = Shop(self.rendered_surface, self.events, page_height)
        self.equipment = Equipment(self.rendered_surface, self.events, self.set_popup, page_height, shed, sellpoint_manager, map_funcs)

        self.rebuild()

    def rebuild(self) -> None:
        logging.info("Rebuilding panel...")

        self.rendered_surface.fill(UI_BACKGROUND_COLOR)

        self.nav_bar.draw()
        
        self.shop.rebuild()
        self.equipment.rebuild()

    def reset_actives(self) -> None:
        self.shop.active = False
        self.equipment.active = False

    def draw_shop(self, force: bool = False) -> None:
        self.reset_actives()
        self.shop.active = True

        redraw_shop = self.shop.update()
        if redraw_shop or force: self.shop.draw()

    def draw_equipment(self, force: bool = False) -> None:
        self.equipment.active = True

        redraw_equipment = self.equipment.update()
        if redraw_equipment or force: self.equipment.draw()

    def draw(self) -> None:
        self.screen.blit(self.rendered_surface, (0, 0))

        redraw_nav_bar = self.nav_bar.update()
        if redraw_nav_bar: self.nav_bar.draw()

        match self.nav_bar.get_selected():
            case 0: self.draw_shop()
            case 1: self.draw_equipment()

    def force_draw_page(self) -> None:
        match self.nav_bar.get_selected():
            case 0: self.draw_shop(force=True)
            case 1: self.draw_equipment(force=True)