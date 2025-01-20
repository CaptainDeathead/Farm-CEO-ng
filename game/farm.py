import pygame as pg

from resource_manager import ResourceManager
from save_manager import SaveManager

from machinary import Tractor, Header, Tool
from destination import Destination
from utils import utils, LayableRenderObj
from data import *

from copy import deepcopy
from math import sqrt
from typing import List, Dict, Sequence

class Job:
    def __init__(self,
                 start_location: Destination,
                 end_location: Destination,
                 vehicle: Tractor | Header,
                 tool: Tool | None,
                 ) -> None:
        
        self.start_location = start_location
        self.end_location = end_location
        self.vehicle = vehicle
        self.tool = tool

    def get_closest_point_on_boundary(self, point: Tuple, boundary: List[Tuple]) -> Tuple | None:
        closest_dist = float('inf')
        closest_point = None

        for px, py in boundary:
            dist = sqrt((point[0] - px) ** 2 + (point[1] - py) ** 2)

            if dist < closest_dist:
                closest_dist = dist
                closest_point = (px, py)

        return closest_point

    def trace_collision_boundary(self, point_end: Tuple, point_start: Tuple, boundary: List[Tuple]) -> List[Tuple]:
        point_end = self.get_closest_point_on_boundary(point_end, boundary)
        point_start = self.get_closest_point_on_boundary(point_start, boundary)

        point_1_index = boundary.index(point_end)
        point_2_index = boundary.index(point_start)

        if point_1_index > point_2_index:
            indexes_reversed = True
            p1_index = point_2_index
            p2_index = point_1_index
        else:
            indexes_reversed = False
            p1_index = point_1_index
            p2_index = point_2_index

        dist_1 = 0
        for px, py in boundary[p1_index:p2_index]:
            index = boundary.index((px, py))
            nx, ny = boundary[index+1]
            dist_1 += sqrt((nx - px) ** 2 + (ny - py) ** 2)

        dist_2 = 0
        for px, py in boundary[p1_index::-1]:
            index = boundary.index((px, py))
            nx, ny = boundary[index+1]
            dist_2 += sqrt((nx - px) ** 2 + (ny - py) ** 2)

        for px, py in boundary[-1:p2_index-1:-1]:
            index = boundary.index((px, py))

            nx, ny = boundary[index + 1]
            dist_2 += sqrt((nx - px) ** 2 + (ny - py) ** 2)

        if dist_1 < dist_2:
            path = boundary[p1_index:p2_index]
        else:
            path = boundary[p1_index::-1] # p1_index down to 0
            path.extend(boundary[-1:p2_index-1:-1]) # Going to end of boundary from start so: end_index down to l2 index

        if indexes_reversed:
            return reversed(path)
        else:
            return path

    def draw_path(self, path) -> None:
        screen = pg.display.get_surface()
        
        for i, point in enumerate(path):
            pg.draw.line(screen, (255, 0, 0), (path[i-1][0] + 620, path[i-1][1]), (point[0] + 620, point[1]))
            pg.display.flip()

    def generate_working_path(self, paddock_destination: Destination, working_width: float, outside_laps: int = 2, skiprow: bool = False) -> List[Sequence[float]]:
        """
        How does this work?

        2 Parts:
            - Outside laps (2)
            - A/B Runlines

        Outside laps:
            1. Shrink the polygon by half the size of the tool to get the first lap.
            2. Then shrink that polygon by the tools whole size to get the second lap.
            3. Repeat step 2 for however many laps you want
            4. Shrink the polygon by half the size of the tool to get the collision polygon.

        The collision polygon is used to check when the vehicle needs to turn on A/B Runlines.
        The end position of the machine is used to figure out when it needs to start turning as it'll stop colliding with the collision shape (make a mask of it)

        A/B Runlines:
            1. Get the collision polygons rect and the longest side.
            2. Construct lines separated by the working width going in the direction of the longest side.
            3. Once the lines are no longer touching the collision shape, check if they touch again untill they go out of the rect.
            
            THIS BIT ASSUMES ITS NORTH-SOUTH A/B RUNLINES, FLIP THE X / Y's FOR EAST-WEST
            4. If there is more than one intersection, get the point on the boundary, and all the points with the same x coords.
                - If you are going up then find the closest coord with its y value above where you are out of your filtered coords, else get the y blow you.
                - This is the coord around the obstical. Its the continued A/B line between that coord and the furthest one by its y value.
                - Using your position and the found coord, find the difference between their indexes in the collision shape.
                    (2 posible paths, from the index of the first coord to the second one in the list e.g. 3-8 with total len 5 or from the index of the first one wrapping around to the second one e.g. 0-3, 8-11 with total len 6)
                - The smallest index difference is the shortest path. Slice the collision shape's list of points to all the index inbetween and its your shortest path to the rest of the A/B
        """

        # Outside laps
        paddock = paddock_destination.destination
        boundary = paddock.boundary

        lap_1 = utils.shrink_polygon(boundary, working_width / 2)
        self.draw_path(lap_1)

        path = []
        path.extend(lap_1)

        laps = [lap_1]
        for i in range(outside_laps - 1):
            new_lap = utils.shrink_polygon(boundary, working_width * (i + 1))

            closest_dist = float('inf')
            closest_point_index = new_lap[0]
            last_lap_point = laps[-1][-1]

            for i, (px, py) in enumerate(new_lap):
                dist = sqrt((last_lap_point[0] - px) ** 2 + (last_lap_point[1] - py) ** 2)

                if dist < closest_dist:
                    closest_dist = dist
                    closest_point_index = i 
            
            finished_lap = new_lap[closest_point_index:]
            finished_lap.extend(new_lap[:closest_point_index])

            laps.append(finished_lap)

            path.extend(laps[-1])
            self.draw_path(laps[-1])

        collision_polygon = utils.shrink_polygon(laps[-1], working_width / 2)
        self.draw_path(collision_polygon)

        # A/B Runlines
        collision_polygon_rect = utils.get_polygon_rect(collision_polygon) 

        # TODO: Locallise the polygons position first so surface isnt big
        collision_polygon_surf = pg.Surface((collision_polygon_rect.x + collision_polygon_rect.w, collision_polygon_rect.y + collision_polygon_rect.h), pg.SRCALPHA)
        pg.draw.polygon(collision_polygon_surf, (255, 0, 0), collision_polygon)
        collision_polygon_mask = pg.mask.from_surface(collision_polygon_surf)

        north = collision_polygon_rect.h > collision_polygon_rect.w
        ab_runlines = []

        if north:
            for x in range(collision_polygon_rect.x + int(working_width / 2), collision_polygon_rect.x + collision_polygon_rect.w, working_width): # TODO: Locallise the polygons position first so surface isnt big
                line_start = (x, collision_polygon_rect.y)
                line_end = (x, collision_polygon_rect.y + collision_polygon_rect.h)

                point_collisions_list = utils.line_collides_mask((line_start, line_end), collision_polygon_mask, collision_polygon_rect)

                point_collisions = []
                for i, col_list in enumerate(point_collisions_list):
                    point_collisions.extend(col_list[::10]) # Every 10 px

                    if i >= len(point_collisions_list) - 1: break

                    # Path around the first lap
                    point_collisions.extend(self.trace_collision_boundary(col_list[-1], point_collisions_list[i+1][0], lap_1))

                if DEBUG_PATH_GENERATION:
                    for point in point_collisions:
                        pg.display.get_surface().set_at((point[0] + 620, point[1]), (0, 0, 255))
                    pg.display.flip()

                ab_runlines.append(point_collisions)
        else:
            for y in range(collision_polygon_rect.y + int(working_width / 2), collision_polygon_rect.y + collision_polygon_rect.h, working_width): # TODO: Locallise the polygons position first so surface isnt big
                line_start = (collision_polygon_rect.x, y)
                line_end = (collision_polygon_rect.x + collision_polygon_rect.w, y)

                point_collisions_list = utils.line_collides_mask((line_start, line_end), collision_polygon_mask, collision_polygon_rect)[::10]

                point_collisions = []
                for col_list in point_collisions_list:
                    point_collisions.extend(col_list[::10]) # Every 10 px

                    if i >= len(point_collisions_list) - 1: break

                    # Path around the first lap
                    point_collisions.extend(self.trace_collision_boundary(col_list[-1], point_collisions_list[i+1][0], lap_1))

                if DEBUG_PATH_GENERATION:
                    for point in point_collisions:
                        pg.display.get_surface().set_at((point[0] + 620, point[1]), (0, 0, 255))
                    pg.display.flip()

                ab_runlines.append(point_collisions)

        if skiprow:
            skipped_rows = []
            non_skipped_rows = []
            skip_this_row = True

            for runline in ab_runlines:
                skip_this_row = not skip_this_row

                if skip_this_row:
                    skipped_rows.insert(0, runline)
                else:
                    non_skipped_rows.append(runline)

            ab_runlines = []
            ab_runlines.extend(non_skipped_rows)
            ab_runlines.extend(skipped_rows)

        ab_reversed = True
        for i, runline in enumerate(ab_runlines):
            ab_reversed = not ab_reversed

            if i >= len(ab_runlines) - 1:
                next_runline = []
            else:
                next_runline = ab_runlines[i+1]
            
            if ab_reversed:
                directed_runline = list(reversed(runline))
                directed_next_runline = next_runline
            else:
                directed_runline = runline
                directed_next_runline = list(reversed(runline))
            
            path.extend(directed_runline)

            if next_runline == []: continue

            # Checks if next runline is close enough to go without path
            dist = sqrt((directed_runline[-1][0] - directed_next_runline[0][0]) ** 2 + (directed_runline[-1][1] - directed_next_runline[0][1]) ** 2)

            # If its too far, it will follow the boundary
            if dist > working_width * 2:
                path.extend(self.trace_collision_boundary(directed_runline[-1], directed_next_runline[0], lap_1))

        return path

    def generate_path(self) -> None:
        if self.tool is None:
            # Header
            if self.start_location.is_paddock:
                if self.end_location.is_paddock:
                    # Generate working
                    ...
                else:
                    # Go home
                    ...
            else:
                if self.end_location.is_paddock:
                    # Go to paddock
                    ...

        elif self.tool.tool_type == "Trailer":
            ...

        else:
            if self.start_location.is_paddock:
                if self.end_location.is_paddock:
                    # Generate working
                    ...
                else:
                    # Go home
                    ...
            else:
                if self.end_location.is_paddock:
                    # Go to paddock
                    ...

class TaskManager:
    def __init__(self, vehicles: List, tools: List) -> None:
        self.vehicles = vehicles
        self.tools = tools

        self.jobs = []

    def test_make_job(self, paddock) -> None:
        start_dest = Destination(paddock)
        end_dest = Destination(paddock)
        job = Job(start_dest, end_dest, None, None)
        return job.generate_working_path(end_dest, 15, 2, True)

class Shed(LayableRenderObj):
    def __init__(self, game_surface: pg.Surface, rect: pg.Rect, rotation: float) -> None:        
        self.game_surface = game_surface

        self.rect = rect

        self.rotation = rotation
        self.color = pg.Color(175, 195, 255)
        self.pad_color = pg.Color(213, 207, 207)
        self.surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.vehicles: List[Tractor | Header] = []
        self.tools: List[Tool] = []

        self.task_manager = TaskManager(self.vehicles, self.tools)

        # shading for roof
        large_shadow_map = ResourceManager.load_image("Lighting/shed_shadow_map.png", (1000, 1000)) # Already converted
        self.shadow_map = pg.transform.scale(large_shadow_map, (rect.w, rect.h*2/3))
        self.shadow_map.set_alpha(128)

        self.rebuild()

    def add_vehicle(self, save_attrs: Dict[str, any]) -> None:
        if save_attrs["header"]: vehicle_type = "Harvesters"
        else: vehicle_type = "Tractors"

        attrs = deepcopy(SaveManager().STATIC_VEHICLES_DICT[vehicle_type][save_attrs["brand"]][save_attrs["model"]])
        attrs.update(save_attrs)

        if attrs["header"]: vehicle = Header(self.game_surface, self.rect, attrs)
        else: vehicle = Tractor(self.game_surface, self.rect, attrs)

        self.vehicles.append(vehicle)

    def add_tool(self, save_attrs: Dict[str, any]) -> None:
        attrs = deepcopy(SaveManager().STATIC_TOOLS_DICT)
        attrs.update(save_attrs)

        tool = Tool(self.game_surface, self.rect, attrs)

        self.tools.append(tool)

    def get_vehicle(self, vehicle_id: int) -> Tractor | Header:
        for vehicle in self.vehicles:
            if vehicle.vehicle_id == vehicle_id: return vehicle

    def task_tractor(self, vehicle: Tractor) -> None:
        ...
    
    def task_header(self, vehicle: Header) -> None:
        ...

    def rebuild(self) -> None:
        self.surface.fill((0, 0, 0, 255))

        # Shed
        pg.draw.rect(self.surface, self.color, pg.Rect(0, 0, self.rect.w, self.rect.h*2/3))
        self.surface.blit(self.shadow_map, (0, 0))

        # Line in middle of shed
        pg.draw.line(self.surface, (150, 150, 200), (0, self.rect.h/3), (self.rect.w, self.rect.h/3), 2)

        # Concrete pad in front of shed
        pg.draw.rect(self.surface, self.pad_color, pg.Rect(0, self.rect.h*2/3, self.rect.w, self.rect.h/3))

    def render2(self) -> None:
        utils.blit_centered(self.game_surface, self.surface, (self.rect.x, self.rect.y), (self.rect.w/2, self.rect.h/2), self.rotation)
