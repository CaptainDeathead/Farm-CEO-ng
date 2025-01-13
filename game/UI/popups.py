import pygame as pg

from UI.pygame_gui import Widget, Popup, Button, DropDown
from events import Events

from machinary import Tractor, Header, Tool
from farm import Shed
from sellpoints import SellPoint

from data import UI_BACKGROUND_COLOR, UI_MAIN_COLOR, UI_TEXT_COLOR, PANEL_WIDTH

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
        self.selected_tool_index = -1

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
