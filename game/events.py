import pygame as pg

from typing import Tuple

class Events:
    def __init__(self) -> None:
        self.mouse_just_pressed: bool = False
        self.mouse_pos: Tuple[int, int] = pg.mouse.get_pos()

    def process_events(self) -> None:
        if self.mouse_just_pressed: self.mouse_just_pressed = False

        self.mouse_pos = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1: self.mouse_just_pressed = True