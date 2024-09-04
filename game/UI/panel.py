import pygame as pg

from resource_manager import ResourceManager
from events import Events

from UI.pygame_gui import Button
from UI.navbar import NavBar

from UI.Menus.shop import Shop

from data import *

class Panel:
    NAVBAR_HEIGHT = 110

    def __init__(self, screen: pg.Surface, events: Events) -> None:
        self.screen: pg.Surface = screen
        self.events: Events = events

        self.SCREEN_WIDTH: int = self.screen.get_width()
        self.SCREEN_HEIGHT: int = self.screen.get_height()

        self.rect: pg.Rect = pg.Rect(0, 0, PANEL_WIDTH, self.SCREEN_HEIGHT)
        self.rendered_surface: pg.Surface = pg.Surface((PANEL_WIDTH, self.SCREEN_HEIGHT))

        self.nav_bar: NavBar = NavBar(self.rendered_surface, self.events, pg.Rect(0, 0, PANEL_WIDTH, self.NAVBAR_HEIGHT))

        self.shop = Shop(self.rendered_surface, self.events, pg.Rect(0, self.NAVBAR_HEIGHT, PANEL_WIDTH, self.SCREEN_HEIGHT - self.NAVBAR_HEIGHT))

        self.rebuild()

    def rebuild(self) -> None:
        self.rendered_surface.fill((255, 255, 255))

        self.nav_bar.draw()
        
        self.shop.rebuild()

    def draw_shop(self) -> None:
        redraw_shop = self.shop.update()
        if redraw_shop: self.shop.draw()

    def draw(self) -> None:
        self.screen.blit(self.rendered_surface, (0, 0))

        redraw_nav_bar = self.nav_bar.update()
        if redraw_nav_bar: self.nav_bar.draw()

        match self.nav_bar.get_selected():
            case 0: self.draw_shop()