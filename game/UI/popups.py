import pygame as pg

from UI.pygame_gui import Widget, Popup, Button, DropDown
from events import Events

from machinary import Tractor, Header, Tool
from farm import Shed
from sellpoints import SellPoint

from data import PANEL_WIDTH

from typing import List

class PopupType:
    def __init__(self) -> None:
        ...

class TractorNewTaskPopup(PopupType):
    WIDTH = 900
    HEIGHT = 600

    def __init__(self, events: Events, vehicle_name: str, shed: Shed, sell_points: List[SellPoint], equipment_buttons: List[Button],
                 draw_equipment_menu: callable, close_popup: callable) -> None:

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
        self.widget.tool_dropdown.select_button(self.tools[tool_index].full_name)

        self.widget.tool_dropdown.draw()
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

        widget.surface.fill((255, 255, 255))
        widget.font = pg.font.SysFont(None, 70)

        widget.tool_lbl = self.widget.font.render("Tool: ", True, (0, 0, 0))
        widget.paddock_lbl = self.widget.font.render("Paddock: ", True, (0, 0, 0))
        widget.destination_lbl = self.widget.font.render("Destination: ", True, (0, 0, 0))

        widget.tool_lbl_pos = (20, 60)
        widget.paddock_lbl_pos = (20, 200)
        widget.destination_lbl_pos = (20, 340)

        widget.surface.blit(widget.tool_lbl, widget.tool_lbl_pos)
        widget.surface.blit(widget.paddock_lbl, widget.paddock_lbl_pos)
        widget.surface.blit(widget.destination_lbl, widget.destination_lbl_pos)

        tool_dropdown_x = widget.tool_lbl_pos[0] + widget.tool_lbl.get_width()
        paddock_dropdown_x = widget.paddock_lbl_pos[0] + widget.paddock_lbl.get_width()
        destination_dropdown_x = widget.destination_lbl_pos[0] + widget.destination_lbl.get_width()

        widget.tool_dropdown_pos = (tool_dropdown_x, widget.tool_lbl_pos[1])
        widget.paddock_dropdown_pos = (paddock_dropdown_x, widget.tool_lbl_pos[1])
        widget.destination_dropdown_pos = (destination_dropdown_x, widget.tool_lbl_pos[1])

        widget.tool_dropdown_width = 700
        widget.paddock_dropdown_width = 10
        widget.destination_dropdown_width = 350

        widget.dropdown_height = 50
        widget.dropdown_bg_color = pg.Color(0, 200, 255)

        # These buttons are disabled on purpose so the user selects the tool from the equipment menu
        widget.tool_dropdown_buttons = [Button(widget.surface, 0, i * widget.dropdown_height, widget.tool_dropdown_width, widget.dropdown_height, widget.rect,
                                               (0, 200, 255), (0, 200, 255), (0, 0, 0), self.tools[i].full_name, 50, (20, 20, 20, 20), 0, 0, True,
                                               None) for i in range(len(self.tools))]

        widget.tool_dropdown = DropDown(widget.surface, widget.tool_dropdown_pos[0], widget.tool_dropdown_pos[1], widget.tool_dropdown_width, widget.dropdown_height,
                                        self.widget_rect, widget.tool_dropdown_buttons, widget.dropdown_bg_color, self.widget_tool_dropdown_on_change)

        widget.update = self.spoofed_widget_update

    def cancel(self) -> None:
        self.close_popup()

    def submit(self) -> None:
        self.close_popup()
        ...

    def widget_tool_dropdown_on_change(self) -> None:
        ...

    def spoofed_widget_update(self) -> None:
        self.widget.tool_dropdown.update()

    def draw(self) -> None:
        self.surface.blit(self.popup.surface, (0, 0))
        self.surface.blit(self.widget.surface, (0, self.popup.BANNER_HEIGHT))

    def update(self) -> None:
        redraw_req = self.popup.update()
        self.widget.update()

        if redraw_req:
            self.draw()