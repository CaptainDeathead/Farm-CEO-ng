import pygame as pg

from random import randint
from typing import Dict, List, Tuple
from data import PANEL_WIDTH, STATE_COLORS

class Paddock:
    def __init__(self, attrs: Dict[int, any], num: str, scale: float, map_paddocks_surf: pg.Surface) -> None:
        self.attrs = attrs
        self.num = num
        self.scale = scale
        self.map_paddocks_surf = map_paddocks_surf
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
        self.is_painting: bool = False

        self.state_changed = False
        self.last_collision_count = 0

    def init_collision(self) -> None:
        self.surface, self.rect = self.create_surface()
        self.localised_boundary = self.localise_boundary()

        # Fill the paddock red so the mask can see the red pixels
        self.fill(pg.Color(255, 0, 0))
        self.mask = pg.mask.from_surface(self.surface)

        self.paint_surface = pg.Surface(self.rect.size, pg.SRCALPHA)
        self.paint_mask = pg.mask.from_surface(self.paint_surface)

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

        buffer = 2 # Just a bit more room in case calculation isnt the most accurate

        width, height = max_x - min_x + buffer, max_y - min_y + buffer
        surface = pg.Surface((width, height), pg.SRCALPHA)
        rect = pg.Rect(min_x, min_y, width, height)

        return surface, rect

    def localise_boundary(self) -> list[tuple]:
        return [(coord[0] - self.rect.x, coord[1] - self.rect.y) for coord in self.boundary]

    def draw_to_map(self, draw_normal_surface: bool = True, draw_paint_surface: bool = False) -> None:
        if draw_normal_surface:
            self.map_paddocks_surf.blit(self.surface, self.rect)

        if draw_paint_surface:
            self.map_paddocks_surf.blit(self.paint_surface, self.rect)

    def fill(self, color: pg.Color) -> None:
        pg.draw.polygon(self.surface, color, self.localised_boundary)
        self.draw_to_map()

    def load_state(self) -> None:
        self.fill(STATE_COLORS[self.state])

    def set_state(self, state: int) -> None:
        self.state = state
        self.load_state()
        self.state_changed = True

    def reset_paint(self) -> None:
        # Note: this only changes the variable is_painting! to reset the paint on the surface you need to fill this paddock after calling this func
        self.paint_surface = pg.Surface(self.rect.size, pg.SRCALPHA)
        self.paint_mask = pg.mask.from_surface(self.paint_surface)

        self.last_collision_count = 0
        self.is_painting = False

    def paint(self, surface: pg.Surface, pos: Tuple[int, int], color: pg.Color) -> int:
        local_pos = (pos[0] - self.rect.x, pos[1] - self.rect.y)
        surface_mask = pg.mask.from_surface(surface)

        collision_mask = self.mask.overlap_mask(surface_mask, local_pos)
        self.paint_surface.blit(collision_mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0)), (0, 0))

        old_count = self.paint_mask.count()
        self.paint_mask = pg.mask.from_surface(self.paint_surface)
        new_count = self.paint_mask.count() - old_count

        self.draw_to_map(draw_normal_surface=False, draw_paint_surface=True)
        self.is_painting = True

        return new_count

    def paint_rect(self, rect: pg.Rect, color: pg.Color) -> None:
        rect_surface = pg.Surface((rect.w, rect.h))
        rect_surface.fill((255, 255, 255))

        self.paint(rect_surface, (rect.x, rect.y), color)

    def update(self, mouse_pos: tuple[int, int]) -> bool:
        # Need to check if it lies in the mask rect first or an error will occur
        if not self.rect.collidepoint((mouse_pos[0] - PANEL_WIDTH, mouse_pos[1])): return False

        mouse_pos_rel = (mouse_pos[0] - self.rect.x - PANEL_WIDTH, mouse_pos[1] - self.rect.y)
        if self.mask.get_at(mouse_pos_rel): return True

        return False