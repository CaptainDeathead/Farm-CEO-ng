import pygame as pg
import logging

from resource_manager import ResourceManager
from utils import LayableRenderObj, utils
from data import PANEL_WIDTH

from typing import Dict, Sequence

class SellPoint(LayableRenderObj):
    def __init__(self, game_surface: pg.Surface, raw_position: Sequence[int], pos: Sequence[int], rotation: float, map_scale: float, name: str, silo: bool,
                 contents: Dict[str, float], prices: Dict[str, float]) -> None:

        self.game_surface = game_surface
        self.raw_position = raw_position # Position without scaling and moving (raw from savefile)

        self.pos = pos
        self.rotation = rotation

        self.grid_surface = pg.transform.scale_by(ResourceManager.load_image("Sprites/grid.png"), map_scale)
        self.silo_surface = pg.transform.scale_by(ResourceManager.load_image("Sprites/silo.png"), map_scale)
        
        grid_rect = self.grid_surface.get_rect()
        silo_rect = self.silo_surface.get_rect()

        offset_x = silo_rect.width / 2
        offset_y = silo_rect.height / 2

        grid_x = self.pos[0] - offset_x
        grid_y = self.pos[1] - offset_y

        # TODO: THIS IS DISABLED AT THE MOMENT BECAUSE OF ROTATION ISSUES
        #silo_x = self.pos[0] + offset_x
        #silo_y = self.pos[1] + offset_y
        silo_x = self.pos[0]
        silo_y = self.pos[1]

        self.grid_rect = pg.Rect(grid_x, grid_y, grid_rect.w, grid_rect.h)
        self.silo_rect = pg.Rect(silo_x, silo_y, silo_rect.w, silo_rect.h)

        self.name = name
        self.silo = silo
        self.contents = contents
        self.prices = prices
        self.pending_money = 0.0

        self.lbl = pg.font.SysFont(None, int(20 * map_scale)).render(self.name, True, (255, 255, 255))

    def draw_grid(self) -> None:
        # TODO: THIS IS DISABLED AT THE MOMENT BECAUSE OF ROTATION ISSUES
        return
        self.game_surface.blit(self.grid_surface, self.grid_rect)

    def draw_silo(self) -> None:
        #self.game_surface.blit(self.silo_surface, self.silo_rect)
        utils.blit_centered(self.game_surface, self.silo_surface, self.silo_rect.topleft, self.silo_surface.get_rect().center, self.rotation)
        self.game_surface.blit(self.lbl, (self.pos[0] - self.lbl.get_width() // 2, self.pos[1] - self.lbl.get_height() * 2))

    def store_crop(self, crop_type: str, amount: float) -> None:
        """amount should be in tons"""

        if not self.silo:
            raise Exception("Cannot store crops in a non-silo sellpoint!")

        logging.info(f"Filling silo with {amount}T of {crop_type}...")

        self.contents[crop_type] += amount

    def take_crop(self, crop_type: str, desired_amount: float) -> float:
        """desired_amount should be in tons"""

        if not self.silo:
            raise Exception("Cannot take crops from a non-silo sellpoint")

        logging.info(f"Unloading silo of {desired_amount}T of {crop_type}...")

        amount = min(self.contents[crop_type], desired_amount)
        self.contents[crop_type] -= amount

        return amount

    def sell_crop(self, crop_type: str, desired_amount: float) -> None:
        """desired_amount should be in tons"""

        if self.silo:
            raise Exception("Cannot sell crops to a silo!")

        self.pending_money += self.prices[crop_type] * desired_amount
        self.prices[crop_type] -= (desired_amount / 1)

    def update(self, mouse_pos: tuple[int, int]) -> bool:
        if self.silo_rect.collidepoint(mouse_pos[0] + self.silo_rect.w / 2, mouse_pos[1] + self.silo_rect.h / 2):
            return True

        return False