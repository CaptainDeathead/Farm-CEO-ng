import pygame as pg

from UI.pygame_gui import Widget, Popup, Button, DropDown
from events import Events

from save_manager import SaveManager
from machinary import Tractor, Header, Tool
from farm import Shed
from sellpoint_manager import SellpointManager
from sellpoints import SellPoint

from data import *

from typing import List

class PopupType:
    def __init__(self) -> None:
        ...

class TractorNewTaskPopup(PopupType):
    WIDTH = 900
    HEIGHT = 350

    def __init__(self, events: Events, vehicle_name: str, shed: Shed, sell_points: List[SellPoint], equipment_buttons: List[Button],
                 draw_equipment_menu: callable, close_popup: callable, show_destination_picker: callable) -> None:

        self.parent_surface = pg.display.get_surface()
        self.surface = pg.Surface((self.WIDTH, self.HEIGHT), pg.SRCALPHA)
        self.events = events

        self.vehicles = shed.vehicles
        self.tools = shed.tools
        self.sell_points = sell_points
        
        self.equipment_buttons = equipment_buttons
        self.selected_tool_index = 0

        self.draw_equipment_menu = draw_equipment_menu
        self.close_popup = close_popup
        self.show_destination_picker = show_destination_picker

        self.x = PANEL_WIDTH + 20
        self.y = self.parent_surface.get_height() / 2 - self.HEIGHT / 2

        self.rect = pg.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        self.widget_rect = pg.Rect(self.x, self.y + Popup.BANNER_HEIGHT, self.WIDTH, self.HEIGHT - Popup.BANNER_HEIGHT * 2)

        self.widget = Widget(self.parent_surface, self.widget_rect)
        self.init_widget_components()

        self.popup = Popup(self.parent_surface, pg.Rect(0, 0, self.WIDTH, self.HEIGHT), self.rect, 20, f"{vehicle_name} - New Task", self.widget, (63, 72, 204), (255, 255, 255),
                           self.cancel, self.submit, self.events)

        self.popup.draw()
        self.draw()

        self.rewire_equipment_buttons()

    def set_selected_tool(self, tool_index: int) -> None:
        self.selected_tool_index = tool_index
        self.widget.tool_button.text = self.tools[tool_index].full_name

        self.widget.tool_button.rebuild()
        self.widget.tool_button.draw()
        self.widget.draw()
        self.draw()

    def rewire_equipment_buttons(self) -> None:
        for i, vehicle in enumerate(self.vehicles):
            # Focus on the tools in the equipment menu
            self.equipment_buttons[i].set_opacity(128)
            self.equipment_buttons[i].draw()

            self.equipment_buttons[i].old_command = self.equipment_buttons[i].command
            self.equipment_buttons[i].command = lambda: None

        self.draw_equipment_menu()

        for i, tool in enumerate(self.tools):
            index = i + len(self.vehicles)

            self.equipment_buttons[index].old_command = self.equipment_buttons[index].command

            if tool.active:
                self.equipment_buttons[index].set_opacity(128)
                self.equipment_buttons[index].draw()

                self.equipment_buttons[index].command = lambda: None
            else:
                self.equipment_buttons[index].command = lambda i=i: self.set_selected_tool(i)

    def init_widget_components(self) -> None:
        widget = self.widget

        widget.surface.fill(UI_BACKGROUND_COLOR)
        widget.font = pg.font.SysFont(None, 70)

        widget.tool_lbl = self.widget.font.render("Tool: ", True, UI_TEXT_COLOR)
        widget.destination_lbl = self.widget.font.render("Destination: Submit the popup.", True, UI_TEXT_COLOR)

        widget.tool_lbl_pos = (20, 20)
        widget.destination_lbl_pos = (20, 110)

        tool_dropdown_x = widget.tool_lbl_pos[0] + widget.tool_lbl.get_width()
        destination_dropdown_x = widget.destination_lbl_pos[0] + widget.destination_lbl.get_width()

        widget.tool_dropdown_pos = (tool_dropdown_x, widget.tool_lbl_pos[1])
        widget.destination_dropdown_pos = (destination_dropdown_x, widget.tool_lbl_pos[1])

        widget.tool_dropdown_width = 700
        widget.destination_dropdown_width = 350

        widget.dropdown_height = 50

        # Button is disabled
        widget.tool_button = Button(widget.surface, tool_dropdown_x, widget.tool_lbl_pos[1], widget.tool_dropdown_width, widget.dropdown_height, widget.rect,
                                    UI_MAIN_COLOR, UI_MAIN_COLOR, UI_TEXT_COLOR, self.tools[0].full_name, 50, (20, 20, 20, 20), 0, 0, True,
                                    None)
        
        widget.tool_button.draw()
        
        widget.surface.blit(widget.tool_lbl, widget.tool_lbl_pos)
        widget.surface.blit(widget.destination_lbl, widget.destination_lbl_pos)

    def cancel(self) -> None:
        self.close_popup()

    def submit(self) -> None:
        self.close_popup()
        self.show_destination_picker(self.selected_tool_index)

    def draw(self) -> None:
        self.widget.surface.blit(self.widget.tool_lbl, self.widget.tool_lbl_pos)
        self.widget.surface.blit(self.widget.destination_lbl, self.widget.destination_lbl_pos)

        self.surface.blit(self.popup.surface, (0, 0))
        self.surface.blit(self.widget.surface, (0, self.popup.BANNER_HEIGHT))

    def update(self) -> None:
        redraw_req = self.popup.update()

        if redraw_req:
            self.draw()

        self.widget.update()

class SelectCropPopup(PopupType):
    WIDTH = 900
    HEIGHT = 500

    def __init__(self, events: Events, sellpoint_manager: SellpointManager, close_popup: object, remove_destination_picker: object, set_tool_fill: object,
                 tool_capacity: float, assign_task: callable, crop_filter: List[str] = []) -> None:
        self.parent_surface = pg.display.get_surface()
        self.surface = pg.Surface((self.WIDTH, self.HEIGHT), pg.SRCALPHA)

        self.events = events
        self.sellpoint_manager = sellpoint_manager

        self.close_popup = close_popup
        self.remove_destination_picker = remove_destination_picker
        self.set_tool_fill = set_tool_fill
        self.tool_capacity = tool_capacity
        self.assign_task = assign_task

        self.done_additional_fert_popup = False

        self.widget_rect = pg.Rect(0, Popup.BANNER_HEIGHT, self.WIDTH, self.HEIGHT - Popup.BANNER_HEIGHT * 2)
        self.widget = Widget(self.parent_surface, self.widget_rect)

        self.widget.surface.fill(UI_BACKGROUND_COLOR)

        self.rect = pg.Rect(0, 0, self.WIDTH, self.HEIGHT)

        self.x = PANEL_WIDTH + 20
        self.y = self.parent_surface.get_height() / 2 - self.HEIGHT / 2

        self.widget_global_rect = pg.Rect(self.x, self.y + Popup.BANNER_HEIGHT, self.widget_rect.w, self.widget_rect.h)
        self.global_rect = pg.Rect(self.x, self.y, self.rect.w, self.rect.h)

        btn_width = 350
        btn_height = 75

        dropdown_pos = (self.WIDTH / 2 - btn_width, self.HEIGHT / 2 - btn_height)

        self.fertiliser_mode = crop_filter == "Fertilisers"
        self.chemical_mode = crop_filter == "Chemicals"

        if self.fertiliser_mode:
            self.crop_selection_buttons = [
                Button(self.widget.surface, dropdown_pos[0], dropdown_pos[1], btn_width, btn_height, pg.Rect(0, 0, self.WIDTH, self.HEIGHT), UI_MAIN_COLOR, UI_ACTIVE_COLOR, UI_TEXT_COLOR,
                       f"{fert_type.capitalize()}", 40, (20, 20, 20, 20), 0, 0, True, authority=True) for fert_type in FERTILISERS
            ]
        elif self.chemical_mode:
            self.crop_selection_buttons = [
                Button(self.widget.surface, dropdown_pos[0], dropdown_pos[1], btn_width, btn_height, pg.Rect(0, 0, self.WIDTH, self.HEIGHT), UI_MAIN_COLOR, UI_ACTIVE_COLOR, UI_TEXT_COLOR,
                       f"{fert_type.capitalize()}", 40, (20, 20, 20, 20), 0, 0, True, authority=True) for fert_type in CHEMICALS
            ]
        else:
            self.crop_selection_buttons = [
                Button(self.widget.surface, dropdown_pos[0], dropdown_pos[1], btn_width, btn_height, pg.Rect(0, 0, self.WIDTH, self.HEIGHT), UI_MAIN_COLOR, UI_ACTIVE_COLOR, UI_TEXT_COLOR,
                    f"{crop_type.capitalize()} ({round(sellpoint_manager.get_stored_amount(crop_type), 1)}T)", 40, (20, 20, 20, 20), 0, 0, True, authority=True)
                    for crop_type in CROP_TYPES
            ]

        if len(self.crop_selection_buttons) == 0:
            # TODO: NO CROPS OWNED SCREEN, MAYBE TAKE USER TO CROP BUY MENU
            self.crop_selection_buttons.append(
                Button(self.widget.surface, dropdown_pos[0], dropdown_pos[1], btn_width, btn_height, pg.Rect(0, 0, self.WIDTH, self.HEIGHT), UI_MAIN_COLOR, UI_ACTIVE_COLOR, UI_TEXT_COLOR,
                   f"NO CROP (N/A)", 40, (20, 20, 20, 20), 0, 0, True, authority=True)
            )

            self.submit = self.cancel

        self.crop_selection_dropdown = DropDown(self.widget.surface, self.WIDTH / 2 - btn_width / 2, 20, btn_width, btn_height,
                                                self.widget_global_rect, self.crop_selection_buttons, UI_BACKGROUND_COLOR, lambda: None)

        self.popup = Popup(self.parent_surface, self.rect, self.global_rect, 20, f"New Task - Select Crop Type", self.widget, (63, 72, 204), (255, 255, 255),
                           self.cancel, self.submit, self.events)

        self.popup.draw()
        self.draw()

    def get_max_fertiliser_buy_amount(self, selected_fert: str) -> float:
        stored_amount = self.sellpoint_manager.get_stored_amount(selected_fert)
        buy_amount = max(0, self.tool_capacity - stored_amount)
        max_affordable_amount = SaveManager().money // FERTILISER_PRICES[selected_fert]

        return min(buy_amount, max_affordable_amount)

    def get_max_chemical_buy_amount(self, selected_chem: str) -> float:
        stored_amount = self.sellpoint_manager.get_stored_amount(selected_chem)
        buy_amount = max(0, self.tool_capacity - stored_amount)
        max_affordable_amount = SaveManager().money // CHEMICAL_PRICES[selected_chem]

        return min(buy_amount, max_affordable_amount)

    def cancel(self) -> None:
        self.close_popup()
        self.remove_destination_picker()

    def submit(self) -> None:
        self.close_popup()
        self.remove_destination_picker()

        selected_item = self.crop_selection_dropdown.get_selected_text().lower()

        if self.fertiliser_mode:
            total_buy_amount = self.get_max_fertiliser_buy_amount(selected_item)

            SaveManager().take_money(total_buy_amount * FERTILISER_PRICES[selected_item])
            old_crop_type, old_amount = self.set_tool_fill(FILL_TYPES.index(selected_item), total_buy_amount)
        elif self.chemical_mode:
            total_buy_amount = self.get_max_chemical_buy_amount(selected_item)

            SaveManager().take_money(total_buy_amount * CHEMICAL_PRICES[selected_item])
            old_crop_type, old_amount = self.set_tool_fill(FILL_TYPES.index(selected_item), total_buy_amount)
        else:
            crop_type = selected_item.split(" ")[0]
            crop_amount = min(self.tool_capacity, self.sellpoint_manager.get_stored_amount(crop_type))
            crop_index = FILL_TYPES.index(crop_type)

            self.sellpoint_manager.take_crop(crop_type, crop_amount)
            old_crop_type, old_amount = self.set_tool_fill(crop_index, crop_amount)

            buy_crop_amount = max(0, self.tool_capacity - (crop_amount + old_amount))

            self.set_tool_fill(crop_index, buy_crop_amount + old_amount + crop_amount)
            SaveManager().take_money(BASE_CROP_PRICES[crop_index] * 0.15 * buy_crop_amount)

        if old_amount > 0 and old_crop_type in FILL_TYPES:
            self.sellpoint_manager.store_crop(FILL_TYPES[old_crop_type], old_amount)

        self.assign_task(done_additional_popup=True)

    def draw(self) -> None:
        self.surface.blit(self.popup.surface, (0, 0))
        self.surface.blit(self.widget.surface, (0, self.popup.BANNER_HEIGHT))

    def update(self) -> None:
        self.crop_selection_dropdown.update(self.events.authority_mouse_just_released)
        self.crop_selection_dropdown.draw()

        self.popup.update()

        self.draw()

class OKPopup(PopupType):
    WIDTH = 900
    HEIGHT = 500

    def __init__(self, events: Events, close_popup: object, title: str, description: str) -> None:
        self.parent_surface = pg.display.get_surface()
        self.surface = pg.Surface((self.WIDTH, self.HEIGHT), pg.SRCALPHA)

        self.events = events
        self.close_popup = close_popup
        
        self.title = title
        self.description = description

        self.widget_rect = pg.Rect(0, Popup.BANNER_HEIGHT, self.WIDTH, self.HEIGHT - Popup.BANNER_HEIGHT * 2)
        self.widget = Widget(self.parent_surface, self.widget_rect)

        self.widget.surface.fill(UI_BACKGROUND_COLOR)

        self.rect = pg.Rect(0, 0, self.WIDTH, self.HEIGHT)

        self.x = PANEL_WIDTH + 20
        self.y = self.parent_surface.get_height() / 2 - self.HEIGHT / 2

        self.widget_global_rect = pg.Rect(self.x, self.y + Popup.BANNER_HEIGHT, self.widget_rect.w, self.widget_rect.h)
        self.global_rect = pg.Rect(self.x, self.y, self.rect.w, self.rect.h)

        self.widget.surface.blit(pg.font.SysFont(None, 60).render(self.description, True, UI_TEXT_COLOR, wraplength=self.widget.rect.w - 40), (20, 20))

        self.popup = Popup(self.parent_surface, self.rect, self.global_rect, 20, self.title, self.widget, (63, 72, 204), (255, 255, 255),
                           self.cancel, self.submit, self.events, show_exit_button=False)

        self.popup.draw()
        self.draw()

    def cancel(self) -> None:
        self.close_popup()

    def submit(self) -> None:
        self.close_popup()

    def draw(self) -> None:
        self.surface.blit(self.popup.surface, (0, 0))
        self.surface.blit(self.widget.surface, (0, self.popup.BANNER_HEIGHT))

    def update(self) -> None:
        self.popup.update()
        self.draw()

class OKCancelPopup(PopupType):
    WIDTH = 900
    HEIGHT = 500

    def __init__(self, events: Events, close_popup: object, submit_func: object, title: str, description: str) -> None:
        self.parent_surface = pg.display.get_surface()
        self.surface = pg.Surface((self.WIDTH, self.HEIGHT), pg.SRCALPHA)

        self.events = events
        self.close_popup = close_popup
        self.submit_func = submit_func
        
        self.title = title
        self.description = description

        self.widget_rect = pg.Rect(0, Popup.BANNER_HEIGHT, self.WIDTH, self.HEIGHT - Popup.BANNER_HEIGHT * 2)
        self.widget = Widget(self.parent_surface, self.widget_rect)

        self.widget.surface.fill(UI_BACKGROUND_COLOR)

        self.rect = pg.Rect(0, 0, self.WIDTH, self.HEIGHT)

        self.x = PANEL_WIDTH + 20
        self.y = self.parent_surface.get_height() / 2 - self.HEIGHT / 2

        self.widget_global_rect = pg.Rect(self.x, self.y + Popup.BANNER_HEIGHT, self.widget_rect.w, self.widget_rect.h)
        self.global_rect = pg.Rect(self.x, self.y, self.rect.w, self.rect.h)

        self.widget.surface.blit(pg.font.SysFont(None, 60).render(self.description, True, UI_TEXT_COLOR, wraplength=self.widget.rect.w - 40), (20, 20))

        self.popup = Popup(self.parent_surface, self.rect, self.global_rect, 20, self.title, self.widget, (63, 72, 204), (255, 255, 255),
                           self.cancel, self.submit, self.events)

        self.popup.draw()
        self.draw()

    def cancel(self) -> None:
        self.close_popup()

    def submit(self) -> None:
        self.submit_func()
        self.close_popup()

    def draw(self) -> None:
        self.surface.blit(self.popup.surface, (0, 0))
        self.surface.blit(self.widget.surface, (0, self.popup.BANNER_HEIGHT))

    def update(self) -> None:
        self.popup.update()
        self.draw()