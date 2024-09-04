import pygame as pg

from resource_manager import ResourceManager
from vehicle_trailer_simulation import Vehicle, Trailer, Hitch

from typing import Dict

class Tractor(Vehicle):
    def __init__(self, screen: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any], brand: str, model: str) -> None:
        self.screen = screen
        self.shed_rect = shed_rect
        
        self.attrs = attrs
        self.hp = attrs["hp"]
        self.anims = attrs["anims"]
        self.price = attrs["price"]
        self.default_fuel = attrs["fuel"]
        self.fuel = self.default_fuel

        self.string_task = "No task assigned"
        self.paddock: int = None

        image = ResourceManager.load_image(self.anims['normal'])
        super().__init__(screen, image, 0, 0)

class Tool(Trailer):
    ...