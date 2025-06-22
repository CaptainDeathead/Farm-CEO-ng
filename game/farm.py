import pygame as pg
import logging

from resource_manager import ResourceManager
from save_manager import SaveManager

from machinary import Tractor, Header, Tool
from pathfinding import TaskManager
from events import Events
from destination import Destination
from sellpoints import SellPoint
from utils import utils, LayableRenderObj
from data import *

from copy import deepcopy
from typing import List, Dict, Sequence

class Shed(LayableRenderObj):
    def __init__(self, game_surface: pg.Surface, events: Events, rect: pg.Rect, rotation: float, roads: List[Sequence[int]], scale: List[Sequence[int]], silo: SellPoint | None, request_sleep: object) -> None:
        self.game_surface = game_surface
        self.events = events

        self.rect = rect
        self.global_rect = pg.Rect(self.rect.x + PANEL_WIDTH - self.rect.w / 2, self.rect.y - self.rect.h / 2, self.rect.w, self.rect.h)
        self.scale = scale

        self.rotation = rotation
        self.color = pg.Color(175, 195, 255)
        self.pad_color = pg.Color(213, 207, 207)
        self.surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.vehicles: List[Tractor | Header] = []
        self.tools: List[Tool] = []

        if silo is None:
            logging.warning(f"Received silo is None! Should be {SellPoint} type. This will should be set later by the set_silo function.")

        self._silo = silo
        self.request_sleep = request_sleep

        self.roads = roads
        self.scale_roads()

        self.equipment_draw = lambda **args: logging.warning("equipment_draw called before it was initialized in the shed!")
        self.task_manager = TaskManager(self.vehicles, self.tools, self.roads, self.rect.center)

        # shading for roof
        large_shadow_map = ResourceManager.load_image("Lighting/shed_shadow_map.png", (1000, 1000)) # Already converted
        self.shadow_map = pg.transform.scale(large_shadow_map, (rect.w, rect.h*2/3))
        self.shadow_map.set_alpha(128)

        self.rebuild()

    def get_silo(self) -> SellPoint | None:
        """
        Returns the silo in the sellpoint_manager

        If the sellpoint_manager hasn't given the shed the silo yet, then the silo will be None
        """
        if self._silo is None:
            logging.warning(f"shed.silo property was called but shed._silo is still None! Returning NoneType value.")

        return self._silo

    def set_equipment_draw(self, equipment_draw: object) -> None:
        # Should be called from equipment.py at __init__
        self.equipment_draw = equipment_draw

        logging.debug("Recieved equipment_draw, setting it in every vehicle...")

        for vehicle in self.vehicles:
            vehicle.set_equipment_draw(self.equipment_draw)

        logging.info("equipment_draw has been set.")

    def set_silo(self, silo: SellPoint) -> None:
        self._silo = silo
        logging.debug(f"Shed received silo: {silo}.")

    def scale_roads(self) -> None:
        new_roads = []
        for road in self.roads:
            new_roads.append([])
            for point in self.roads[road]:
                px, py = point
                
                px *= self.scale
                py *= self.scale

                new_roads[-1].append((px, py)) 

        self.roads = new_roads

    def add_vehicle(self, save_attrs: Dict[str, any]) -> None:
        if save_attrs["header"]: vehicle_type = "Harvesters"
        else: vehicle_type = "Tractors"

        attrs = deepcopy(SaveManager().STATIC_VEHICLES_DICT[vehicle_type][save_attrs["brand"]][save_attrs["model"]])
        attrs.update(save_attrs)

        if attrs["header"]: vehicle = Header(self.game_surface, self.rect, attrs, self.scale, self.task_header, self.equipment_draw)
        else: vehicle = Tractor(self.game_surface, self.rect, attrs, self.scale, self.task_tractor, self.equipment_draw, self.get_silo)

        self.vehicles.append(vehicle)

    def add_tool(self, save_attrs: Dict[str, any]) -> None:
        attrs = deepcopy(SaveManager().STATIC_TOOLS_DICT[save_attrs["toolType"]][save_attrs["brand"]][save_attrs["model"]])
        attrs.update(save_attrs)

        tool = Tool(self.game_surface, self.rect, attrs, self.scale)

        self.tools.append(tool)

    def get_vehicle(self, vehicle_id: int) -> Tractor | Header:
        for vehicle in self.vehicles:
            if vehicle.vehicle_id == vehicle_id: return vehicle

    def task_tractor(self, tractor: Tractor, tool: Tool, destination: Destination, stage: int = -1) -> None:
        job = self.task_manager.create_job(tractor, tool, tractor.destination, destination)
        path = job.generate_path()

        tractor.destination = destination
        tractor.tool = tool
        tool.destination = destination
        tool.vehicle = tractor

        if not tool.active:
            tractor.tool.assign_vehicle(tractor)

        if destination.is_paddock: paddock = int(destination.destination.num) - 1 # its an index
        else: paddock = -1

        tractor.set_path(job, path, stage, paddock)
    
    def task_header(self, header: Header, destination: Destination, stage: int = -1) -> None:
        job = self.task_manager.create_job(header, None, header.destination, destination)
        path = job.generate_path()

        header.destination = destination

        if destination.is_paddock: paddock = int(destination.destination.num) - 1 # its an index
        else: paddock = -1

        header.set_path(job, path, stage, paddock)

    def simulate(self, dt: float) -> None:
        self.update()

        for vehicle in self.vehicles:
            if vehicle.active:
                vehicle.update(dt)

    def rebuild(self) -> None:
        self.surface.fill((0, 0, 0, 255))

        # Shed
        pg.draw.rect(self.surface, self.color, pg.Rect(0, 0, self.rect.w, self.rect.h*2/3))
        self.surface.blit(self.shadow_map, (0, 0))

        # Line in middle of shed
        pg.draw.line(self.surface, (150, 150, 200), (0, self.rect.h/3), (self.rect.w, self.rect.h/3), 2)

        # Concrete pad in front of shed
        pg.draw.rect(self.surface, self.pad_color, pg.Rect(0, self.rect.h*2/3, self.rect.w, self.rect.h/3))
    
    def update(self) -> None:
        if self.events.check_mouse_hit(self.global_rect):
            # Sleep
            self.request_sleep()

    def render2(self) -> None:
        utils.blit_centered(self.game_surface, self.surface, (self.rect.x, self.rect.y), (self.rect.w/2, self.rect.h/2), self.rotation)

        if DEBUG_ROADS:
            for road in self.roads:
                for i, point in enumerate(road[:-1]):
                    px, py = point
                    nx, ny = road[i+1]

                    pg.draw.line(self.game_surface, (255, 255, 0), (px, py), (nx, ny))