import pygame as pg

from UI.pygame_gui import Widget, Popup, Button, DropDown
from events import Events

from machinary import Tractor, Header, Tool
from farm import Shed
from sellpoints import SellPoint

from typing import List

class PopupType:
    def __init__(self) -> None:
        ...

class TractorNewTaskPopup(PopupType):
    WIDTH = 500
    HEIGHT = 400

    def __init__(self, events: Events, vehicle_name: str, shed: Shed, sell_points: List[SellPoint]) -> None:
        self.parent_surface = pg.display.get_surface()
        self.surface = pg.Surface((self.WIDTH, self.HEIGHT), pg.SRCALPHA)
        self.events = events

        self.vehicles = shed.vehicles
        self.tools = shed.tools
        self.sell_points = sell_points

        self.x = self.parent_surface.get_width() / 2 - self.WIDTH / 2
        self.y = self.parent_surface.get_height() / 2 - self.HEIGHT / 2

        self.rect = pg.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        self.widget_rect = pg.Rect(self.x, self.y + Popup.BANNER_HEIGHT, self.WIDTH, self.HEIGHT - Popup.BANNER_HEIGHT)

        self.widget = Widget(self.parent_surface, self.widget_rect)
        self.init_widget_components()

        self.popup = Popup(self.parent_surface, self.rect, 20, f"{vehicle_name} - New Task", self.widget, (0, 200, 255), (255, 255, 255), self.cancel, self.submit, self.events)

    def init_widget_components(self) -> None:
        widget = self.widget

        widget.font = pg.font.SysFont(None, 20)

        widget.tool_lbl = self.widget.font.render("Tool: ", True, (0, 0, 0))
        widget.paddock_lbl = self.widget.font.render("Paddock: ", True, (0, 0, 0))
        widget.destination_lbl = self.widget.font.render("Destination: ", True, (0, 0, 0))

        widget.tool_lbl_pos = (20, 20)
        widget.paddock_lbl_pos = (20, 40)
        widget.destination_lbl_pos = (20, 40)

        tool_dropdown_x = widget.tool_lbl_pos[0] + widget.tool_lbl.get_width()
        paddock_dropdown_x = widget.paddock_lbl_pos[0] + widget.paddock_lbl.get_width()
        destination_dropdown_x = widget.destination_lbl_pos[0] + widget.destination_lbl.get_width()

        widget.tool_dropdown_pos = (tool_dropdown_x, widget.tool_lbl_pos[1])
        widget.paddock_dropdown_pos = (paddock_dropdown_x, widget.tool_lbl_pos[1])
        widget.destination_dropdown_pos = (destination_dropdown_x, widget.tool_lbl_pos[1])

        widget.tool_dropdown_width = 400
        widget.paddock_dropdown_width = 10
        widget.destination_dropdown_width = 350

        widget.dropdown_height = 30
        widget.dropdown_bg_color = pg.Color(0, 200, 255)

        widget.tool_dropdown_buttons = [Button(widget.surface, 0, i * widget.dropdown_height, widget.tool_dropdown_width, widget.dropdown_height, widget.rect,
                                               (0, 200, 255), (0, 200, 255), (0, 0, 0), self.tools[i].full_name, 20, (20, 20, 20, 20), 0, 0, True,
                                               None) for i in range(len(self.tools))]

        widget.tool_dropdown = DropDown(widget.surface, widget.tool_dropdown_pos[0], widget.tool_dropdown_pos[1], widget.tool_dropdown_width, widget.dropdown_height,
                                        self.widget_rect, widget.tool_dropdown_buttons, widget.dropdown_bg_color, self.widget_tool_dropdown_on_change)

        
        widget.update = self.spoofed_widget_update

    def cancel(self) -> None:
        ...

    def submit(self) -> None:
        ...

    def widget_tool_dropdown_on_change(self) -> None:
        ...

    def spoofed_widget_update(self) -> None:
        self.widget.tool_dropdown.update()

    def draw(self) -> None:
        self.surface.blit(self.popup.surface, (0, 0))
        self.surface.blit(self.widget.surface, self.widget.rect)

    def update(self) -> None:
        redraw_req = self.popup.update()
        self.widget.update()

        if redraw_req:
            self.draw()