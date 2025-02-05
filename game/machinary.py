import pygame as pg
import logging

from resource_manager import ResourceManager
from vehicle_trailer_simulation import Vehicle, Trailer, Hitch
from destination import Destination
from utils import utils
from data import *

from math import atan2, sqrt, cos, sin, radians, degrees
from typing import Dict, List, Sequence

class Tractor(Vehicle):
    IS_VEHICLE: bool = True
    PATH_POP_RADIUS: bool = 15

    def __init__(self, game_surface: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any], task_tractor: object) -> None:
        self.surface = game_surface
        self.shed_rect = shed_rect
        self.task_tractor = task_tractor
        
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
        self.stage = 2
        self.destination = Destination(None)
        self.max_speed = 40
        self.curr_speed = self.max_speed

        self.tool: Tool = None

        self.desired_rotation: float = 0.0

        image = ResourceManager.load_image(self.anims['normal'])
        super().__init__(self.surface, image, (shed_rect.x, shed_rect.y + 10), 0, self.hitch_y)

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def paddock_text(self) -> str:
        if self.paddock == -1: return "--"
        return str(self.paddock + 1).capitalize() # (Currently its the paddock index, not the num)

    def follow_path(self) -> None:
        if len(self.path) == 0:
            self.stage += 1

            if self.stage - 1 in END_JOB_STAGES:
                self.active = False
                logging.debug(f"Vehicle: {self.vehicle_id} has completed their task.")
                return
            else:
                logging.debug(f"Vehicle: {self.vehicle_id} moving on to next path stage ({self.stage})...")

                if self.stage == JOB_TYPES["working"]:
                    self.curr_speed = 20
                else:
                    self.curr_speed = 40

                if self.stage == JOB_TYPES["travelling_from"]:
                    # Go to shed
                    self.task_tractor(self, self.tool, Destination(None), self.stage)
                else:
                    self.task_tractor(self, self.tool, self.destination, self.stage)

        px, py = self.path[0]

        multiplier = 1

        # If the vehicle is travelling
        if self.curr_speed == 40:
            multiplier = 2

        dist = sqrt((px - self.rect.centerx) ** 2 + (py - self.rect.centery) ** 2)
        if dist < self.PATH_POP_RADIUS * multiplier:
            self.path.pop(0)
            self.follow_path()
            return

        self.desired_rotation = (degrees(atan2(-(py - self.rect.centery), px - self.rect.centerx)) + 360) % 360 - 90
        
    def set_path(self, new_path: List[Sequence[float]], stage: int) -> None:
        if stage == -1:
            # Default to travelling -> working -> etc...
            stage = 2

        logging.info(f"Setting new path for vehicle: {self.vehicle_id}...")
        self.path = new_path
        self.active = True
        self.tool.active = True
        self.stage = stage
    
    def calculate_movement(self, dt: float) -> None:
        turn_amount = utils.angle_difference(self.rotation, self.desired_rotation)

        self.rotation += max(-MAX_TURN_SPEED, min(MAX_TURN_SPEED, turn_amount)) * dt * 10
        self.rotation %= 360

        direction = [cos(radians(-self.rotation-90)), sin(radians(-self.rotation-90))]

        self.velocity[0] = direction[0] * self.curr_speed
        self.velocity[1] = direction[1] * self.curr_speed

    def update(self, dt: float) -> None:
        if self.active:
            self.follow_path()
            self.calculate_movement(dt)

            if len(self.path) > 0:
                for point in self.path:
                    pg.draw.circle(self.surface, (255, 0, 0), point, 3)

                pg.draw.line(self.surface, (0, 0, 255), self.path[0], self.rect.center)

            self.tool.update(dt)
            self.draw(dt)

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
        self.size = attrs["size"]

        self.string_task = "No task assigned"
        self.paddock: int = -1
        self.path: List[Sequence[float, float]] = []

        self.active = False
        self.destination = Destination(None)

        self.desired_rotation: float = 0.0

        image = ResourceManager.load_image(self.anims['pipeIn'])
        super().__init__(self.surface, image, (shed_rect.x, shed_rect.y + 10), 0, 0)

        self.working_width = self.image.get_width()

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def paddock_text(self) -> str:
        if self.paddock == -1: return "--"
        return str(self.paddock + 1).capitalize() # (Currently its the paddock index, not the num)

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

        self.working_width = self.master_image.get_width()

        self.string_task = "No task assigned"
        self.paddock: int = -1
        self.path: List[Sequence[float]]

        self.fill = 0
        self.fill_type = -1

        self.active = False
        self.destination = Destination(None)

        self.vehicle: Tractor | Header = None

        self.desired_rotation: float = 0.0

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def paddock_text(self) -> str:
        if self.paddock == -1: return "--"
        return str(self.paddock + 1).capitalize() # (Currently its the paddock index, not the num)

    def get_vehicle_id(self) -> None:
        if self.vehicle is not None:
            return self.vehicle.vehicle_id

        return -1

    def set_animation(self, anim_name: str) -> None:
        self.master_image = pg.transform.scale2x(ResourceManager.load_image(self.anims[anim_name]))

    def assign_vehicle(self, vehicle: Tractor | Header) -> None:
        super().__init__(self.surface, vehicle, self.master_image, (self.shed_rect.x, self.shed_rect.y + 10), 0, -self.master_image.get_height() / 2 + 5)

    def update(self, dt: float) -> None:
        if self.active:
            self.draw(dt * 16)