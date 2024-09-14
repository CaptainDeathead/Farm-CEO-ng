import pygame as pg

from resource_manager import ResourceManager
from vehicle_trailer_simulation import Vehicle, Trailer, Hitch

from math import atan2

from typing import Dict, List, Sequence

class Tractor(Vehicle):
    def __init__(self, map_overlay_surface: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any], brand: str, model: str) -> None:
        self.surface = map_overlay_surface
        self.shed_rect = shed_rect

        self.brand = brand
        self.model = model
        
        self.attrs = attrs
        self.hp = attrs["hp"]
        self.anims = attrs["anims"]
        self.price = attrs["price"]
        self.default_fuel = attrs["fuel"]
        self.fuel = self.default_fuel

        self.string_task = "No task assigned"
        self.paddock: int = -1
        self.path: List[Sequence[float, float]] = []

        self.active = False
        self.tool: Tool = None

        self.desired_rotation: float = 0.0

        image = ResourceManager.load_image(self.anims['normal'])
        super().__init__(self.surface, image, 0, 0)

    def follow_path(self) -> None:
        px, py = self.path[0]

        self.desired_rotation = atan2(py, px)
        rotate_difference = self.rotation - self.desired_rotation
        
        if rotate_difference < self.rotation:
            self.desired_rotation -= rotate_difference
        else:
            self.desired_rotation += rotate_difference

        self.desired_rotation %= 360
        self.path.pop(0)

    def update(self) -> None:
        if self.active:
            self.follow_path()
            self.tool.update()

            self.draw()

class Tool(Trailer):
    ...