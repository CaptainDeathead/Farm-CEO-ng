import pygame as pg

from resource_manager import ResourceManager
from utils import LayableRenderObj, utils

from typing import Dict, Sequence

class SellPoint(LayableRenderObj):
    def __init__(self, game_surface: pg.Surface, pos: Sequence[int], rotation: float, map_scale: float, name: str, silo: bool,
                 contents: Dict[str, float], prices: Dict[str, float]) -> None:

        self.game_surface = game_surface

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

        if not silo:
            self.prices = self.contents.get("prices", None)

    def draw_grid(self) -> None:
        # TODO: THIS IS DISABLED AT THE MOMENT BECAUSE OF ROTATION ISSUES
        return
        self.game_surface.blit(self.grid_surface, self.grid_rect)

    def draw_silo(self) -> None:
        #self.game_surface.blit(self.silo_surface, self.silo_rect)
        utils.blit_centered(self.game_surface, self.silo_surface, self.silo_rect.topleft, self.silo_surface.get_rect().center, self.rotation)