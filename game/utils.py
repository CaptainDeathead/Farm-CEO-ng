import pygame as pg

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