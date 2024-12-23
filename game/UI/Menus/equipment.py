import pygame as pg
import logging

from resource_manager import ResourceManager
from save_manager import SaveManager
from paddock_manager import PaddockManager
from events import Events

from UI.pygame_gui import Button
from UI.popups import TractorNewTaskPopup

from utils import utils
from farm import Shed
from machinary import Tractor
from sellpoints import SellpointManager
from data import *

from typing import List

class Equipment:
    BUTTON_WIDTH = PANEL_WIDTH - 40

    def __init__(self, parent_surface: pg.Surface, events: Events, set_popup: callable, rect: pg.Rect, shed: Shed, sellpoint_manager: SellpointManager) -> None:
        self.parent_surface = parent_surface
        self.events = events
        self.set_popup = set_popup

        self.rect = rect
        self.rect.y += 20
        self.shed = shed
        self.sellpoint_manager = sellpoint_manager

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        self.scrollable_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.title_font = pg.font.SysFont(None, 60)
        self.body_font = pg.font.SysFont(None, 40)

        self.equipment_buttons: List[Button] = []
        self.og_equipment_button_rects: List[pg.Rect] = []

        self.scroll_y = 0.0
        self.max_y = 0.0
        self.scrolling_last_frame = False

    def close_popup(self) -> None:
        self.set_popup(None)

        self.rebuild()
        self.draw()

    def trigger_vehicle_popup(self, vehicle_id: int) -> None:
        vehicle = self.shed.get_vehicle(vehicle_id)

        if vehicle.active == True:
            ... # TODO: Error vehicle already active popup
        elif isinstance(vehicle, Tractor):
            popup = TractorNewTaskPopup(self.events, vehicle.full_name, self.shed, self.sellpoint_manager.sellpoints, self.equipment_buttons, self.draw,
                                        lambda: self.close_popup())
        else:
            ... # TODO: popup_type = HeaderNewTaskPopup

        self.set_popup(popup)

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

        # Vehicles
        for vehicle in self.shed.vehicles:
            button = Button(self.scrollable_surface, x, y, self.BUTTON_WIDTH, button_height, self.rect,
                       (0, 200, 255), (0, 0, 255), white, "", 20, (20, 20, 20, 20), 0, 0, command=lambda vehicle=vehicle: self.trigger_vehicle_popup(vehicle.vehicle_id), authority=True)
            
            button.draw()
            self.equipment_buttons.append(button)
            self.og_equipment_button_rects.append(button.global_rect)

            name_lbl = self.title_font.render(f"{vehicle.brand} {vehicle.model}", True, white)
            self.scrollable_surface.blit(name_lbl, (center - name_lbl.get_width()/2, y + 10))
            
            self.scrollable_surface.blit(self.body_font.render(f"Task: {vehicle.string_task}", True, white), (60, y + 50))
            self.scrollable_surface.blit(self.body_font.render(f"Fuel: {vehicle.fuel}L", True, white), (60, y + 80))

            pdk_lbl = self.body_font.render(f"Paddock: {vehicle.paddock}", True, white)
            self.scrollable_surface.blit(pdk_lbl, (PANEL_WIDTH - 60 - pdk_lbl.get_width(), y + 80))

            y += y_inc

        # Tools
        for tool in self.shed.tools:
            button = Button(self.scrollable_surface, x, y, self.BUTTON_WIDTH, button_height, self.rect,
                       (150, 0, 255), (0, 0, 255), white, "", 20, (20, 20, 20, 20), 0, 0, command=lambda: None, authority=True)
            
            button.draw()
            self.equipment_buttons.append(button)
            self.og_equipment_button_rects.append(button.global_rect)

            name_lbl = self.title_font.render(tool.full_name, True, white)
            self.scrollable_surface.blit(name_lbl, (center - name_lbl.get_width()/2, y + 10))
            
            self.scrollable_surface.blit(self.body_font.render(f"Task: {tool.string_task}", True, white), (60, y + 50))
            self.scrollable_surface.blit(self.body_font.render(f"Fill ({tool.fill_type}): {tool.fill}T", True, white), (60, y + 80))

            pdk_lbl = self.body_font.render(f"Paddock: {tool.paddock}", True, white)
            self.scrollable_surface.blit(pdk_lbl, (PANEL_WIDTH - 60 - pdk_lbl.get_width(), y + 80))

            y += y_inc

        self.max_y = y

    def update(self) -> bool:
        for i, button in enumerate(self.equipment_buttons):
            # Move the button's global_rect values to where they are with scrolling (only effects mouse press detection)
            og_button_rect = self.og_equipment_button_rects[i]
            button.global_rect = pg.Rect(og_button_rect.x, og_button_rect.y + self.scroll_y, og_button_rect.width, og_button_rect.height)

            # Mouse was pressed on the button and the mouse is released now (these buttons are different because the scrolling can press them)
            button_press = self.events.authority_mouse_just_released and button.global_rect.collidepoint(self.events.authority_mouse_start_press_location)
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