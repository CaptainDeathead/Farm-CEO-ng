import pygame as pg

from resource_manager import ResourceManager
from events import Events

from UI.pygame_gui import Button

from data import *

from typing import List

class NavBar:
    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect, switch_cmd: callable) -> None:
        self.parent_surface = parent_surface
        self.events = events
        self.rect = rect
        self.switch_cmd = switch_cmd
        
        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        
        self.buttons: List[Button] = [Button(self.rendered_surface, 13, 6, 120, 100, self.rect, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Shop", 30, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 128, 6, 120, 100, self.rect, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Equipment", 30, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 248, 6, 120, 100, self.rect, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Map", 30, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 368, 6, 120, 100, self.rect, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Grain", 30, (0, 0, 0, 0), 0, 0, True),
                                      Button(self.rendered_surface, 488, 6, 120, 100, self.rect, (0, 200, 255), (0, 0, 200), (255, 255, 255), "Finance", 30, (0, 0, 0, 0), 0, 0, True)]
        
        self.selected_button = 0
        self.just_rebuilt = False

        self.rebuild()

    def get_selected(self) -> int: return self.selected_button

    def rebuild(self, rebuild_buttons: bool = False) -> None:
        self.rendered_surface.fill((255, 255, 255))

        for i, button in enumerate(self.buttons):
            if self.selected_button == i: button.set_selected(True)
            else: button.set_selected(False)

            # draw gray outline around buttons
            pg.draw.rect(self.rendered_surface, (150, 150, 150), (button.x-5, button.y-5, button.width+10, button.height+10), border_radius=5)

            if rebuild_buttons: button.rebuild()

            button.draw()

        self.just_rebuilt = True

    def select_button(self, index: int) -> None:
        if index <= len(self.buttons):
            self.selected_button = index

            self.rebuild(rebuild_buttons=True)
            self.switch_cmd()

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
        self.parent_surface.blit(self.rendered_surface, self.rect)

    def update(self) -> bool:
        self.check_events()

        if self.just_rebuilt:
            self.just_rebuilt = False
            return True
        
        return False