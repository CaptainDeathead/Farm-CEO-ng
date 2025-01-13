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
from machinary import Tractor, Header, Tool
from sellpoints import SellpointManager
from destination import Destination
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
        self.in_scroll = False

        self.selected_vehicle = None
        self.showing_destination_picker = False

        self.destination_exit_btn = None
        self.destination_submit_btn = None

    def close_popup(self) -> None:
        self.set_popup(None)

        self.rebuild()
        self.draw()

    def cancel_task_assign(self) -> None:
        self.showing_destination_picker = False

    def assign_task(self) -> None:
        self.showing_destination_picker = False
        
        ...

    def show_destination_picker(self, tool_index: int) -> None:
        tool = self.shed.tools[tool_index]
        self.showing_destination_picker = True

        self.rebuild_destination_picker(tool, Destination(None))
        self.draw()

    def trigger_vehicle_popup(self, vehicle_id: int) -> None:
        self.selected_vehicle = self.shed.get_vehicle(vehicle_id)

        if self.selected_vehicle.active == True:
            ... # TODO: Error vehicle already active popup
        elif isinstance(self.selected_vehicle, Tractor):
            popup = TractorNewTaskPopup(self.events, self.selected_vehicle.full_name, self.shed, self.sellpoint_manager.sellpoints, self.equipment_buttons, self.draw,
                                        lambda: self.close_popup(), self.show_destination_picker)
        else:
            ... # TODO: popup_type = HeaderNewTaskPopup

        self.set_popup(popup)

    def rebuild(self) -> None:
        logging.debug("Rebuilding equipment menu...")

        self.rendered_surface.fill(UI_BACKGROUND_COLOR)
        self.equipment_buttons = []

        center = PANEL_WIDTH / 2

        button_height = 130
        button_spacing = 20

        y_inc = button_height + button_spacing

        self.scrollable_surface = pg.Surface((self.rect.w, (len(self.shed.vehicles) + len(self.shed.tools)) * y_inc), pg.SRCALPHA)

        x, y = center - self.BUTTON_WIDTH / 2, 0

        # Vehicles
        for vehicle in self.shed.vehicles:
            button = Button(self.scrollable_surface, x, y, self.BUTTON_WIDTH, button_height, self.rect,
                       UI_MAIN_COLOR, UI_ACTIVE_COLOR, UI_TEXT_COLOR, "", 20, (20, 20, 20, 20), 0, 0, command=lambda vehicle=vehicle: self.trigger_vehicle_popup(vehicle.vehicle_id), authority=True)
            
            button.draw()
            self.equipment_buttons.append(button)
            self.og_equipment_button_rects.append(button.global_rect)

            name_lbl = self.title_font.render(f"{vehicle.brand} {vehicle.model}", True, UI_TEXT_COLOR)
            self.scrollable_surface.blit(name_lbl, (center - name_lbl.get_width()/2, y + 10))
            
            self.scrollable_surface.blit(self.body_font.render(f"Task: {vehicle.string_task}", True, UI_TEXT_COLOR), (60, y + 50))
            self.scrollable_surface.blit(self.body_font.render(f"Fuel: {vehicle.fuel}L", True, UI_TEXT_COLOR), (60, y + 80))

            pdk_lbl = self.body_font.render(f"Paddock: {vehicle.paddock}", True, UI_TEXT_COLOR)
            self.scrollable_surface.blit(pdk_lbl, (PANEL_WIDTH - 60 - pdk_lbl.get_width(), y + 80))

            y += y_inc

        # Tools
        for tool in self.shed.tools:
            button = Button(self.scrollable_surface, x, y, self.BUTTON_WIDTH, button_height, self.rect,
                       UI_TOOL_BUTTON_COLOR, UI_ACTIVE_COLOR, UI_TEXT_COLOR, "", 20, (20, 20, 20, 20), 0, 0, command=lambda: None, authority=True)
            
            button.draw()
            self.equipment_buttons.append(button)
            self.og_equipment_button_rects.append(button.global_rect)

            name_lbl = self.title_font.render(tool.full_name, True, UI_TEXT_COLOR)
            self.scrollable_surface.blit(name_lbl, (center - name_lbl.get_width()/2, y + 10))
            
            self.scrollable_surface.blit(self.body_font.render(f"Task: {tool.string_task}", True, UI_TEXT_COLOR), (60, y + 50))
            self.scrollable_surface.blit(self.body_font.render(f"Fill ({tool.fill_type}): {tool.fill}T", True, UI_TEXT_COLOR), (60, y + 80))

            pdk_lbl = self.body_font.render(f"Paddock: {tool.paddock}", True, UI_TEXT_COLOR)
            self.scrollable_surface.blit(pdk_lbl, (PANEL_WIDTH - 60 - pdk_lbl.get_width(), y + 80))

            y += y_inc

        self.max_y = y

    def rebuild_destination_picker(self, tool: Tool, selected_destination: Destination) -> None:
        self.rendered_surface.fill(UI_BACKGROUND_COLOR)

        wrap_length = int(PANEL_WIDTH * 0.8)

        self.title_font.align = pg.FONT_CENTER
        self.body_font.align = pg.FONT_LEFT

        title_lbl = self.title_font.render(f"Select destination for new job:", True, UI_TEXT_COLOR, wraplength=wrap_length)
        machine_info_lbl = self.body_font.render(f"\nVehicle: {self.selected_vehicle.full_name}\nTool: {tool.full_name}\n\n", True, UI_TEXT_COLOR, wraplength=wrap_length)

        selected_lbl = self.title_font.render(f"Selected: {selected_destination.name}", True, UI_TEXT_COLOR, wraplength=wrap_length)

        self.body_font.align = pg.FONT_CENTER
        info_lbl = self.body_font.render(f"\nNote: Tap on the destination you want on the map to select it.", True, UI_TEXT_COLOR, wraplength=wrap_length)

        lbls_height = title_lbl.get_height() + machine_info_lbl.get_height() + selected_lbl.get_height() + info_lbl.get_height()
        lbls_surface = pg.Surface((PANEL_WIDTH, lbls_height), pg.SRCALPHA)

        curr_y = 0

        lbls_surface.blit(title_lbl, (PANEL_WIDTH / 2 - title_lbl.get_width() / 2, curr_y))
        curr_y += title_lbl.get_height()

        lbls_surface.blit(machine_info_lbl, (PANEL_WIDTH / 2 - machine_info_lbl.get_width() / 2, curr_y))
        curr_y += machine_info_lbl.get_height()

        lbls_surface.blit(selected_lbl, (PANEL_WIDTH / 2 - selected_lbl.get_width() / 2, curr_y))
        curr_y += selected_lbl.get_height()

        lbls_surface.blit(info_lbl, (PANEL_WIDTH / 2 - info_lbl.get_width() / 2, curr_y))
        curr_y += 50

        self.rendered_surface.blit(lbls_surface, (PANEL_WIDTH / 2 - lbls_surface.get_width() / 2, 50))

        btn_width = 75
        btn_y = PANEL_WIDTH / 2 + lbls_surface.get_height() / 2 + 50

        exit_img = ResourceManager.load_image("Icons/cross.png")
        submit_img = ResourceManager.load_image("Icons/tick.png")

        self.destination_exit_btn = Button(self.rendered_surface, PANEL_WIDTH / 2 - btn_width / 2 - btn_width / 1.5, btn_y, btn_width, btn_width, pg.Rect(0, 0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
                               "", 10, (0, 0, 0, 0), 0, 0, True, self.cancel_task_assign, exit_img)
        
        self.destination_submit_btn = Button(self.rendered_surface, PANEL_WIDTH / 2 - btn_width / 2 + btn_width / 1.5, btn_y, btn_width, btn_width, pg.Rect(0, 0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
                                 "", 10, (0, 0, 0, 0), 0, 0, True, self.assign_task, submit_img)

        self.destination_exit_btn.draw()
        self.destination_submit_btn.draw()

    def update(self) -> bool:
        if self.showing_destination_picker:
            redraw_all = False

            redraw_required = self.destination_exit_btn.update(self.events.mouse_just_released, self.events.set_override)
            if redraw_required:
                redraw_all = True
                self.destination_exit_btn.draw()

            redraw_required = self.destination_submit_btn.update(self.events.mouse_just_released, self.events.set_override)
            if redraw_required:
                redraw_all = True
                self.destination_submit_btn.draw()

            if redraw_all:
                self.draw()

        for i, button in enumerate(self.equipment_buttons):
            # Move the button's global_rect values to where they are with scrolling (only effects mouse press detection)
            og_button_rect = self.og_equipment_button_rects[i]
            button.global_rect = pg.Rect(og_button_rect.x, og_button_rect.y + self.scroll_y, og_button_rect.width, og_button_rect.height)

            # Mouse was pressed on the button and the mouse is released now (these buttons are different because the scrolling can press them)
            if not self.in_scroll and self.events.mouse_pos[1] > NAVBAR_HEIGHT:
                button_press = self.events.authority_mouse_just_released and button.global_rect.collidepoint(self.events.authority_mouse_start_press_location)
                button.update(button_press, self.events.set_override)

        if self.in_scroll and self.events.authority_mouse_just_released:
            self.in_scroll = False

        if len(self.shed.vehicles) + len(self.shed.tools) != len(self.equipment_buttons):
            self.rebuild()
            return True

        if pg.mouse.get_pressed()[0] and self.rect.collidepoint(pg.mouse.get_pos()):
            if not self.scrolling_last_frame: pg.mouse.get_rel() # clear rel because user was not scrolling jast frame (avoids jitter)
            rx, ry = pg.mouse.get_rel()

            if (abs(rx) > 10 and abs(ry) > 10) or ry == 0:
                self.scrolling_last_frame = True
                return False

            self.in_scroll = True
            
            height = self.rendered_surface.get_height()
            if self.max_y > height:
                new_scroll_y = self.scroll_y + ry
                self.scroll_y = min(0, max((self.max_y - height + 40) * -1, new_scroll_y)) # + 40 for padding at the bottom

                self.scrolling_last_frame = True
                return True
            
        self.scrolling_last_frame = pg.mouse.get_pressed()[0]
        return False

    def draw(self) -> None:
        if not self.showing_destination_picker:
            self.rendered_surface.fill(UI_BACKGROUND_COLOR)
            self.rendered_surface.blit(self.scrollable_surface, (0, self.scroll_y))

        self.parent_surface.blit(self.rendered_surface, self.rect)