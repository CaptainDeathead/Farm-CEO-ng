import pygame as pg
from time import sleep, time

pg.init()

screen = pg.display.set_mode((400, 400))

clock = pg.time.Clock()
target_fps = 60

paddock_polygon = [(10, 10), (40, 15), (80, 5), (240, 150), (380, 300), (100, 280)]
polygon_surface = pg.Surface((380, 300), pg.SRCALPHA)
polygon_surface.fill((0, 0, 0, 0))
pg.draw.polygon(polygon_surface, (255, 0, 0), paddock_polygon)

seeded_rect = pg.Rect(50, 170, 30, 30)
rect_surface = pg.Surface((seeded_rect.w, seeded_rect.h), pg.SRCALPHA)
rect_surface.fill((0, 0, 0, 0))
pg.draw.rect(rect_surface, (0, 0, 255), (0, 0, seeded_rect.w, seeded_rect.h))

polygon_mask = pg.mask.from_surface(polygon_surface)
rect_mask = pg.mask.from_surface(rect_surface)

while 1:
    dt = clock.tick(target_fps)
    screen.fill((0, 0, 0))

    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            exit()

    screen.blit(polygon_mask.to_surface(), (0, 0))
    screen.blit(rect_mask.to_surface(), (seeded_rect.x, seeded_rect.y))

    screen.blit(polygon_mask.overlap_mask(rect_mask, (seeded_rect.x, seeded_rect.y)).to_surface(setcolor=(0, 255, 0), unsetcolor=(0, 0, 0, 0)))

    pg.display.flip()