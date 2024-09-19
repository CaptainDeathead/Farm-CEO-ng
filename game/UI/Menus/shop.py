import pygame as pg
import logging

from resource_manager import ResourceManager
from save_manager import SaveManager
from paddock_manager import PaddockManager
from events import Events

from time import time

from UI.pygame_gui import Button, DropDown
from utils import utils
from data import *
from typing import List

class PaddockBuyMenu:
    DROPDOWN_WIDTH = 100
    SEGMENT_HEIGHT = 50
    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect) -> None:
        self.parent_surface = parent_surface
        self.events = events
        self.rect = rect

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.dropdown = DropDown(self.rendered_surface, PANEL_WIDTH / 2 - self.DROPDOWN_WIDTH / 2, 50, self.DROPDOWN_WIDTH,
                                 self.SEGMENT_HEIGHT, self.rect, self.get_buttons_for_dropdown(), (0, 200, 255), self.rebuild)
        
        self.product_title_font = pg.font.SysFont(None, 80)

        self.not_enough_money_lbl = self.product_title_font.render("Not enough money!", True, (255, 0, 0))

        self.buy_button = Button(self.rendered_surface, PANEL_WIDTH / 2 - 150, self.rect.h - 280, 300, 100, self.rect, (0, 200, 255),
                                  (0, 200, 255), (255, 255, 255), "Buy", 60, (20, 20, 20, 20), 0, 0, True, lambda: self.buy_selected())
        
        self.last_money = SaveManager().money

        self.rebuild()

    def get_buttons_for_dropdown(self) -> List[Button]:
        all_paddocks = PaddockManager().paddocks
        unowned_paddocks = []

        for paddock in all_paddocks:
            if paddock.owned_by == "player": continue
            unowned_paddocks.append(paddock)

        buttons = [
            Button(self.rendered_surface, 0, (int(paddock.num) - 1) * self.SEGMENT_HEIGHT, self.DROPDOWN_WIDTH, self.SEGMENT_HEIGHT, self.rect,
                   (0, 200, 255), (0, 200, 255), (0, 0, 0), paddock.num, 50, (5, 5, 5, 5), 0, 0, True) for paddock in unowned_paddocks
        ]

        return buttons

    def buy_selected(self) -> None:
        selected_paddock = int(self.dropdown.get_selected_text())-1
        paddock_area = PaddockManager().paddocks[selected_paddock].hectares

        # Paddock price = Area * 12000
        price = paddock_area * 12000

        PaddockManager().paddocks[selected_paddock].owned_by = "player"
        PaddockManager().paddocks[selected_paddock].rebuild_num()
        SaveManager().set_money(SaveManager().money - price)

        self.dropdown = DropDown(self.rendered_surface, PANEL_WIDTH / 2 - self.DROPDOWN_WIDTH / 2, 50, self.DROPDOWN_WIDTH,
                                 self.SEGMENT_HEIGHT, self.rect, self.get_buttons_for_dropdown(), (0, 200, 255), self.rebuild)
        
        self.buy_button.hide()
        self.update()

    def draw_can_buy(self) -> None:
        selected_paddock = int(self.dropdown.get_selected_text())-1
        paddock_area = PaddockManager().paddocks[selected_paddock].hectares

        # Paddock price = Area * 12000
        price = paddock_area * 12000

        price_lbl = self.product_title_font.render(f"Price: ${price:,}", True, (0, 0, 0))
        self.rendered_surface.blit(price_lbl, (PANEL_WIDTH / 2 - price_lbl.get_width() / 2, self.rect.h - 350))

        if price > SaveManager().money:
            self.buy_button.hide()
            self.rendered_surface.blit(self.not_enough_money_lbl, (PANEL_WIDTH / 2 - self.not_enough_money_lbl.get_width() / 2, self.buy_button.rect.y + 20))
            return
        
        self.buy_button.show()
        self.buy_button.draw()

    def rebuild(self) -> None:
        logging.info("Rebuilding paddock buy menu...")
        self.rendered_surface.fill((255, 255, 255), (0, 0, PANEL_WIDTH, self.rendered_surface.get_height() - 170)) # - 170 for back button below

        self.draw_can_buy()

    def update(self) -> None:
        self.dropdown.update(self.events.mouse_just_pressed, self.events.set_override)
        self.buy_button.update(self.events.mouse_just_pressed, self.events.set_override)

        if self.last_money != SaveManager().money:
            self.last_money = SaveManager().money

            self.rebuild()
        
        self.draw()

    def draw(self) -> None:
        self.parent_surface.blit(self.rendered_surface, self.rect)
        self.dropdown.draw()

class Shop:
    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect) -> None:
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

        self.in_paddock_menu = False

        self.paddock_buy_menu = PaddockBuyMenu(self.parent_surface, self.events, self.rect)

        self.not_enough_money_lbl = self.product_title_font.render("Not enough money!", True, (255, 0, 0))
        self.not_enough_xp_lbl = self.product_title_font.render("Not enough XP!", True, (255, 0, 0))

        self.buy_button = Button(self.rendered_surface, PANEL_WIDTH / 2 - 150, self.rect.h - 280, 300, 100, self.rect, (0, 200, 255),
                                  (0, 200, 255), (255, 255, 255), "Buy", 60, (20, 20, 20, 20), 0, 0, True, lambda: self.buy_selected())
        
        self.buy_button.hide()

        self.back_button = Button(self.rendered_surface, PANEL_WIDTH / 2 - 150, self.rect.h - 160, 300, 100, self.rect, (0, 200, 255),
                                  (0, 200, 255), (255, 255, 255), "Back", 60, (20, 20, 20, 20), 0, 0, True, lambda: self.backtrack_path())

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
            self.path.pop()

        for item in self.path:
            self.current_items = self.current_items[item]

        self.rebuild()

    def update_path(self, new_path_segment: str) -> None:
        self.path.append(new_path_segment)
        self.current_items = self.current_items[new_path_segment]

        self.rebuild()

    def rebuild_buyimg(self) -> None:
        self.rendered_surface.fill((255, 255, 255), (0, 0, PANEL_WIDTH, 200)) # clear any old images

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
            self.rendered_surface.fill((255, 255, 255), (0, self.buy_button.rect.y, PANEL_WIDTH, self.buy_button.rect.h))
            self.rendered_surface.blit(self.not_enough_xp_lbl, (PANEL_WIDTH / 2 - self.not_enough_xp_lbl.get_width() / 2, self.buy_button.rect.y + 20))
            
            self.buy_button.hide()
            self.buy_button.draw()
        
        elif SaveManager().money < money_required:
            self.rendered_surface.fill((255, 255, 255), (0, self.buy_button.rect.y, PANEL_WIDTH, self.buy_button.rect.h))
            self.rendered_surface.blit(self.not_enough_money_lbl, (PANEL_WIDTH / 2 - self.not_enough_money_lbl.get_width() / 2, self.buy_button.rect.y + 20))

            self.buy_button.hide()
            self.buy_button.draw()
        
        else:
            self.buy_button.show()
            self.buy_button.draw()

    def open_paddocks_buy_menu(self) -> None:
        self.in_paddock_menu = True
        
        self.buy_button.hide()
        self.back_button.show()

        self.draw()

    def rebuild_buyscr(self) -> None:
        logging.info("Rebuilding equipment buy menu...")

        self.product_images = []
        self.current_image = 0
        
        for image_path in self.current_items["anims"]:
            if image_path == "default" or self.current_items["anims"][image_path] is None: continue

            new_img = pg.transform.scale_by(ResourceManager.load_image(self.current_items["anims"][image_path], (32, 32)), 4)
            self.product_images.append(new_img)

        self.rebuild_buyimg()

        black = pg.Color(0, 0, 0)

        brand = self.path[-2]
        name = self.path[-1]
        title_lbl = self.product_lbls_font.render(f"{brand} {name}", True, black)

        self.rendered_surface.blit(title_lbl, (PANEL_WIDTH / 2 - title_lbl.get_width() / 2, 220))

        curr_y = 300

        for attr in self.current_items:
            fullcaps = False

            if attr in ("sizePx", "turningPoint", "hitch", "anims", "pipeOffset") or self.current_items[attr] is None: continue
            elif attr == "price":
                # int(<an_integar>):, in an f string formats with commas
                text = self.product_title_font.render(f"Price: ${self.current_items[attr]:,}", True, black)
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

            text = self.product_lbls_font.render(f"{final_attr}: {self.current_items[attr]}{unit}", True, black)
            pos = (PANEL_WIDTH / 8, curr_y)

            self.rendered_surface.blit(text, pos)

            curr_y += text.get_height() + 5

        self.just_rebuilt = True

    def rebuild(self) -> None:
        logging.info("Rebuilding buy menu items...")

        self.rendered_surface.fill((255, 255, 255, 255))
        self.buttons = []

        if len(self.path) == 3: return self.rebuild_buyscr()

        x = 25
        y = 50

        size = (self.rect.w - 25*4)/3 # padding = 25, 3 buttons in each row
        step = size + 25 # padding = 25

        for item in self.current_items:
            self.buttons.append(Button(self.rendered_surface, x, y, size, size, self.rect, (0, 200, 255), (0, 200, 255), (255, 255, 255),
                                       item, 30, (20, 20, 20, 20), 0, 0, True, lambda item=item: self.update_path(item)))
            
            x += step

            if x >= step * 3 + 25 - 5:
                y += step
                x = 25

        if len(self.path) == 0:
            paddocks_btn = Button(self.rendered_surface, x, y, size, size, self.rect, (0, 200, 255), (0, 200, 255),(255, 255, 255),
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