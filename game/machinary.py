import pygame as pg
import logging

from resource_manager import ResourceManager
from vehicle_trailer_simulation import Vehicle, Trailer, Hitch
from destination import Destination
from sellpoints import SellPoint
from utils import utils
from data import *

from time import time
from math import atan2, sqrt, cos, sin, radians, degrees
from copy import deepcopy
from typing import Dict, List, Sequence

class Tractor(Vehicle):
    IS_VEHICLE: bool = True
    PATH_POP_RADIUS: bool = 15
    UNLOAD_INTERVAL: float = 0.5
    UNLOAD_RATE: float = 1

    def __init__(self, game_surface: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any], scale: float, task_tractor: object, equipment_draw: object, get_silo: object) -> None:
        self.surface = game_surface
        self.shed_rect = shed_rect
        self.scale = scale

        self.task_tractor = task_tractor
        self.equipment_draw = equipment_draw
        
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
        self.get_silo = get_silo

        self.active = False
        self.stage = 2
        self.destination = Destination(None)
        self.max_speed = 40
        self.curr_speed = self.max_speed

        self.tool: Tool = None

        self.desired_rotation: float = 0.0
        self.waiting = False
        self.has_waited = False
        self.going_to_gate = False
        self.heading_to_silo = False
        self.heading_to_sell = False

        self.last_unload = time()

        image = pg.transform.scale_by(ResourceManager.load_image(self.anims['normal']), self.scale*VEHICLE_SCALE)
        super().__init__(self.surface, image, (shed_rect.x, shed_rect.y + 10), 0, self.hitch_y)

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def paddock_text(self) -> str:
        if self.paddock == -1: return "--"
        return str(self.paddock + 1).capitalize() # (Currently its the paddock index, not the num)

    @property
    def working(self) -> bool: return self.stage == JOB_TYPES["working"]

    def set_equipment_draw(self, equipment_draw: object) -> None:
        self.equipment_draw = equipment_draw

    def set_string_task(self, text: str) -> None:
        self.string_task = text

        if self.tool is not None:
            self.tool.string_task = text

        self.equipment_draw(rebuild=True)

    def set_job(self, job) -> None:
        """job is of type `pathfinding.Job`"""

        self.job = job

    def set_waiting(self, waiting: bool) -> None:
        was_waiting = self.waiting
        self.waiting = waiting

        if was_waiting and not self.waiting:
            self.has_waited = True

    def unload_tool(self) -> None:
        if time() - self.last_unload < self.UNLOAD_INTERVAL: return

        self.last_unload = time()
        fill_difference = min(self.tool.fill, self.UNLOAD_RATE)
        self.tool.fill -= fill_difference

        if self.destination.destination == self.get_silo():
            self.get_silo().store_crop(self.tool.get_fill_type_str, fill_difference)
        elif self.destination.is_sellpoint:
            self.destination.destination.sell_crop(self.tool.get_fill_type_str, fill_difference)
        else:
            logging.warning(f"Unloading {fill_difference}T of {self.tool.fill_type} into nothing.")

        if self.tool.fill == 0:
            self.tool.set_animation('empty')
            self.tool.reload_vt_sim()

            self.set_waiting(False)
            self.heading_to_silo = False
            self.heading_to_sell = False
            self.stage = JOB_TYPES["travelling_from"]
            self.set_string_task("Driving to shed...")
            self.task_tractor(self, self.tool, Destination(None), self.stage)

    def follow_path(self) -> None:
        if len(self.path) == 0:
            if self.tool.tool_type == "Trailers" and self.destination.is_paddock:
                # Needs to unload
                if self.has_waited:
                    if self.going_to_gate:
                        self.has_waited = False
                        self.going_to_gate = False
                        self.heading_to_silo = True
                        target = Destination(self.get_silo())
                        self.task_tractor(self, self.tool, target, self.stage)
                        self.set_string_task(f"Transporting {round(self.tool.fill, 1)}T of {self.tool.get_fill_type_str} to {self.destination.get_name()}...")
                    else:
                        self.stage = JOB_TYPES["transporting_from"]
                        self.going_to_gate = True
                        self.set_string_task(f"Transporting {round(self.tool.fill, 1)}T of {self.tool.get_fill_type_str} to a silo...")
                else:
                    self.set_waiting(True)
                
                return

            elif self.tool.tool_type == "Trailers" and (self.heading_to_silo or self.heading_to_sell):
                # Needs to unload trailer
                # This will get called over and over again while it is unloading
                if self.heading_to_silo:
                    self.destination = Destination(self.get_silo())
                
                self.set_waiting(True)
                self.unload_tool()
                return

            self.stage += 1

            if self.stage - 1 in END_JOB_STAGES:
                self.active = False
                self.tool.active = False
                self.paddock = -1
                self.tool.paddock = -1

                self.set_string_task("No task assigned")

                logging.debug(f"Vehicle: {self.vehicle_id} has completed their task.")
                return
            else:
                logging.debug(f"Vehicle: {self.vehicle_id} moving on to next path stage ({self.stage})...")

                if self.working:
                    self.set_string_task(f"{TOOL_ACTIVE_NAMES[self.tool.tool_type]}...".capitalize())
                    self.tool.set_working_animation()

                    self.curr_speed = 20
                else:
                    self.curr_speed = 40

                    if self.stage - 1 == JOB_TYPES["working"]:
                        # was just working, sort out paddock now
                        self.destination.destination.reset_paint()
                        self.destination.destination.set_state(self.tool.get_output_state())

                if self.stage == JOB_TYPES["travelling_from"]:
                    # Go to shed
                    self.set_string_task("Travelling to shed...")

                    self.task_tractor(self, self.tool, Destination(None), self.stage)
                else:
                    # TODO: Call update_machine_info with the correct information
                    if self.stage == JOB_TYPES["travelling_to"]:
                        self.set_string_task(f"Travelling to {self.destination.get_name()}...")

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
        
    def set_path(self, job, new_path: List[Sequence[float]], stage: int, paddock: int = -1) -> None:
        if stage == -1:
            # Default to travelling -> working -> etc...
            stage = 2

            self.set_string_task(f"Travelling to {self.destination.get_name()}...")

        logging.info(f"Setting new path for vehicle: {self.vehicle_id}...")
        self.set_job(job)
        self.path = new_path

        # Required for trailers because the tool.path is just a copy of the original path
        # The way back for trailers is just the opporsite of the original path
        self.tool.path = deepcopy(new_path)

        self.active = True
        self.tool.active = True
        self.stage = stage
        self.paddock = paddock
        self.tool.paddock = paddock
        self.waiting = False
    
    def calculate_movement(self, dt: float) -> float:
        if self.waiting:
            self.velocity = [0, 0]
            return 0

        turn_amount = utils.angle_difference(self.rotation, self.desired_rotation)

        self.rotation += max(-MAX_TURN_SPEED, min(MAX_TURN_SPEED, turn_amount)) * dt * 10
        self.rotation %= 360

        direction = [cos(radians(-self.rotation-90)), sin(radians(-self.rotation-90))]

        self.velocity[0] = direction[0] * self.curr_speed
        self.velocity[1] = direction[1] * self.curr_speed

        return sqrt(self.velocity[0]**2 + self.velocity[1]**2)

    def update(self, dt: float) -> None:
        if not self.active: return

        self.follow_path()

        if len(self.path) > 0 and DEBUG_PATHS:
            for point in self.path:
                pg.draw.circle(self.surface, (255, 0, 0), point, 3)

            pg.draw.line(self.surface, (0, 0, 255), self.path[0], self.rect.center)

        required_dt = 1/TARGET_FPS
        remaining_dt = dt
        while remaining_dt > 0:
            if remaining_dt < required_dt: remaining_dt = required_dt

            self.calculate_movement(required_dt)
            self.simulate(required_dt)
            self.tool.simulate(required_dt * 2)

            remaining_dt -= required_dt

        self.tool.update()
        self.draw()

class Header(Vehicle):
    IS_VEHICLE: bool = True
    PATH_POP_RADIUS: bool = 15
    UNLOAD_INTERVAL: float = 0.5
    UNLOAD_RATE: float = 0.5

    def __init__(self, game_surface: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any], scale: float, task_header: object, equipment_draw: object) -> None:
        self.surface = game_surface
        self.shed_rect = shed_rect
        self.scale = scale

        self.task_header = task_header
        self.equipment_draw = equipment_draw
        
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
        self.storage = attrs["storage"]

        self.string_task = "No task assigned"
        self.paddock: int = -1
        self.path: List[Sequence[float, float]] = []

        self.active = False
        self.stage = 2
        self.destination = Destination(None)
        self.max_speed = 40
        self.curr_speed = self.max_speed

        self.last_fill = 0

        self.last_paint_left = (0, 0)
        self.last_paint_right = (0, 0)

        self.desired_rotation: float = 0.0

        image = ResourceManager.load_image(self.anims['pipeIn'])
        super().__init__(self.surface, image, (shed_rect.x, shed_rect.y + 10), 0, 0)

        self.working_width = self.image.get_width()

        self.waiting_for_unloading_vehicle_assign = False
        self.waiting_for_unloading_vehicle = False
        self.unloading_vehicle = None
        self.unloading = False
        self.last_unload = time()
        self.waiting = False

        self.completed_path = []
        self.job = None

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model}"

    @property
    def paddock_text(self) -> str:
        if self.paddock == -1: return "--"
        return str(self.paddock + 1).capitalize() # (Currently its the paddock index, not the num)

    @property
    def get_fill_type_str(self) -> str:
        if self.fill_type == -1: return "--"
        return CROP_TYPES[self.fill_type]

    @property
    def working(self) -> bool: return self.stage == JOB_TYPES["working"]

    def get_output_state(self) -> int:
        return 0

    def set_equipment_draw(self, equipment_draw: object) -> None:
        self.equipment_draw = equipment_draw

    def set_string_task(self, text: str) -> None:
        self.string_task = text
        self.equipment_draw(rebuild=True)

    def set_job(self, job) -> None:
        """job is of type `pathfinding.Job`"""

        self.job = job

    def unload(self) -> None:
        if time() - self.last_unload < self.UNLOAD_INTERVAL: return

        self.last_unload = time()

        fill_difference = min(self.fill, self.UNLOAD_RATE)
        self.fill -= fill_difference
        self.equipment_draw()

        if self.unloading_vehicle is None:
            logging.warning("Header unloading into null vehicle (nothing)!")
        else:
            self.unloading_vehicle.tool.update_fill(self.fill_type, fill_difference)

        if self.fill == 0:
            self.unloading = False
            self.waiting = False
            self.original_image = ResourceManager.load_image(self.anims['pipeIn'])

            self.unloading_vehicle.set_waiting(False)
            self.unloading_vehicle.tool.set_animation('full')
            self.unloading_vehicle.tool.reload_vt_sim()
            self.unloading_vehicle.path = self.job.trace_collision_boundary(self.position, self.destination.destination.gate, self.job.lap_1)

            logging.debug(f"{self.full_name} is now empty. Resuming task...")

    def on_unloading_vehicle_arrive(self) -> None:
        logging.debug(f"{self.full_name} unloading vehicle has arrived. Begginning unloading sequence...")

        self.waiting_for_unloading_vehicle = False
        self.unloading = True

    def on_unloading_vehicle_assign(self, vehicle: Tractor) -> List[Sequence[float]]:
        """Returns a path to the header"""

        logging.debug(f"{self.full_name} unloading vehicle has been assigned. Waiting for it's arrival...")

        self.unloading_vehicle = vehicle
        self.waiting_for_unloading_vehicle_assign = False
        self.waiting_for_unloading_vehicle = True

        return list(reversed(self.job.trace_collision_boundary(self.position, self.destination.destination.gate, self.job.lap_1)))

    def follow_path(self) -> None:
        if self.waiting_for_unloading_vehicle_assign: return

        if self.waiting_for_unloading_vehicle:
            if self.unloading_vehicle.waiting:
                self.on_unloading_vehicle_arrive()
            else:
                return

        if self.unloading:
            self.unload()
            return

        if len(self.path) == 0:
            self.stage += 1

            if self.stage - 1 in END_JOB_STAGES:
                self.active = False
                self.paddock = -1
                self.completed_path = []

                self.set_string_task("No task assigned")

                logging.debug(f"Vehicle: {self.vehicle_id} has completed their task.")
                return

            logging.debug(f"Vehicle: {self.vehicle_id} moving on to next path stage ({self.stage})...")

            if self.working:
                self.set_string_task(f"{TOOL_ACTIVE_NAMES['Headers']}...".capitalize())
                self.curr_speed = 20
            else:
                self.curr_speed = 40

                if self.stage - 1 == JOB_TYPES["working"]:
                    # was just working, sort out paddock now
                    self.destination.destination.reset_paint()
                    self.destination.destination.set_state(self.get_output_state())

            if self.stage == JOB_TYPES["travelling_from"]:
                # Go to shed
                self.set_string_task("Travelling to shed...")

                self.task_header(self, Destination(None), self.stage)
            else:
                # TODO: Call update_machine_info with the correct information
                if self.stage == JOB_TYPES["travelling_to"]:
                    self.set_string_task(f"Travelling to {self.destination.get_name()}...")

                self.task_header(self, self.destination, self.stage)

        px, py = self.path[0]

        multiplier = 1

        # If the vehicle is travelling
        if self.curr_speed == 40:
            multiplier = 2

        dist = sqrt((px - self.rect.centerx) ** 2 + (py - self.rect.centery) ** 2)
        if dist < self.PATH_POP_RADIUS * multiplier:
            self.completed_path.append(self.path[0])
            self.path.pop(0)
            self.follow_path()
            return

        self.desired_rotation = (degrees(atan2(-(py - self.rect.centery), px - self.rect.centerx)) + 360) % 360 - 90
        
    def set_path(self, job, new_path: List[Sequence[float]], stage: int, paddock: int = -1) -> None:
        if stage == -1:
            # Default to travelling -> working -> etc...
            stage = 2
            self.set_string_task(f"Travelling to {self.destination.get_name()}...")

        logging.info(f"Setting new path for vehicle: {self.vehicle_id}...")
        self.set_job(job)
        self.path = new_path
        self.active = True
        self.stage = stage
        self.paddock = paddock
    
    def calculate_movement(self, dt: float) -> float:
        if self.waiting:
            self.velocity = [0, 0]
            return 0

        turn_amount = utils.angle_difference(self.rotation, self.desired_rotation)

        self.rotation += max(-MAX_TURN_SPEED, min(MAX_TURN_SPEED, turn_amount)) * dt * 10
        self.rotation %= 360

        direction = [cos(radians(-self.rotation-90)), sin(radians(-self.rotation-90))]

        self.velocity[0] = direction[0] * self.curr_speed
        self.velocity[1] = direction[1] * self.curr_speed

        return sqrt(self.velocity[0]**2 + self.velocity[1]**2)

    def paint(self) -> int:
        paint_surf = self.image
        return self.destination.destination.paint(paint_surf, self.rect.topleft, STATE_COLORS[self.get_output_state()])

    def check_paint(self) -> None: 
        if self.waiting: return

        half_width = self.image.get_width() / 2
        half_height = self.image.get_height() / 2

        local_center = self.image.get_rect().center
        center = (local_center[0] + self.x, local_center[1] + self.y)

        left_paint = utils.rotate_point_centered(center, (center[0] - half_width, center[1] - half_height), -radians(self.rotation))
        right_paint = utils.rotate_point_centered(center, (center[0] + half_width, center[1] - half_height), -radians(self.rotation))

        pg.draw.circle(pg.display.get_surface(), (255, 0, 0), (PANEL_WIDTH + left_paint[0], left_paint[1]), 3)
        pg.draw.circle(pg.display.get_surface(), (0, 0, 255), (PANEL_WIDTH + right_paint[0], right_paint[1]), 3)

        last_paint_left_dist = sqrt((left_paint[0] - self.last_paint_left[0])**2 + (left_paint[1] - self.last_paint_left[1])**2)
        last_paint_right_dist = sqrt((right_paint[0] - self.last_paint_right[0])**2 + (right_paint[1] - self.last_paint_right[1])**2)

        if last_paint_left_dist >= PAINT_RECT_DIST or last_paint_right_dist >= PAINT_RECT_DIST:
            fill_amount = self.paint()
            self.increment_fill(fill_amount)

            self.last_paint_left = left_paint
            self.last_paint_right = right_paint

    def request_unload(self) -> None:
        logging.info(f"Header {self.full_name} is requesting unload...")
        self.waiting_for_unloading_vehicle_assign = True
        self.waiting = True
        self.original_image = ResourceManager.load_image(self.anims['pipeOut'])

    def increment_fill(self, fill_amount: int) -> None:
        last_fill_amount = self.fill
        self.fill += fill_amount / EQUIPMENT_RATES["Headers"]

        if round(last_fill_amount, 1) < round(self.fill, 1):
            # Equipment menu will need a rebuild as the rounding ticks over
            self.equipment_draw(rebuild=True)

        if self.fill >= self.storage:
            self.request_unload()

    def update(self, dt: float) -> None:
        if not self.active: return

        self.follow_path()

        if len(self.path) > 0 and DEBUG_PATHS:
            for point in self.path:
                pg.draw.circle(self.surface, (255, 0, 0), point, 3)

            pg.draw.line(self.surface, (0, 0, 255), self.path[0], self.rect.center)

        required_dt = 1/TARGET_FPS
        remaining_dt = dt
        while remaining_dt > 0:
            if remaining_dt < required_dt: remaining_dt = required_dt

            if self.working:
                self.check_paint()

            self.calculate_movement(required_dt)

            self.simulate(required_dt)

            remaining_dt -= required_dt

        self.draw()

class Tool(Trailer):
    IS_VEHICLE: bool = False

    def __init__(self, game_surface: pg.Surface, shed_rect: pg.Rect, attrs: Dict[str, any], scale: float) -> None:
        self.surface = game_surface
        self.shed_rect = shed_rect
        self.scale = scale

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

        if self.tool_type in ("Seeders", "Spreaders", "Sprayers", "Trailers"):
            self.storage = attrs["storage"]

        if self.tool_type == "Seeders":
            self.cart = attrs["cart"]

        if self.tool_type == "Trailers":
            self.set_animation("full")
        else:
            self.set_animation(self.anims["default"]) # anims['default'] key returns the name of the key to the default image

        self.working_width = self.master_image.get_width()

        self.string_task = "No task assigned"
        self.paddock: int = -1
        self.path: List[Sequence[float]]

        self.fill = attrs.get("fill", 0)
        self.fill_type = attrs.get("fillType", -1)
        self.last_fill = 0

        self.last_paint_left = (0, 0)
        self.last_paint_right = (0, 0)

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

    @property
    def get_fill_type_str(self) -> str:
        if self.fill_type == -1: return "--"
        return CROP_TYPES[self.fill_type]

    @property
    def working(self) -> bool: return self.vehicle.working

    @property
    def has_fill(self) -> bool: return FILL_TOOLS[self.tool_type]

    def get_vehicle_id(self) -> None:
        if self.vehicle is not None:
            return self.vehicle.vehicle_id

        return -1

    def get_output_state(self) -> None:
        if self.tool_type in ("Spreaders", "Sprayers"):
            return self.destination.destination.state
        
        return TOOL_STATES[self.tool_type][0]

    def set_fill(self, fill_type: int, fill_amount: float) -> Tuple[int, float]:
        """Returns how much crop was stored in it already and the type"""

        crop_name = CROP_TYPES[fill_type]

        logging.debug(f"Filling {self.full_name} with {fill_amount}T of {crop_name}...")

        if self.fill > 0:
            logging.warning(f"While filling {self.full_name} it already has {round(self.fill, 1)} tons of {CROP_TYPES[self.fill_type]} which should be stored back in the silo!")

        fill_pool = self.fill + fill_amount

        self.fill_type = fill_type
        self.fill = min(self.storage, fill_pool)

        original_fill_type = self.fill_type
        original_fill = fill_pool - self.fill

        return original_fill_type, original_fill

    def update_fill(self, fill_type: int, fill_amount: float) -> Tuple[int, float]:
        """
        Returns how much crop was stored in it already and the type
        (Is a wrapper to set_fill except adds the fill already in the tool)
        """

        if self.fill_type != fill_type and self.fill > 0:
            logging.warning(f"Trailer already has fill of a different fill type! Updating this is adding crop that doesn't exist of the new type. (Old: {self.get_fill_type_str})")

        return self.set_fill(fill_type, self.fill + fill_amount)

    def reload_vt_sim(self) -> None:
        logging.debug(f"Reloading vehicle_trailer_simulation for tool {self.full_name}...")
        super().__init__(self.surface, self.vehicle, self.master_image, (self.shed_rect.x, self.shed_rect.y + 10), 0, -self.master_image.get_height() / 2 + 9)

    def set_animation(self, anim_name: str) -> None:
        anim = self.anims.get(anim_name, self.anims['default'])
        self.master_image = pg.transform.scale_by(ResourceManager.load_image(anim), self.scale*TOOL_SCALE)

    def set_working_animation(self, reload_vt: bool = True) -> None:
        logging.info(f"Setting working animation for tool: {self.full_name}...")

        if "on" in self.anims: self.set_animation("on")
        elif "unfolded" in self.anims: self.set_animation("unfolded")

        if reload_vt: self.reload_vt_sim()

    def assign_vehicle(self, vehicle: Tractor | Header) -> None:
        super().__init__(self.surface, vehicle, self.master_image, (self.shed_rect.x, self.shed_rect.y + 10), 0, -self.master_image.get_height() / 2 + 9)

        self.set_working_animation(reload_vt=False)
        self.working_width = self.master_image.get_width()

        if self.tool_type == "Trailer":
            self.set_animation("full")
        else:
            self.set_animation(self.anims["default"]) # anims['default'] key returns the name of the key to the default image

    def request_fill(self) -> None:
        logging.info(f"Tool {self.full_name} is requesting fill...")

        logging.error("Error when requesting fill! Unimplemented!")

    def paint(self) -> int:
        paint_surf = pg.transform.rotate(self.master_image, self.rotation)
        return self.destination.destination.paint(paint_surf, self.position, STATE_COLORS[self.get_output_state()])

    def check_paint(self) -> None: 
        half_width = self.master_image.get_width() / 2
        half_height = self.master_image.get_height() / 2

        local_center = self.master_image.get_rect().center
        center = (local_center[0] + self.x, local_center[1] + self.y)

        left_paint = utils.rotate_point_centered(center, (center[0] - half_width, center[1] + half_height), -radians(self.rotation))
        right_paint = utils.rotate_point_centered(center, (center[0] + half_width, center[1] + half_height), -radians(self.rotation))

        pg.draw.circle(pg.display.get_surface(), (255, 0, 0), (PANEL_WIDTH + left_paint[0], left_paint[1]), 3)
        pg.draw.circle(pg.display.get_surface(), (0, 0, 255), (PANEL_WIDTH + right_paint[0], right_paint[1]), 3)

        last_paint_left_dist = sqrt((left_paint[0] - self.last_paint_left[0])**2 + (left_paint[1] - self.last_paint_left[1])**2)
        last_paint_right_dist = sqrt((right_paint[0] - self.last_paint_right[0])**2 + (right_paint[1] - self.last_paint_right[1])**2)

        if last_paint_left_dist >= PAINT_RECT_DIST or last_paint_right_dist >= PAINT_RECT_DIST:
            fill_amount = self.paint()

            if self.has_fill:
                self.decrement_fill(fill_amount)

            self.last_paint_left = left_paint
            self.last_paint_right = right_paint

    def decrement_fill(self, fill_amount: int) -> None:
        last_fill_amount = self.fill
        self.fill -= fill_amount / EQUIPMENT_RATES[self.tool_type] # Tons to kilos

        if round(last_fill_amount, 1) > round(self.fill, 1):
            # Equipment menu will need a rebuild as the rounding ticks over
            self.vehicle.equipment_draw(rebuild=True)

        if self.fill <= 0:
            self.request_fill()

    def update(self) -> None:
        if self.active:
            if self.working:
                if self.tool_type in PAINT_TOOLS:
                    self.check_paint()

            self.draw()