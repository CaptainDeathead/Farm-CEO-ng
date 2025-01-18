import pygame as pg

from resource_manager import ResourceManager
from save_manager import SaveManager

from machinary import Tractor, Header, Tool
from destination import Destination
from utils import utils, LayableRenderObj
from data import *

from copy import deepcopy
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

    def join_line_endings(self, line_1_end: Tuple, line_2_start: Tuple, boundary: List[Tuple]) -> List[Tuple]:
        line_1_index = boundary.index(line_1_end)
        line_2_index = boundary.index(line_2_start)

        if line_1_index > line_2_index:
            indexes_reversed = True
            l1_index = line_2_index
            l2_index = line_1_index
        else:
            indexes_reversed = False
            l1_index = line_1_index
            l2_index = line_2_index

        dist_1 = l1_index - l2_index
        dist_2 = l1_index + ((len(boundary) - 1) - l2_index)

        if dist_1 < dist_2:
            path = boundary[l1_index:l2_index]
        else:
            path = boundary[l1_index::-1] # l1_index down to 0
            path.extend(boundary[-1:l2_index-1:-1]) # Going to end of boundary from start so: end_index down to l2 index

        if indexes_reversed:
            return reversed(path)
        else:
            return path

    def draw_path(self, path) -> None:
        screen = pg.display.get_surface()
        
        for i, point in enumerate(path):
            pg.draw.line(screen, (255, 0, 0), (path[i-1][0] + 620, path[i-1][1]), (point[0] + 620, point[1]))
            pg.display.flip()
            pg.time.wait(10)
            #screen.set_at((point[0] + 620, point[1]), (255, 0, 0))

        pg.display.flip()

    def generate_working_path(self, paddock_destination: Destination, working_width: float, outside_laps: int = 2) -> List[Sequence[float]]:
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
        for _ in range(outside_laps - 1):
            laps.append(utils.shrink_polygon(laps[-1], working_width))
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

        if north:
            for x in range(collision_polygon_rect.x + int(working_width / 2), collision_polygon_rect.x + collision_polygon_rect.w, working_width): # TODO: Locallise the polygons position first so surface isnt big
                line_start = (x, collision_polygon_rect.y)
                line_end = (x, collision_polygon_rect.y + collision_polygon_rect.h)

                point_collisions = utils.line_collides_mask((line_start, line_end), collision_polygon_mask, collision_polygon_rect)
                lines = utils.lines_form_points(point_collisions)

                for point in point_collisions:
                    pg.display.get_surface().set_at((point[0] + 620, point[1]), (0, 0, 255))

                for line in lines:
                    #pg.draw.line(pg.display.get_surface(), (0, 0, 255), (line[0][0] + 620, line[0][1]), (line[1][0] + 620, line[1][1]))
                    pg.display.flip()
                    pg.time.wait(100)

                line_path = []

                if len(lines) > 1:
                    for i, line in enumerate(lines[0:-1]):
                        join_path = self.join_lines(line[1], lines[i+1][0], boundary)

                        line_path.extend(line)
                        line_path.extend(join_path)
                else:
                    line_path.extend(lines[0])

                line_transition = (line_end[0] + working_width / 2, line_end[1] + working_width)

                path.extend(line_path)
                path.append(line_transition)
        else:
            for y in range(collision_polygon_rect.y + int(working_width / 2), collision_polygon_rect.y + collision_polygon_rect.h, working_width): # TODO: Locallise the polygons position first so surface isnt big
                line_start = (collision_polygon_rect.x, y)
                line_end = (collision_polygon_rect.x + collision_polygon_rect.w, y)

                point_collisions = utils.line_collides_mask((line_start, line_end), collision_polygon_mask, collision_polygon_rect)
                lines = utils.lines_form_points(point_collisions)

                for line in lines:
                    pg.draw.line(pg.display.get_surface(), (0, 0, 255), (line[0][0] + 620, line[0][1]), (line[1][0] + 620, line[1][1]))
                    pg.display.flip()
                    pg.time.wait(100)

                line_path = []

                if len(lines) > 1:
                    for i, line in enumerate(lines[0:-1]):
                        join_path = self.join_lines(line[1], lines[i+1][0], boundary)

                        line_path.extend(line)
                        line_path.extend(join_path)
                else:
                    line_path.extend(lines[0])

                line_transition = (line_end[0] + working_width, line_end[1] + working_width / 2)

                path.extend(line_path)
                path.append(line_transition)

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
        return job.generate_working_path(end_dest, 10, 2)

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
