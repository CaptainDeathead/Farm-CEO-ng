import pygame as pg
import math
import os

from typing import List, Tuple

pg.init()

PATH: str = os.path.abspath('.')
ASSETS_PATH: str = PATH + '/assets'
IMAGES_PATH: str = ASSETS_PATH + '/images'

# https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
def rotate_point_centered(origin: Tuple[float, float], point: Tuple[float, float], angle: float) -> Tuple[int, int]:
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in radians.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)

    return qx, qy

def rotate_image_centered(image: pg.Surface, angle: float, x: float, y: float) -> Tuple[pg.Surface, pg.Rect]:
    rotated_image = pg.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=(x, y))

    return rotated_image, new_rect

class Hitch:
    def __init__(self, local_x: float, local_y: float, parent_center: Tuple[float, float]) -> None:
        self.local_x: float = local_x
        self.local_y: float = local_y
        self.parent_center: Tuple[float, float] = parent_center

        self.global_x: float = parent_center[0] + local_x
        self.global_y: float = parent_center[1] + local_y

        self.local_position: Tuple[float, float] = (self.local_x, self.local_y)
        self.position: Tuple[float, float] = (self.global_x, self.global_y)
        self.vector: pg.math.Vector2 = pg.math.Vector2(self.local_position)

    @property
    def x(self) -> float: return self.global_x

    @property
    def y(self) -> float: return self.global_y

    def update_parent_center(self, new_center: Tuple[float, float]) -> None:
        self.global_x += new_center[0] - self.parent_center[0]
        self.global_y += new_center[1] - self.parent_center[1]

        self.parent_center = new_center

        self.position = (self.global_x, self.global_y)

    def update_position(self, x: float, y: float) -> None:
        self.global_x = x
        self.global_y = y

        self.position = (self.global_x, self.global_y)

class Vehicle:
    def __init__(self, screen: pg.Surface, image: pg.Surface, pos: Tuple[float, float], hitch_offset_x: int, hitch_offset_y: int) -> None:
        self.screen: pg.Surface = screen
        
        self.original_image: pg.Surface = image
        self.image: pg.Surface = self.original_image

        self.width: int = self.original_image.get_width()
        self.height: int = self.original_image.get_height()

        self.rect: pg.Rect = self.image.get_rect()
        self.x: float = pos[0]
        self.y: float = pos[1]
        self.update_rect()
        
        self.rotation: float = 0.0
        self.velocity: List[float] = [0, 0]
        self.hitch: Hitch = Hitch(hitch_offset_x, hitch_offset_y, self.rect.center)

    @property
    def position(self) -> pg.math.Vector2:
        return pg.math.Vector2((self.x, self.y))

    @property
    def speed(self) -> float:
        return math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)

    def rotate_image_centered(self, angle: float):
        self.image = pg.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.original_image.get_rect(topleft=(self.x, self.y)).center)

    def update_rect(self) -> None:
        self.rect.x = self.x
        self.rect.y = self.y

    def move(self, delta_time: float) -> None:
        self.x += self.velocity[0] * delta_time
        self.y += self.velocity[1] * delta_time

        self.velocity[0] *= 0.9 / delta_time
        self.velocity[1] *= 0.9 / delta_time

    def draw(self, delta_time: float) -> None:
        self.move(delta_time)

        self.update_rect()
        self.rotate_image_centered(self.rotation)

        self.hitch.update_parent_center(self.rect.center)

        self.screen.blit(self.image, self.rect.topleft)

        rotated_hitch = rotate_point_centered(self.rect.center, self.rect.center + self.hitch.vector, math.radians(-self.rotation))

        self.hitch.update_position(rotated_hitch[0], rotated_hitch[1])

        pg.draw.circle(self.screen, (0, 0, 255), rotated_hitch, 3)
        pg.draw.circle(self.screen, (0, 0, 255), self.position, 3)

class Trailer:
    def __init__(self, screen: pg.Surface, vehicle: Vehicle, image: pg.Surface, pos: Tuple[float, float], hitch_offset_x: int, hitch_offset_y: int) -> None:
        self.screen: pg.Surface = screen
        self.vehicle: Vehicle = vehicle

        self.original_image: pg.Surface = image
        self.image: pg.Surface = self.original_image

        self.rect: pg.Rect = self.image.get_rect()
        self.x: float = pos[0]
        self.y: float = pos[1]
        self.update_rect()

        self.rotation: float = 0.0
        self.hitch: Hitch = Hitch(hitch_offset_x, hitch_offset_y, self.rect.center)

    @property
    def position(self) -> pg.math.Vector2: return pg.math.Vector2((self.x, self.y))

    def rotate_image_centered(self, angle) -> None:
        self.image = pg.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def direction_to_vehicle(self, delta_time: float) -> float:
        """
        Degrees
        """

        direction = math.degrees(math.atan2(self.vehicle.hitch.y-self.hitch.y, self.vehicle.hitch.x-self.hitch.x)) + 90

        change = direction + self.rotation
        if change > 270: change -= 360

        if change < -90: change = 1000
        elif change > 90: change = -1000

        change /= 30 / delta_time ** 2

        rotation = self.rotation - change * self.vehicle.speed

        return rotation

    def snap_to_parent(self) -> None:
        direction = [math.cos(math.radians(-self.vehicle.rotation-90)), math.sin(math.radians(-self.vehicle.rotation-90))]

        self.x += round(self.vehicle.hitch.x - self.hitch.x - direction[0] * 5, 0)
        self.y += round(self.vehicle.hitch.y - self.hitch.y - direction[1] * 5, 0)

    def update_rect(self) -> None:
        self.rect.x = self.x
        self.rect.y = self.y

    def draw(self, delta_time: float) -> None:
        self.rotation %= 360
        self.rotation = self.direction_to_vehicle(delta_time)

        self.update_rect()

        rotated_hitch = rotate_point_centered(self.rect.center, self.rect.center+self.hitch.vector, -math.radians(self.rotation))
        self.hitch.update_position(rotated_hitch[0], rotated_hitch[1])

        self.snap_to_parent()

        self.rotate_image_centered(self.rotation)
        self.hitch.update_parent_center(self.rect.center)

        self.screen.blit(self.image, (self.x, self.y))

        #pg.draw.circle(self.screen, (0, 255, 0), rotated_hitch, 3)

class Test:
    def __init__(self) -> None:
        self.screen: pg.Surface = pg.display.set_mode((800, 800))
        self.clock: pg.time.Clock = pg.time.Clock()
        self.vehicle: Vehicle = Vehicle(self.screen, pg.image.load(f"{IMAGES_PATH}/tractor_0.png"), (200.0, 200.0), 0, 14)
        self.trailer: Trailer = Trailer(self.screen, self.vehicle, pg.image.load(f"{IMAGES_PATH}/tool_0.png"), (240.0, 200.0), 0, -5)

    def main(self) -> None:
        dt: float = 0.0001 # 0 devision errors

        while 1:
            self.screen.fill((0, 0, 0))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()

            pg.display.set_caption(str(self.clock.get_fps()))

            keys = pg.key.get_pressed()

            if keys[pg.K_w]:
                direction = [math.cos(math.radians(-self.vehicle.rotation-90)), math.sin(math.radians(-self.vehicle.rotation-90))]

                self.vehicle.velocity[0] = direction[0] * 1
                self.vehicle.velocity[1] = direction[1] * 1

            if keys[pg.K_a]: self.vehicle.rotation += 1 * self.vehicle.speed * dt
            if keys[pg.K_d]: self.vehicle.rotation -= 1 * self.vehicle.speed * dt

            self.vehicle.draw(dt)
            self.trailer.draw(dt)

            pg.display.flip()
            dt = self.clock.tick(60) / 1000 * 60

if __name__ == "__main__":
    test = Test()
    test.main()
