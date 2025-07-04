import pygame as pg
import logging

from UI.pygame_gui import Button
from resource_manager import ResourceManager
from events import Events
from data import *
from utils import utils

class Guide:
    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect, scale: int) -> None:
        self.parent_surface = parent_surface
        self.events = events
        self.rect = rect
        self.scale = scale

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        self.rendered_surface.fill(UI_BACKGROUND_COLOR)

        self.page_1 = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        self.page_2 = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.active = False
        self.page = 0

        self.page_toggle_button = Button(self.rendered_surface, self.rect.w / 2 - 250 / 2, self.rect.h - 125, 250, 75, pg.Rect(0, NAVBAR_HEIGHT, 0, 0), UI_MAIN_COLOR, UI_ACTIVE_COLOR, UI_TEXT_COLOR, "Switch page", 40, (20, 20, 20, 20), 0, 0, True, self.switch_page)

        guide = {
            "title": "Farming Basics",
            "text": [
                "- Paddocks have different stages: Harvested, Cultivated, Sown and Ready To Harvest.",
                "- A paddock must first be cultivated with a cultivator, then sown with a seeder.",
                "- Paddocks must be harvested with a header.",
                "- When a header is full or tool is empty, use a trailer to unload / load it.",
                "- The cycle then repeats.",
                "- Pressing the shed advances all growth stages by sleeping."
            ],
            "title1": "Fertilisers and Chemicals",
            "text1": [
                "<LIME>      - Lime can be optionally spreaded every 3 years to boost a paddocks yield. Lime can be applied during the harvested and cultivated stages.",
                "<SUPER>      - Super can be spreaded on paddocks in their first or second growth stages.",
                "<UREA>      - Urea is very similar to Super, however it provides an additional yield bonus. Both Urea and Super require a spreader.",
                "<WEEDS>      - Weeds can affect paddocks. Weeds have 2 different strengths. Heavier weeds come up in later growth stages. Weeds have a SEVERE yield impact. Sprayers are used to remove weeds"
            ],
            "page": "bluh",
            "title2": "Selling Crops",
            "text2": [
                "- The grain menu allows you to see all stored crops and their prices. Market prices are reduced after selling crops.",
                "- Less valuable crops usually have a higher yield.",
                "- To sell crops, use a trailer and select the sellpoint you want to sell at."
            ]
        }

        lime_img = pg.transform.smoothscale_by(ResourceManager.load_image("Icons/FillTypes/lime.png"), 0.75)
        super_img = pg.transform.smoothscale_by(ResourceManager.load_image("Icons/FillTypes/super.png"), 0.75)
        urea_img = pg.transform.smoothscale_by(ResourceManager.load_image("Icons/FillTypes/urea.png"), 0.75)
        herbicide_img = pg.transform.smoothscale_by(ResourceManager.load_image("Icons/FillTypes/weeds.png"), 0.75)

        title_font = pg.font.SysFont(None, 50 * self.scale)
        text_font = pg.font.SysFont(None, 35 * self.scale)

        title_font.align = pg.FONT_CENTER
        text_font.align = pg.FONT_LEFT

        curr_y = 20
        target_surf = self.page_1
        for texttype in guide:
            if "page" in texttype:
                target_surf = self.page_2
                curr_y = 20

            elif "title" in texttype:
                title = title_font.render(guide[texttype], True, UI_TEXT_COLOR)
                target_surf.blit(title, (self.rendered_surface.width / 2 - title.width / 2, curr_y))
                curr_y += title.height + 10

            elif "text" in texttype:
                for text in guide[texttype]:
                    literal_text = text.replace("<LIME>", "").replace("<SUPER>", "").replace("<UREA>", "").replace("<WEEDS>", "")

                    if "<LIME>" in text:
                        utils.blit_centered(target_surf, lime_img, (25, curr_y + 5), lime_img.get_rect().center, 0.0)
                    elif "<SUPER>" in text:
                        utils.blit_centered(target_surf, super_img, (25, curr_y + 5), super_img.get_rect().center, 0.0)
                    elif "<UREA>" in text:
                        utils.blit_centered(target_surf, urea_img, (25, curr_y + 5), urea_img.get_rect().center, 0.0)
                    elif "<HERBICIDE>" in text:
                        utils.blit_centered(target_surf, herbicide_img, (25, curr_y + 5), herbicide_img.get_rect().center, 0.0)

                    text_lbl = text_font.render(literal_text, True, UI_TEXT_COLOR, wraplength=PANEL_WIDTH - 20)
                    target_surf.blit(text_lbl, (10, curr_y))
                    curr_y += text_lbl.height + 10

    def switch_page(self) -> None:
        self.page = (self.page + 1) % 2

    def draw(self) -> None:
        self.rendered_surface.fill(UI_BACKGROUND_COLOR)

        if self.page == 0:
            self.rendered_surface.blit(self.page_1, (0, 0))
        else:
            self.rendered_surface.blit(self.page_2, (0, 0))

        self.page_toggle_button.draw()
        self.parent_surface.blit(self.rendered_surface, (0, NAVBAR_HEIGHT))

    def update(self) -> bool:
        pressed = self.page_toggle_button.update(self.events.mouse_just_pressed, self.events.set_override)

        if (self.events.mouse_just_pressed and self.page_toggle_button.global_rect.collidepoint(pg.mouse.get_pos())) or pressed:
            return True

        return False