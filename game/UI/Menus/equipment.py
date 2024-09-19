import pygame as pg
import logging

from resource_manager import ResourceManager
from save_manager import SaveManager
from paddock_manager import PaddockManager
from events import Events

from UI.pygame_gui import Button

from utils import utils
from farm import Shed
from data import *

from typing import List

class Equipment:
    BUTTON_WIDTH = PANEL_WIDTH - 40

    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect, shed: Shed) -> None:
        self.parent_surface = parent_surface
        self.events = events
        self.rect = rect
        self.rect.y += 20
        self.shed = shed

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        self.scrollable_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.title_font = pg.font.SysFont(None, 60)
        self.body_font = pg.font.SysFont(None, 40)

        self.equipment_buttons: List[Button] = []

        self.scroll_y = 0.0
        self.max_y = 0.0
        self.scrolling_last_frame = False

    def rebuild(self) -> None:
        logging.debug("Rebuilding equipment menu...")

        self.rendered_surface.fill((255, 255, 255))
        self.equipment_buttons = []

        white = pg.Color(255, 255, 255)
        center = PANEL_WIDTH / 2

        button_height = 130
        button_spacing = 20

        y_inc = button_height + button_spacing

        self.scrollable_surface = pg.Surface((self.rect.w, (len(self.shed.vehicles) + len(self.shed.tools)) * y_inc), pg.SRCALPHA)

        x, y = center - self.BUTTON_WIDTH / 2, 0

        for vehicle in self.shed.vehicles:
            button = Button(self.scrollable_surface, x, y, self.BUTTON_WIDTH, button_height, self.rect,
                       (0, 200, 255), (0, 0, 255), white, "", 20, (20, 20, 20, 20), 0, 0, command=lambda: None)
            
            button.draw()
            self.equipment_buttons.append(button)

            name_lbl = self.title_font.render(f"{vehicle.brand} {vehicle.model}", True, white)
            self.scrollable_surface.blit(name_lbl, (center - name_lbl.get_width()/2, y + 10))
            
            self.scrollable_surface.blit(self.body_font.render(f"Task: {vehicle.string_task}", True, white), (60, y + 50))
            self.scrollable_surface.blit(self.body_font.render(f"Fuel: {vehicle.fuel}L", True, white), (60, y + 80))

            pdk_lbl = self.body_font.render(f"Paddock: {vehicle.paddock}", True, white)
            self.scrollable_surface.blit(pdk_lbl, (PANEL_WIDTH - 60 - pdk_lbl.get_width(), y + 80))

            y += y_inc

        # TODO: Tools
        # ...

        self.max_y = y

    def update(self) -> bool:
        for button in self.equipment_buttons:
            # Mouse was pressed on the button and the mouse is released now (these buttons are different because the scrolling can press them)
            button_press = self.events.mouse_just_released and button.global_rect.collidepoint(self.events.mouse_start_press_location)
            button.update(button_press, self.events.set_override)

        if len(self.shed.vehicles) + len(self.shed.tools) != len(self.equipment_buttons):
            self.rebuild()
            
            return True

        if pg.mouse.get_pressed()[0] and self.rect.collidepoint(pg.mouse.get_pos()):
            if not self.scrolling_last_frame: pg.mouse.get_rel() # clear rel because user was not scrolling jast frame (avoids jitter)
            rx, ry = pg.mouse.get_rel()

            if (abs(rx) > 10 and abs(ry) > 10) or ry == 0:
                self.scrolling_last_frame = True
                return False
            
            height = self.rendered_surface.get_height()
            if self.max_y > height:
                new_scroll_y = self.scroll_y + ry
                self.scroll_y = min(0, max((self.max_y - height + 40) * -1, new_scroll_y)) # + 40 for padding at the bottom

                self.scrolling_last_frame = True
                return True
            
        self.scrolling_last_frame = pg.mouse.get_pressed()[0]
        return False

    def draw(self) -> None:
        self.rendered_surface.fill((255, 255, 255))

        self.rendered_surface.blit(self.scrollable_surface, (0, self.scroll_y))
        self.parent_surface.blit(self.rendered_surface, self.rect)