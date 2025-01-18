import pygame as pg
import pyclipper

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
    def scale_rect(rect: pg.Rect, scale: float) -> pg.Rect:
        return pg.Rect(rect.x * scale, rect.y * scale, rect.w * scale, rect.h * scale)

    @staticmethod
    def shrink_polygon(polygon: list[tuple[int, int]], shrink: int) -> list[tuple[int, int]]:
        offset = pyclipper.PyclipperOffset()
        offset.AddPath(polygon, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)

        return offset.Execute(-shrink)[0]

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
    def line_collides_mask(line: list[tuple, tuple], mask: pg.Mask, polygon_rect: pg.Rect) -> list[tuple[float, float]]:
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
        while 1:
            if x1 == x2 and y1 == y2:
                break

            if mask.get_at((x1, y1)):
                collisions.append((x1, y1))
            
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

class LayableRenderObj:
    def render0(self) -> None: ...
    def render1(self) -> None: ...
    def render2(self) -> None: ...

    def render(self) -> None:
        self.render0(); self.render1(); self.render2()