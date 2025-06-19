import pygame as pg
import logging

from resource_manager import ResourceManager
from save_manager import SaveManager
from paddock_manager import PaddockManager
from events import Events

from UI.pygame_gui import Button
from UI.popups import TractorNewTaskPopup, SelectCropPopup

from utils import utils
from farm import Shed
from machinary import Tractor, Header, Tool
from sellpoint_manager import SellpointManager
from destination import Destination
from data import *

from typing import List

class HeaderTool:
    def __init__(self, **args) -> None:
        self.tool_type = "Headers"
        self.full_name = "Header Front"

class Equipment:
    BUTTON_WIDTH = PANEL_WIDTH - 40

    def __init__(self, parent_surface: pg.Surface, events: Events, set_popup: callable, rect: pg.Rect, shed: Shed, sellpoint_manager: SellpointManager,
                 map_funcs: dict[str, object]) -> None:

        self.parent_surface = parent_surface
        self.events = events
        self.set_popup = set_popup

        self.rect = rect
        self.rect.y += 20
        self.shed = shed
        self.sellpoint_manager = sellpoint_manager

        self.map_darken = map_funcs["map_darken"]
        self.map_lighten = map_funcs["map_lighten"]
        self.set_location_click_callback = map_funcs["set_location_click_callback"]
        self.destroy_location_click_callback = map_funcs["destroy_location_click_callback"]
        self.fill_all_paddocks = map_funcs["fill_all_paddocks"]
        self.get_paddocks = map_funcs["get_paddocks"]

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

        self.showing_destination_picker = False

        self.destination_exit_btn = None
        self.destination_submit_btn = None

        self.selected_vehicle = None
        self.selected_tool = None
        self.selected_destination = None

        self.location_callback_has_happened = False

        self.active = False
        self.shed.set_equipment_draw(self.draw)

        self.selected_vehicle_unloading_headers = {}

    def close_popup(self) -> None:
        self.set_popup(None)

        self.rebuild()
        self.draw()

    def reset_map(self) -> None:
        logging.info("Unhiding all paddocks and removing map transparency...")

        self.fill_all_paddocks()
        self.map_lighten()

    def remove_destination_picker(self) -> None:
        self.showing_destination_picker = False

        self.draw()
        self.reset_map()
        self.destroy_location_click_callback()

    def cancel_task_assign(self) -> None:
        self.showing_destination_picker = False
        self.selected_vehicle_unloading_headers = {}

        self.draw()
        self.reset_map()
        self.destroy_location_click_callback()

    def assign_task(self, done_additional_popup: bool = False) -> None:
        if self.selected_destination is None: return

        if self.selected_tool.tool_type == "Seeders" and not done_additional_popup:
            logging.debug("Selected tool is a seeder. Opening crop selection popup...")
            self.set_popup(SelectCropPopup(self.events, self.sellpoint_manager, self.close_popup, self.remove_destination_picker, self.selected_tool.set_fill, self.assign_task))
            return

        elif self.selected_tool.tool_type == "Trailers" and not done_additional_popup:
            logging.debug("Selected tool is a trailer. Opening crop selection popup...")
            self.set_popup(SelectCropPopup(self.events, self.sellpoint_manager, self.close_popup, self.remove_destination_picker, self.selected_tool.set_fill, self.assign_task))
            return

        logging.info(f"Assigning vehicle: {self.selected_vehicle.full_name}, with tool: {self.selected_tool.full_name} a task at: {self.selected_destination.get_name()}...")

        self.shed.task_tractor(self.selected_vehicle, self.selected_tool, self.selected_destination)

        # There is a full header in the paddock because it would've been added by the get_excluded_paddocks call
        if self.selected_destination.is_paddock and self.selected_tool.tool_type == "Trailers":
            self.selected_vehicle.path.extend(self.selected_vehicle_unloading_headers[self.selected_vehicle.paddock].on_unloading_vehicle_assign(self.selected_vehicle))
            self.selected_vehicle.path.append(self.selected_vehicle_unloading_headers[self.selected_vehicle.paddock].position)

        elif self.selected_tool.tool_type == "Trailers":
            # Just delivering
            self.selected_vehicle.heading_to_sell = True

        self.remove_destination_picker()

    def assign_header_task(self, **args) -> None:
        if self.selected_destination is None: return

        logging.info(f"Assigning header: {self.selected_vehicle.full_name} a task at: {self.selected_destination.get_name()}...")

        self.shed.task_header(self.selected_vehicle, self.selected_destination)
        self.remove_destination_picker()

    def location_click_callback(self, destination: Destination) -> None:
        # Check if the callback has happened before because when clicking a paddock it doesnt use the mouse override, thus clicking whatever is behind the popup (a paddock)
        if not self.location_callback_has_happened:
            self.location_callback_has_happened = True
            return

        self.selected_destination = destination

        if self.selected_destination.is_paddock:
            paddock_index = int(self.selected_destination.destination.num) - 1
            if paddock_index in self.get_excluded_paddocks(self.selected_tool.tool_type):
                # The paddock is not the state the tool requires
                return

        elif self.selected_destination.is_sellpoint and self.selected_tool.tool_type in EXCLUDE_SELLPOINT_TOOLS:
            return

        self.rebuild_destination_picker(self.selected_tool, destination)
        self.draw()

    def get_excluded_paddocks(self, tool_type: str) -> List[int]:
        tool_states = TOOL_STATES[tool_type]
        desired_paddock_states = [tool_state - 1 for tool_state in tool_states]

        excluded_paddocks = []

        for p, paddock in enumerate(self.get_paddocks()):
            if paddock.state not in desired_paddock_states:
                excluded_paddocks.append(p)
                continue

            if tool_type == "Trailers":
                found_valid_header = False
                for vehicle in self.shed.vehicles:
                    if isinstance(vehicle, Header) and vehicle.paddock == int(paddock.num) - 1 and vehicle.waiting_for_unloading_vehicle_assign:
                        found_valid_header = True
                        self.selected_vehicle_unloading_headers[p] = vehicle
                        break
                
                if not found_valid_header:
                    excluded_paddocks.append(p)

        return excluded_paddocks

    def show_destination_picker(self, tool_index: int) -> None:
        logging.info("Entering destination selection mode. Darkening map and hiding un-necessary paddocks...")

        if tool_index == -1:
            self.selected_tool = HeaderTool()
        else:
            self.selected_tool = self.shed.tools[tool_index]
            
        self.showing_destination_picker = True
        self.location_callback_has_happened = False

        self.set_location_click_callback(self.location_click_callback)
        self.rebuild_destination_picker(self.selected_tool, Destination(None))
        
        excluded_paddocks = self.get_excluded_paddocks(self.selected_tool.tool_type)
        self.fill_all_paddocks(excluded_paddocks)

        self.map_darken()
        self.draw()       

    def trigger_vehicle_popup(self, vehicle_id: int) -> None:
        self.selected_vehicle = self.shed.get_vehicle(vehicle_id)

        if self.selected_vehicle.active == True:
            ... # TODO: Error vehicle already active popup
            return
        elif isinstance(self.selected_vehicle, Tractor):
            popup = TractorNewTaskPopup(self.events, self.selected_vehicle.full_name, self.shed, self.sellpoint_manager.sellpoints, self.equipment_buttons, self.draw,
                                        lambda: self.close_popup(), self.show_destination_picker)
        else:
            self.show_destination_picker(-1)
            self.location_callback_has_happened = True # This can be true since no popup ever happened
            return

        self.set_popup(popup)

    def rebuild(self) -> None:
        logging.debug("Rebuilding equipment menu...")

        self.rendered_surface.fill(UI_BACKGROUND_COLOR)
        self.equipment_buttons = []
        self.og_equipment_button_rects = []

        center = PANEL_WIDTH / 2

        button_height = 130
        header_button_height = button_height + 30
        button_spacing = 20

        y_inc = button_height + button_spacing

        self.scrollable_surface = pg.Surface((self.rect.w, (len(self.shed.vehicles) + len(self.shed.tools)) * (y_inc + 30)), pg.SRCALPHA)

        x, y = center - self.BUTTON_WIDTH / 2, 0

        # Vehicles
        for vehicle in self.shed.vehicles:
            if isinstance(vehicle, Header):
                bh = header_button_height
                y_inc = bh + button_spacing
            else:
                bh = button_height
                y_inc = bh + button_spacing

            button = Button(self.scrollable_surface, x, y, self.BUTTON_WIDTH, bh, self.rect,
                       UI_MAIN_COLOR, pg.Color(255, 100, 0), UI_TEXT_COLOR, "", 20, (20, 20, 20, 20), 0, 0, command=lambda vehicle=vehicle: self.trigger_vehicle_popup(vehicle.vehicle_id), authority=True)
            
            button.draw()
            self.equipment_buttons.append(button)
            self.og_equipment_button_rects.append(button.global_rect)

            name_lbl = self.title_font.render(f"{vehicle.brand} {vehicle.model}", True, UI_TEXT_COLOR)
            self.scrollable_surface.blit(name_lbl, (center - name_lbl.get_width()/2, y + 10))
            
            self.scrollable_surface.blit(self.body_font.render(f"Task: {vehicle.string_task}", True, UI_TEXT_COLOR), (60, y + 50))

            fuel_lbl = self.body_font.render(f"Fuel: {vehicle.fuel}L", True, UI_TEXT_COLOR)
            self.scrollable_surface.blit(fuel_lbl, (60, y + 80))

            if isinstance(vehicle, Header):
                fill_lbl = self.body_font.render(f"Fill ({vehicle.get_fill_type_str.capitalize()}): {round(vehicle.fill, 1)}T", True, UI_TEXT_COLOR)
                self.scrollable_surface.blit(fill_lbl, (60, y + 110))

            pdk_lbl = self.body_font.render(f"Paddock: {vehicle.paddock_text}", True, UI_TEXT_COLOR)
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
            self.scrollable_surface.blit(self.body_font.render(f"Fill ({tool.get_fill_type_str.capitalize()}): {round(tool.fill, 1)}T", True, UI_TEXT_COLOR), (60, y + 80))

            pdk_lbl = self.body_font.render(f"Paddock: {tool.paddock_text}", True, UI_TEXT_COLOR)
            self.scrollable_surface.blit(pdk_lbl, (PANEL_WIDTH - 60 - pdk_lbl.get_width(), y + 80))

            y += y_inc

        self.max_y = y

    def rebuild_destination_picker(self, tool: Tool | None, selected_destination: Destination) -> None:
        self.rendered_surface.fill(UI_BACKGROUND_COLOR)

        wrap_length = int(PANEL_WIDTH * 0.8)

        title_font = pg.font.SysFont(None, 70)
        selected_font = pg.font.SysFont(None, 55)
        body_font = pg.font.SysFont(None, 50)
        note_font = pg.font.SysFont(None, 40)

        title_font.align = pg.FONT_CENTER
        body_font.align = pg.FONT_LEFT

        title_lbl = title_font.render(f"Select destination for new job:", True, UI_TEXT_COLOR, wraplength=wrap_length)
        if isinstance(tool, HeaderTool):
            # Header
            machine_info_lbl = body_font.render(f"\nVehicle: {self.selected_vehicle.full_name}\n\n", True, UI_TEXT_COLOR, wraplength=wrap_length)
        else:
            machine_info_lbl = body_font.render(f"\nVehicle: {self.selected_vehicle.full_name}\nTool: {tool.full_name}\n\n", True, UI_TEXT_COLOR, wraplength=wrap_length)

        selected_lbl = selected_font.render(f"Selected: {selected_destination.name}", True, UI_TEXT_COLOR, wraplength=wrap_length)

        body_font.align = pg.FONT_CENTER
        info_lbl = note_font.render(f"\nNote: Tap on the destination you want on the map to select it.", True, UI_TEXT_COLOR, wraplength=wrap_length)

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

        if isinstance(tool, HeaderTool):
            submit_func = self.assign_header_task
        else:
            submit_func = self.assign_task

        self.destination_exit_btn = Button(self.rendered_surface, PANEL_WIDTH / 2 - btn_width / 2 - btn_width / 1.5, btn_y, btn_width, btn_width, self.rect, (0, 0, 0), (0, 0, 0), (0, 0, 0),
                               "", 10, (0, 0, 0, 0), 0, 0, True, self.cancel_task_assign, exit_img)
        
        self.destination_submit_btn = Button(self.rendered_surface, PANEL_WIDTH / 2 - btn_width / 2 + btn_width / 1.5, btn_y, btn_width, btn_width, self.rect, (0, 0, 0), (0, 0, 0), (0, 0, 0),
                                 "", 10, (0, 0, 0, 0), 0, 0, True, submit_func, submit_img)

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

            return redraw_all

        for i, button in enumerate(self.equipment_buttons):
            # Move the button's global_rect values to where they are with scrolling (only effects mouse press detection)
            og_button_rect = self.og_equipment_button_rects[i]
            button.global_rect = pg.Rect(og_button_rect.x, og_button_rect.y + self.scroll_y, og_button_rect.width, og_button_rect.height)

            # Mouse was pressed on the button and the mouse is released now (these buttons are different because the scrolling can press them)
            if not self.in_scroll and self.events.mouse_pos[1] > NAVBAR_HEIGHT:
                button_press = self.events.authority_mouse_just_released and button.global_rect.collidepoint(self.events.authority_mouse_start_press_location)
                button.update(button_press, lambda x: None)

        if self.in_scroll and self.events.authority_mouse_just_released:
            self.in_scroll = False

        if len(self.shed.vehicles) + len(self.shed.tools) != len(self.equipment_buttons):
            self.rebuild()
            return True

        if pg.mouse.get_pressed()[0] and self.rect.collidepoint(pg.mouse.get_pos()):
            if not self.scrolling_last_frame: pg.mouse.get_rel() # clear rel because user was not scrolling jast frame (avoids jitter)
            rx, ry = pg.mouse.get_rel()

            if (abs(rx) > 10 and abs(ry) > 10) or abs(ry) <= 2:
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

    def draw(self, rebuild: bool = False) -> None:
        if not self.showing_destination_picker:
            if rebuild: self.rebuild()

            self.rendered_surface.fill(UI_BACKGROUND_COLOR)
            self.rendered_surface.blit(self.scrollable_surface, (0, self.scroll_y))

        if self.active:
            self.parent_surface.blit(self.rendered_surface, self.rect)