import pygame as pg
from time import sleep, time

pg.init()

screen = pg.display.set_mode((400, 400))

clock = pg.time.Clock()
target_fps = 60

paddock_polygon = [(10, 10), (40, 15), (80, 5), (240, 150), (380, 300), (100, 280)]

seeded_rect = pg.Rect(50, 170, 30, 30)

while 1:
    dt = clock.tick(target_fps)
    screen.fill((0, 0, 0))

    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            exit()

    pg.draw.polygon(screen, (255, 0, 0), paddock_polygon)
    pg.draw.rect(screen, (0, 0, 255), seeded_rect)

    pg.display.flip()