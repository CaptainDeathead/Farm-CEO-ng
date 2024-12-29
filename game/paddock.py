import pygame as pg

from random import randint
from typing import Dict, List, Tuple

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