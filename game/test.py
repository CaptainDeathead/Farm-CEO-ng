import pygame as pg
from time import sleep, time

pg.init()

screen = pg.display.set_mode((400, 400))

clock = pg.time.Clock()
target_fps = 60

anim_progress = 0
speed = 10

start_time = time()
while anim_progress <= 400:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            exit()

    sleep(6 / target_fps)

    pg.draw.rect(screen, (255, 0, 0), (0, 0, anim_progress, 400))
    
    dt = clock.tick(target_fps) / 1000.0
    pg.display.flip()
    #print(dt)
    #print(anim_progress)
    anim_progress += speed * dt * target_fps
print(time() - start_time)

anim_progress = 0
screen.fill((0, 0, 0))

start_time = time()
while anim_progress <= 400:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            exit()

    sleep(0 / target_fps)

    pg.draw.rect(screen, (255, 0, 0), (0, 0, anim_progress, 400))
    
    dt = clock.tick(target_fps) / 1000.0
    pg.display.flip()
    #print(dt)
    #print(anim_progress)
    anim_progress += speed * dt * target_fps
print(time() - start_time)