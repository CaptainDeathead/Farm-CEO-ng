import pygame as pg

from resource_manager import ResourceManager
from utils import LayableRenderObj

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

        silo_x = self.pos[0] + offset_x
        silo_y = self.pos[1] + offset_y

        self.grid_rect = pg.Rect(grid_x, grid_y, grid_rect.w, grid_rect.h)
        self.silo_rect = pg.Rect(silo_x, silo_y, silo_rect.w, silo_rect.h)

        self.name = name
        self.silo = silo
        self.contents = contents
        self.prices = prices

        if not silo:
            self.prices = self.contents.get("prices", None)
