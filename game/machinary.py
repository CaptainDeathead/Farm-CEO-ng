import pygame as pg
import logging

from resource_manager import ResourceManager
from vehicle_trailer_simulation import Vehicle, Trailer, Hitch

from math import atan2

from typing import Dict, List, Sequence

class Tractor(Vehicle):
    IS_VEHICLE: bool = True

    def __init__(self, game_surface: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any]) -> None:
        self.surface = game_surface
        self.shed_rect = shed_rect
        
        self.attrs = attrs
        self.brand = attrs["brand"]
        self.model = attrs["model"]
        self.hp = attrs["hp"]
        self.anims = attrs["anims"]
        self.price = attrs["price"]
        self.default_fuel = attrs["fuel"]
        self.fuel = self.default_fuel
        self.max_fuel = attrs["max_fuel"]
        self.fill = attrs["fill"]
        self.fill_type = attrs["fillType"]
        self.vehicle_id = attrs["vehicleId"]
        self.job_id = attrs["jobId"]
        self.completion_amount = attrs["completionAmount"]
        self.working_backwards = attrs["workingBackwards"]
        self.hitch_y = attrs["hitch"]

        self.string_task = "No task assigned"
        self.paddock: int = -1
        self.path: List[Sequence[float]] = []

        self.active = False
        self.tool: Tool = None

        self.desired_rotation: float = 0.0

        image = ResourceManager.load_image(self.anims['normal'])
        super().__init__(self.surface, image, (shed_rect.x, shed_rect.y + 10), 0, self.hitch_y)

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

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

    def set_path(self, new_path: List[Sequence[float]]) -> None:
        logging.info(f"Setting new path for vehicle: {self.vehicle_id}.")
        self.path = new_path

    def update(self) -> None:
        if self.active:
            self.follow_path()
            self.tool.update()

            self.draw()

class Header(Vehicle):
    IS_VEHICLE: bool = True

    def __init__(self, game_surface: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any]) -> None:
        self.surface = game_surface
        self.shed_rect = shed_rect
        
        self.attrs = attrs
        self.brand = attrs["brand"]
        self.model = attrs["model"]
        self.hp = attrs["hp"]
        self.anims = attrs["anims"]
        self.price = attrs["price"]
        self.default_fuel = attrs["fuel"]
        self.fuel = self.default_fuel
        self.max_fuel = attrs["max_fuel"]
        self.fill = attrs["fill"]
        self.fill_type = attrs["fillType"]
        self.vehicle_id = attrs["vehicleId"]
        self.job_id = attrs["jobId"]
        self.completion_amount = attrs["completionAmount"]
        self.working_backwards = attrs["workingBackwards"]

        self.string_task = "No task assigned"
        self.paddock: int = -1
        self.path: List[Sequence[float, float]] = []

        self.active = False
        self.desired_rotation: float = 0.0

        image = ResourceManager.load_image(self.anims['pipeIn'])
        super().__init__(self.surface, image, (shed_rect.x, shed_rect.y + 10), 0, 0)

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

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
            self.draw()

class Tool(Trailer):
    IS_VEHICLE: bool = False

    def __init__(self, game_surface: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any]) -> None:
        self.surface = game_surface
        self.shed_rect = shed_rect

        self.attrs = attrs
        self.brand = attrs["brand"]
        self.model = attrs["model"]
        self.tool_type = attrs["toolType"]
        self.size = attrs["size"]
        self.size_px = attrs["sizePx"]
        self.hp = attrs["hp"]
        self.turning_point = attrs["turningPoint"]
        self.hitch_y = attrs["hitch"]
        self.anims = attrs["anims"]
        self.price = attrs["price"]
        self.tool_id = attrs["toolId"]

        if self.tool_type in ("Seeder", "Spreader", "Sprayer", "Trailer"):
            self.storage = attrs["storage"]

        if self.tool_type == "Seeder":
            self.cart = attrs["cart"]

        if self.tool_type == "Trailer":
            self.set_animation("full")
        else:
            self.set_animation(self.anims["default"]) # anims['default'] key returns the name of the key to the default image

        self.string_task = "No task assigned"
        self.paddock: int = -1
        self.path: List[Sequence[float]]

        self.fill = 0
        self.fill_type = -1

        self.active = False
        self.vehicle: Tractor | Header = None

        self.desired_rotation: float = 0.0

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

    def get_vehicle_id(self) -> None:
        if self.vehicle is not None:
            return self.vehicle.vehicle_id

        return -1

    def set_animation(self, anim_name: str) -> None:
        self.master_image = ResourceManager.load_image(self.anims[anim_name])

    def assign_vehicle(self, vehicle: Tractor | Header) -> None:
        self.vehicle_unloaded = vehicle
        super().__init__(self.surface, self.vehicle_unloaded, self.master_image, (self.shed_rect.x, self.shed_rect.y + 10), 0, self.hitch_y)

    def update(self) -> None:
        if self.active:
            ...