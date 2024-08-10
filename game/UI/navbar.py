import pygame as pg

from resource_manager import ResourceManager

from UI.pygame_gui import Button

from data import *

from typing import List

class NavBar:
    def __init__(self, screen: pg.Surface, rect: pg.Rect) -> None:
        self.screen: pg.Surface = screen
        self.rect: pg.Rect = rect
        
        self.rendered_surface: pg.Surface = pg.Surface((rect.w, rect.h))
        
        self.buttons: List[Button] = [Button(self.rendered_surface, 13, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Shop", 20, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 128, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Equipment", 20, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 248, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Paddocks", 20, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 368, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Grain", 20, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 488, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Finance", 20, (0, 0, 0, 0), 0, 0, True)]
        
        self.selected_button: int = 0

        self.rebuild()

    def rebuild(self) -> None:
        self.rendered_surface.fill((255, 255, 255))

        for i, button in enumerate(self.buttons):
            if self.selected_button == i: button.set_selected(True)
            else: button.set_selected(False)

            # draw gray outline around buttons
            pg.draw.rect(self.rendered_surface, (150, 150, 150), (button.x-5, button.y-5, button.width+10, button.height+10), border_radius=5)

            button.draw()

    def select_button(self, index: int) -> None:
        if len(index) <= len(self.buttons):
            self.selected_button = index

    def draw(self) -> None:
        self.screen.blit(self.rendered_surface, (self.rect.x, self.rect.y))