import pygame as pg
import logging

from resource_manager import ResourceManager
from save_manager import SaveManager
from paddock_manager import PaddockManager
from sellpoint_manager import SellPoint
from destination import Destination
from events import Events

from time import time

from UI.pygame_gui import Button, DropDown
from utils import utils
from data import *
from typing import List, Dict


class PaddockBuyMenu:
    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect, map_funcs: dict[str, object], backtrack_path: object) -> None:
        self.parent_surface = parent_surface
        self.events = events

        self.rect = pg.Rect(rect.x, rect.y + 20, rect.w, rect.h - 20)

        self.map_darken = map_funcs["map_darken"]
        self.map_lighten = map_funcs["map_lighten"]
        self.set_location_click_callback = map_funcs["set_location_click_callback"]
        self.destroy_location_click_callback = map_funcs["destroy_location_click_callback"]
        self.fill_all_paddocks = map_funcs["fill_all_paddocks"]
        self.get_paddocks = map_funcs["get_paddocks"]

        self.backtrack_path = backtrack_path

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.title_font = pg.font.SysFont(None, 60)
        self.body_font = pg.font.SysFont(None, 40)

        self.showing_destination_picker = False

        self.destination_exit_btn = None
        self.destination_submit_btn = None

        self.selected_destination = None
        self.location_callback_has_happened = False

        self.active = False
        self.last_money = SaveManager().money

    def reset_map(self) -> None:
        logging.info("Unhiding all paddocks and removing map transparency...")

        self.fill_all_paddocks(draw_paint=True)
        self.map_lighten()

    def remove_destination_picker(self) -> None:
        self.showing_destination_picker = False

        self.draw()
        self.reset_map()
        self.destroy_location_click_callback()

    def location_click_callback(self, destination: Destination) -> None:
        if destination.is_paddock:
            paddock_index = int(destination.destination.num) - 1
            if paddock_index in self.get_excluded_paddocks():
                # The paddock is already owned
                return            

        self.rebuild_destination_picker(destination)
        self.draw()

        if destination is not None and destination.is_paddock:
            self.selected_destination = destination
        else:
            self.selected_destination = None

    def get_excluded_paddocks(self) -> List[int]:
        excluded_paddocks = []

        for p, paddock in enumerate(self.get_paddocks()):
            if paddock.owned_by == "player" or paddock.price > SaveManager().money:
                excluded_paddocks.append(p)

        return excluded_paddocks

    def show_destination_picker(self) -> None:
        logging.info("Entering destination selection mode. Darkening map and hiding un-necessary paddocks...")

        self.showing_destination_picker = True
        self.location_callback_has_happened = False

        self.set_location_click_callback(self.location_click_callback)
        self.rebuild_destination_picker(Destination(None))
        
        excluded_paddocks = self.get_excluded_paddocks()
        self.fill_all_paddocks(excluded_paddocks)

        self.map_darken()
        self.draw()

    def cancel_buy_paddock(self) -> None:
        self.showing_destination_picker = False

        self.draw()
        self.reset_map()
        self.destroy_location_click_callback()

        self.backtrack_path()

    def buy_paddock(self) -> None:
        if self.selected_destination is None: return

        paddock = self.selected_destination.destination
        if SaveManager().money < paddock.price:
            return

        paddock.owned_by = "player"
        paddock.rebuild_num()
        SaveManager().take_money(paddock.price)

        self.cancel_buy_paddock()

    def rebuild_destination_picker(self, selected_destination: Destination) -> None:
        if selected_destination is None: return

        self.rendered_surface.fill(UI_BACKGROUND_COLOR)

        wrap_length = int(PANEL_WIDTH * 0.8)

        title_font = pg.font.SysFont(None, 70)
        selected_font = pg.font.SysFont(None, 55)
        body_font = pg.font.SysFont(None, 50)
        note_font = pg.font.SysFont(None, 40)

        title_font.align = pg.FONT_CENTER
        body_font.align = pg.FONT_LEFT

        title_lbl = title_font.render(f"Select paddock to buy:", True, UI_TEXT_COLOR, wraplength=wrap_length)

        selected_lbl = selected_font.render(f"Selected: {selected_destination.name}", True, UI_TEXT_COLOR, wraplength=wrap_length)

        if selected_destination.destination is None or isinstance(selected_destination.destination, SellPoint):
            price_lbl = selected_font.render(f"Price: --", True, UI_TEXT_COLOR, wraplength=wrap_length)
        else:
            price_lbl = selected_font.render(f"Price: ${selected_destination.destination.price:,}", True, UI_TEXT_COLOR, wraplength=wrap_length)

        body_font.align = pg.FONT_CENTER
        info_lbl = note_font.render(f"\nNote: Tap on the destination you want on the map to select it.", True, UI_TEXT_COLOR, wraplength=wrap_length)

        lbls_height = title_lbl.get_height() + 40 + selected_lbl.get_height() + price_lbl.get_height() + info_lbl.get_height()
        lbls_surface = pg.Surface((PANEL_WIDTH, lbls_height), pg.SRCALPHA)

        curr_y = 0

        lbls_surface.blit(title_lbl, (PANEL_WIDTH / 2 - title_lbl.get_width() / 2, curr_y))
        curr_y += title_lbl.get_height() + 40

        lbls_surface.blit(selected_lbl, (PANEL_WIDTH / 2 - selected_lbl.get_width() / 2, curr_y))
        curr_y += selected_lbl.get_height()

        lbls_surface.blit(price_lbl, (PANEL_WIDTH / 2 - price_lbl.get_width() / 2, curr_y))
        curr_y += price_lbl.get_height()

        lbls_surface.blit(info_lbl, (PANEL_WIDTH / 2 - info_lbl.get_width() / 2, curr_y))
        curr_y += 50

        self.rendered_surface.blit(lbls_surface, (PANEL_WIDTH / 2 - lbls_surface.get_width() / 2, 50))

        btn_width = 75
        btn_y = PANEL_WIDTH / 2 + lbls_surface.get_height() / 2 + 50

        exit_img = ResourceManager.load_image("Icons/cross.png")
        submit_img = ResourceManager.load_image("Icons/tick.png")

        self.destination_exit_btn = Button(self.rendered_surface, PANEL_WIDTH / 2 - btn_width / 2 - btn_width / 1.5, btn_y, btn_width, btn_width, self.rect, (0, 0, 0), (0, 0, 0), (0, 0, 0),
                               "", 10, (0, 0, 0, 0), 0, 0, True, self.cancel_buy_paddock, exit_img)
        
        self.destination_submit_btn = Button(self.rendered_surface, PANEL_WIDTH / 2 - btn_width / 2 + btn_width / 1.5, btn_y, btn_width, btn_width, self.rect, (0, 0, 0), (0, 0, 0), (0, 0, 0),
                                 "", 10, (0, 0, 0, 0), 0, 0, True, self.buy_paddock, submit_img)

        self.destination_exit_btn.draw()
        self.destination_submit_btn.draw()

    def draw(self) -> None:
        self.parent_surface.blit(self.rendered_surface, (0, NAVBAR_HEIGHT))

    def update(self) -> None:
        self.destination_exit_btn.update(self.events.mouse_just_pressed, lambda x: None)
        self.destination_submit_btn.update(self.events.mouse_just_pressed, lambda x: None)
        self.draw()

class Shop:
    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect, map_funcs: Dict[str, object]) -> None:
        self.parent_surface = parent_surface
        self.events = events
        self.rect = rect

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.vehicles_dict = ResourceManager.load_json("Machinary/Vehicles/vehicles.json")
        self.tools_dict = ResourceManager.load_json("Machinary/Tools/tools.json")

        self.global_dict = {}
        self.global_dict.update(self.vehicles_dict)
        self.global_dict.update(self.tools_dict)

        self.current_items = self.global_dict

        self.buttons: List[Button] = []
        self.path: List[str] = []

        self.product_title_font = pg.font.SysFont(None, 80)
        self.product_lbls_font = pg.font.SysFont(None, 60)

        self.product_images: List[pg.Surface] = []
        self.current_image = 0
        self.last_image_change = time()

        self.last_100_pages = []
        self.easter_egg = False

        self.in_paddock_menu = False

        self.paddock_buy_menu = PaddockBuyMenu(self.parent_surface, self.events, self.rect, map_funcs, self.backtrack_path)

        self.not_enough_money_lbl = self.product_title_font.render("Not enough money!", True, (255, 0, 0))
        self.not_enough_xp_lbl = self.product_title_font.render("Not enough XP!", True, (255, 0, 0))

        self.buy_button = Button(self.rendered_surface, PANEL_WIDTH / 2 - 150, self.rect.h - 280, 300, 100, self.rect, UI_MAIN_COLOR,
                                  UI_MAIN_COLOR, UI_TEXT_COLOR, "Buy", 60, (20, 20, 20, 20), 0, 0, True, lambda: self.buy_selected())
        
        self.buy_button.hide()

        self.back_button = Button(self.rendered_surface, PANEL_WIDTH / 2 - 150, self.rect.h - 160, 300, 100, self.rect, UI_MAIN_COLOR,
                                  UI_MAIN_COLOR, UI_TEXT_COLOR, "Back", 60, (20, 20, 20, 20), 0, 0, True, lambda: self.backtrack_path())

        self.active = False
        self.just_rebuilt = False
        self.rebuild()

    def buy_selected(self) -> None:
        price = self.current_items["price"]

        machine_type = self.path[0]
        brand = self.path[1]
        model = self.path[2]

        SaveManager().set_money(SaveManager().money-price)
        
        if machine_type in ("Tractors", "Harvesters"): SaveManager().create_vehicle(machine_type == "Harvesters", brand, model)
        else: SaveManager().create_tool(machine_type, brand, model)

        SaveManager().save_game()

        self.path = []
        self.current_items = self.global_dict

        self.buy_button.hide()
        self.back_button.hide()

        self.rebuild()

    def backtrack_path(self) -> None:
        self.current_items = self.global_dict
        
        if self.in_paddock_menu:
            self.in_paddock_menu = False
            self.path = []
        else:
            if len(self.path) > 0:
                self.path.pop()

        for item in self.path:
            self.current_items = self.current_items[item]

        self.rebuild()

    def update_path(self, new_path_segment: str) -> None:
        self.path.append(new_path_segment)
        self.current_items = self.current_items[new_path_segment]

        self.rebuild()

    def rebuild_buyimg(self) -> None:
        self.rendered_surface.fill(UI_BACKGROUND_COLOR, (0, 0, PANEL_WIDTH, 200)) # clear any old images

        img = self.product_images[self.current_image]
        pos = (PANEL_WIDTH / 2, 120)

        utils.blit_centered(self.rendered_surface, img, pos, (img.get_width()/2, img.get_height()/2), 0.0)

    def check_image_cycle(self) -> bool:
        if time() - self.last_image_change >= 1:
            self.current_image += 1
            if self.current_image >= len(self.product_images): self.current_image = 0
            
            self.rebuild_buyimg()
            self.last_image_change = time()

            return True
        
        return False
    
    def check_can_buy(self) -> None:
        money_required = self.current_items["price"]
        xp_required = self.current_items["xp"]

        if SaveManager().xp < xp_required:
            self.rendered_surface.fill(UI_BACKGROUND_COLOR, (0, self.buy_button.rect.y, PANEL_WIDTH, self.buy_button.rect.h))
            self.rendered_surface.blit(self.not_enough_xp_lbl, (PANEL_WIDTH / 2 - self.not_enough_xp_lbl.get_width() / 2, self.buy_button.rect.y + 20))
            
            self.buy_button.hide()
            self.buy_button.draw()
        
        elif SaveManager().money < money_required:
            self.rendered_surface.fill(UI_BACKGROUND_COLOR, (0, self.buy_button.rect.y, PANEL_WIDTH, self.buy_button.rect.h))
            self.rendered_surface.blit(self.not_enough_money_lbl, (PANEL_WIDTH / 2 - self.not_enough_money_lbl.get_width() / 2, self.buy_button.rect.y + 20))

            self.buy_button.hide()
            self.buy_button.draw()
        
        else:
            self.buy_button.show()
            self.buy_button.draw()

    def open_paddocks_buy_menu(self) -> None:
        self.in_paddock_menu = True
        self.paddock_buy_menu.show_destination_picker()
        
        self.buy_button.hide()
        self.back_button.show()

        self.draw()

    def check_last_100(self) -> None:
        if len(self.last_100_pages) == 100:
            for item in self.last_100_pages:
                if item != "Case IH Maxxum 150": return

            self.easter_egg = True # congrats i guess...

    def rebuild_buyscr(self) -> None:
        logging.info("Rebuilding equipment buy menu...")

        self.product_images = []
        self.current_image = 0
        
        for image_path in self.current_items["anims"]:
            if image_path == "default" or self.current_items["anims"][image_path] is None: continue

            new_img = pg.transform.scale_by(ResourceManager.load_image(self.current_items["anims"][image_path], (32, 32)), 4)
            self.product_images.append(new_img)

        self.rebuild_buyimg()

        color = pg.Color(255, 255, 255)

        brand = self.path[-2]
        name = self.path[-1]
        title_lbl = self.product_lbls_font.render(f"{brand} {name}", True, color)

        # Very important code here, shhhhhhhh
        if len(self.last_100_pages) == 100: self.last_100_pages.pop(0)
        self.last_100_pages.append(f"{brand} {name}")
        self.check_last_100()

        self.rendered_surface.blit(title_lbl, (PANEL_WIDTH / 2 - title_lbl.get_width() / 2, 220))

        curr_y = 300

        for attr in self.current_items:
            fullcaps = False

            if attr in ("sizePx", "turningPoint", "hitch", "anims", "pipeOffset") or self.current_items[attr] is None: continue
            elif attr == "price":
                # int(<an_integar>):, in an f string formats with commas
                text = self.product_title_font.render(f"Price: ${self.current_items[attr]:,}", True, color)
                pos = (PANEL_WIDTH / 2 - text.get_width() / 2, self.rect.h - 350)

                self.rendered_surface.blit(text, pos)
                continue
            elif attr in ("xp", "hp"): fullcaps = True

            unit = ""
            match attr:
                case "max_fuel": unit = "L"
                case "storage": unit = "T"
                case "size": unit = "ft"

            final_attr = attr.capitalize()
            if fullcaps: final_attr = attr.upper()

            if final_attr == "Max_fuel": final_attr = "Fuel"

            text = self.product_lbls_font.render(f"{final_attr}: {self.current_items[attr]}{unit}", True, color)
            pos = (PANEL_WIDTH / 8, curr_y)

            self.rendered_surface.blit(text, pos)

            curr_y += text.get_height() + 5

        self.just_rebuilt = True

    def rebuild(self) -> None:
        logging.info("Rebuilding buy menu items...")

        self.rendered_surface.fill(UI_BACKGROUND_COLOR)
        self.buttons = []

        if len(self.path) == 3: return self.rebuild_buyscr()

        x = 25
        y = 50

        size = (self.rect.w - 25*4)/3 # padding = 25, 3 buttons in each row
        step = size + 25 # padding = 25

        for item in self.current_items:
            if self.easter_egg:
                self.buttons.append(Button(self.rendered_surface, x, y, size, size, self.rect, UI_MAIN_COLOR, UI_MAIN_COLOR, UI_TEXT_COLOR,
                                       item, 30, (20, 20, 20, 20), 0, 0, True, lambda item=item: self.update_path(item),
                                       image=ResourceManager.load_image("Sprites/linus.jpg", (size, size))))
            else:
                self.buttons.append(Button(self.rendered_surface, x, y, size, size, self.rect, UI_MAIN_COLOR, UI_MAIN_COLOR, UI_TEXT_COLOR,
                                       item, 30, (20, 20, 20, 20), 0, 0, True, lambda item=item: self.update_path(item)))
            
            x += step

            if x >= step * 3 + 25 - 5:
                y += step
                x = 25

        if len(self.path) == 0:
            paddocks_btn = Button(self.rendered_surface, x, y, size, size, self.rect, UI_MAIN_COLOR, UI_MAIN_COLOR, UI_TEXT_COLOR,
                              "Paddocks", 30, (20, 20, 20, 20), 0, 0, True, lambda: self.open_paddocks_buy_menu())
                            
            self.buttons.append(paddocks_btn)

        self.just_rebuilt = True

    def check_buyscr(self) -> bool:
        update = False

        update = self.check_image_cycle()
        self.check_can_buy()

        return update

    def update(self) -> bool:
        update = False

        if len(self.path) == 3:
            update = self.check_buyscr()
        elif self.in_paddock_menu:
            self.paddock_buy_menu.update()
        else:
            for button in self.buttons:
                button.update(self.events.mouse_just_pressed, self.events.set_override)

        if not self.in_paddock_menu:
            self.buy_button.update(self.events.mouse_just_pressed, self.events.set_override)
            self.back_button.update(self.events.mouse_just_pressed, self.events.set_override)

        if self.just_rebuilt:
            self.just_rebuilt = False
            update = True
        
        return update

    def draw(self) -> None:
        for button in self.buttons: button.draw()

        if len(self.path) > 0: self.back_button.show()
        else:
            if not self.in_paddock_menu: self.back_button.hide()

        self.back_button.draw()

        self.parent_surface.blit(self.rendered_surface, (self.rect.x, self.rect.y))