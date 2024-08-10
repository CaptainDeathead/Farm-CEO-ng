import pygame as pg

from resource_manager import ResourceManager
from events import Events

from UI.pygame_gui import Button

from data import *

from typing import List

class NavBar:
    def __init__(self, screen: pg.Surface, events: Events, rect: pg.Rect) -> None:
        self.screen: pg.Surface = screen
        self.events: Events = events
        self.rect: pg.Rect = rect
        
        self.rendered_surface: pg.Surface = pg.Surface((rect.w, rect.h))
        
        self.buttons: List[Button] = [Button(self.rendered_surface, 13, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Shop", 20, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 128, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Equipment", 20, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 248, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Contracts", 20, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 368, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Grain", 20, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 488, 6, 120, 100, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Finance", 20, (0, 0, 0, 0), 0, 0, True)]
        
        self.selected_button: int = 0
        self.just_rebuilt: bool = False

        self.rebuild()

    def rebuild(self, rebuild_buttons: bool = False) -> None:
        self.rendered_surface.fill((255, 255, 255))

        for i, button in enumerate(self.buttons):
            if self.selected_button == i: button.set_selected(True)
            else: button.set_selected(False)

            # draw gray outline around buttons
            pg.draw.rect(self.rendered_surface, (150, 150, 150), (button.x-5, button.y-5, button.width+10, button.height+10), border_radius=5)

            if rebuild_buttons: button.rebuild()

            button.draw()

    def select_button(self, index: int) -> None:
        if index <= len(self.buttons):
            self.selected_button = index

            self.rebuild(rebuild_buttons=True)
            self.just_rebuilt = True

    def check_events(self) -> None:
        if self.events.mouse_just_pressed:
            # mouse doesnt collide with navbar
            if not self.rect.collidepoint(self.events.mouse_pos): return
            
            for button in self.buttons:
                # mouse doesnt collide with button
                if not button.rect.collidepoint(self.events.mouse_pos): continue
               
                if button.selected: break # button already focused 

                self.select_button(self.buttons.index(button))
                break

    def draw(self) -> None:
        self.screen.blit(self.rendered_surface, (self.rect.x, self.rect.y))

    def update(self) -> bool:
        self.check_events()

        if self.just_rebuilt:
            self.just_rebuilt = False
            return True
        
        return False