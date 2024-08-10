import pygame as pg

from resource_manager import ResourceManager
from events import Events

from UI.pygame_gui import Button
from UI.navbar import NavBar

from data import *

class Panel:
    def __init__(self, screen: pg.Surface, events: Events) -> None:
        self.screen: pg.Surface = screen
        self.events: Events = events

        self.SCREEN_WIDTH: int = self.screen.get_width()
        self.SCREEN_HEIGHT: int = self.screen.get_height()

        self.rect: pg.Rect = pg.Rect(0, 0, PANEL_WIDTH, self.SCREEN_HEIGHT)
        self.rendered_surface: pg.Surface = pg.Surface((PANEL_WIDTH, self.SCREEN_HEIGHT))

        self.nav_bar: NavBar = NavBar(self.rendered_surface, self.events, pg.Rect(0, 0, PANEL_WIDTH, 110))

        self.rebuild()

    def rebuild(self) -> None:
        self.rendered_surface.fill((255, 255, 255))

        self.nav_bar.draw()

    def draw(self) -> None:
        self.screen.blit(self.rendered_surface, (0, 0))

        redraw_nav_bar = self.nav_bar.update()
        if redraw_nav_bar: self.nav_bar.draw()