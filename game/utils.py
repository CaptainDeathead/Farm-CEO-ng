import pygame as pg

from shapely.geometry import Polygon
from data import *

from math import atan2, degrees, cos, sin
from typing import Tuple

class utils:
    # https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
    @staticmethod
    def blit_centered(surf: pg.Surface, image: pg.Surface, pos: Tuple[int, int], obj_center: Tuple[int, int], angle: float):

        # offset from pivot to center
        image_rect = image.get_rect(topleft = (pos[0] - obj_center[0], pos[1]-obj_center[1]))
        offset_center_to_pivot = pg.math.Vector2(pos) - image_rect.center
        
        # roatated offset from pivot to center
        rotated_offset = offset_center_to_pivot.rotate(-angle)

        # roatetd image center
        rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)

        # get a rotated image
        rotated_image = pg.transform.rotate(image, angle)
        rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

        # rotate and blit the image
        surf.blit(rotated_image, rotated_image_rect)

    
    @staticmethod
    # https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    def rotate_point_centered(origin: Tuple[float, float], point: Tuple[float, float], angle: float) -> Tuple[int, int]:
        """
        Rotate a point counterclockwise by a given angle around a given origin.
        The angle should be given in radians.
        """
        ox, oy = origin
        px, py = point

        qx = ox + cos(angle) * (px - ox) - sin(angle) * (py - oy)
        qy = oy + sin(angle) * (px - ox) + cos(angle) * (py - oy)

        return qx, qy

    @staticmethod
    def scale_rect(rect: pg.Rect, scale: float) -> pg.Rect:
        return pg.Rect(rect.x * scale, rect.y * scale, rect.w * scale, rect.h * scale)

    @staticmethod
    def shrink_polygon(polygon: list[tuple[int, int]], shrink: int) -> list[tuple[int, int]]:
        poly = Polygon(polygon)
        coords = list(poly.buffer(-shrink).exterior.coords)

        processed_coords = []
        for i in range(1, len(coords)):
            p1_raw = coords[i-1]
            p2_raw = coords[i]

            p1 = (int(round(p1_raw[0], 0)), int(round(p1_raw[1], 0)))
            p2 = (int(round(p2_raw[0], 0)), int(round(p2_raw[1], 0)))

            processed_coords.append(p1)

            if p1[0] == p2[0]:
                if abs(p2[1] - p1[1]) != 1:
                    if p1[1] < p2[1]:
                        additions = [(p1[0], y) for y in range(p1[1] + 1, p2[1])]
                        processed_coords.extend(additions)
                    else:
                        additions = [(p1[0], y) for y in range(p2[1] + 1, p1[1])]
                        processed_coords.extend(list(reversed(additions)))

            elif p1[1] == p2[1]:
                if abs(p2[0] - p1[0]) != 1:
                    if p1[0] < p2[0]:
                        additions = [(x, p1[1]) for x in range(p1[0] + 1, p2[0])]
                        processed_coords.extend(additions)
                    else:
                        additions = [(x, p1[1]) for x in range(p2[0] + 1, p1[0])]
                        processed_coords.extend(list(reversed(additions)))

            processed_coords.append(p2) 

        return processed_coords

    @staticmethod
    def get_polygon_rect(polygon: list[tuple[int, int]]) -> pg.Rect:
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = 0, 0

        for coord in polygon:
            if coord[0] < min_x: min_x = coord[0]
            if coord[0] > max_x: max_x = coord[0]

            if coord[1] < min_y: min_y = coord[1]
            if coord[1] > max_y: max_y = coord[1]

        width, height = max_x - min_x, max_y - min_y
        rect = pg.Rect(min_x, min_y, width, height)

        return rect

    @staticmethod
    def line_collides_mask(line: list[tuple, tuple], mask: pg.Mask, polygon_rect: pg.Rect) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        line_start = line[0]
        line_end = line[1]

        step_x = 0
        step_y = 0

        if line_start[0] > line_end[0]:
            step_x = -1
        elif line_start[0] < line_end[0]:
            step_x = 1
        
        if line_start[1] > line_end[1]:
            step_y = -1
        elif line_start[1] < line_end[1]:
            step_y = 1

        x1, y1 = line_start
        x2, y2 = line_end

        collisions = []
        curr_collision_index = -1
        last_was_collision = not mask.get_at((x1, y1))
        while 1:
            if x1 == x2 and y1 == y2:
                break

            if mask.get_at((x1, y1)):
                if not last_was_collision:
                    curr_collision_index += 1
                    collisions.append([])

                collisions[curr_collision_index].append((x1, y1))

                last_was_collision = True

                if DEBUG_PATH_MASK_COLLISION:
                    pg.draw.circle(pg.display.get_surface(), (0, 255, 0), (x1 + 620, y1), 3)
                    pg.display.flip()
                    pg.time.wait(1)
            else:
                last_was_collision = False

                if DEBUG_PATH_MASK_COLLISION:
                    pg.draw.circle(pg.display.get_surface(), (255, 0, 0), (x1 + 620, y1), 3)
                    pg.display.flip()
                    pg.time.wait(1)
            
            x1 += step_x
            y1 += step_y

        return collisions

    @staticmethod
    def lines_form_points(points: list[tuple], tolerance: int = 1) -> list[tuple, tuple]:
        lines = []
        line = []

        lx, ly = points[0]

        for px, py in points[1:]:
            lx, ly = px, py
            if abs(px - lx) > tolerance or abs(py - ly) > tolerance:
                line.append((px, py))

                if len(line) == 2:
                    lines.append(line)
                    line = []

        if lines == [] and len(points) > 1:
            lines = [(points[0], points[-1])]
                
        return lines

    @staticmethod
    def angle_between_lines(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        x1, y1 = v1
        x2, y2 = v2

        dot_product = x1 * x2 + y1 * y2
        determinant = x1 * y2 - y1 * x2

        angle = atan2(determinant, dot_product)

        return degrees(angle) 

    @staticmethod
    def angle_difference(angle_1: float, angle_2: float) -> float:
        diff = angle_2 - angle_1
        diff = (diff + 180) % 360 - 180
        return diff

class VarsSingleton:
    def __new__(cls) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(VarsSingleton, cls).__new__(cls)

        return cls.instance
    
    def init(self, shed) -> None:
        self.shed = shed

class LayableRenderObj:
    def render0(self) -> None: ...
    def render1(self) -> None: ...
    def render2(self) -> None: ...

    def render(self) -> None:
        self.render0(); self.render1(); self.render2()