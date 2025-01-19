import pygame as pg

from random import randint
from typing import Dict, List, Tuple
from data import PANEL_WIDTH

class Paddock:
    def __init__(self, attrs: Dict[int, any], num: int, scale: float) -> None:
        self.attrs = attrs
        self.num = num
        self.scale = scale
        self.state: int = attrs.get("state", randint(0, 5))
        self.owned_by: str = attrs["owned_by"]
        self.hectares: int = attrs["hectares"]

        color = (255, 255, 255)
        if self.owned_by == "player": color = (0, 0, 255)

        self.number_surface = pg.font.SysFont(None, 80).render(str(self.num), True, color)

        cx, cy = attrs["center"]
        gx, gy = attrs["gate"]

        self.center = (int(cx * scale), int(cy * scale))
        self.gate = (int(gx * scale), int(gy * scale))

        self.boundary: List[Tuple] = attrs.get("boundary", [])

    def init_collision(self) -> None:
        self.surface, self.rect = self.create_surface()
        self.localised_boundary = self.localise_boundary()

        # Fill the paddock red so the mask can see the red pixels
        self.fill(pg.Color(255, 0, 0))
        self.mask = pg.mask.from_surface(self.surface)

    def __dict__(self) -> Dict[str, any]:
        return {
            "center": self.attrs["center"],
            "gate": self.attrs["gate"],
            "state": self.state,
            "hectares": self.hectares,
            "owned_by": self.owned_by
        }
    
    def rebuild_num(self) -> None:
        color = (255, 255, 255)
        if self.owned_by == "player": color = (0, 0, 255)
        
        self.number_surface = pg.font.SysFont(None, 80).render(str(self.num), True, color)
    
    def set_boundary(self, boundary: List[Tuple]) -> None:
        self.boundary = boundary

    def create_surface(self) -> tuple[pg.Surface, pg.Rect]:
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = 0, 0

        for coord in self.boundary:
            if coord[0] < min_x: min_x = coord[0]
            if coord[0] > max_x: max_x = coord[0]

            if coord[1] < min_y: min_y = coord[1]
            if coord[1] > max_y: max_y = coord[1]

        width, height = max_x - min_x, max_y - min_y
        surface = pg.Surface((width, height), pg.SRCALPHA)
        rect = pg.Rect(min_x, min_y, width, height)

        return surface, rect

    def localise_boundary(self) -> list[tuple]:
        return [(coord[0] - self.rect.x, coord[1] - self.rect.y) for coord in self.boundary]

    def fill(self, color: pg.Color) -> None:
        pg.draw.polygon(self.surface, color, self.localised_boundary)

    def update(self, mouse_pos: tuple[int, int]) -> bool:
        # Need to check if it lies in the mask rect first or an error will occur
        if not self.rect.collidepoint((mouse_pos[0] - PANEL_WIDTH, mouse_pos[1])): return False

        mouse_pos_rel = (mouse_pos[0] - self.rect.x - PANEL_WIDTH, mouse_pos[1] - self.rect.y)
        if self.mask.get_at(mouse_pos_rel): return True

        return False