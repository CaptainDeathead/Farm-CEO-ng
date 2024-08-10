import pygame as pg

from typing import Tuple, List

class Events:
    def __init__(self) -> None:
        self.mouse_just_pressed: bool = False
        self.mouse_pos: Tuple[int, int] = pg.mouse.get_pos()

    def process_events(self, events: List[pg.event.Event]) -> None:
        if self.mouse_just_pressed: self.mouse_just_pressed = False

        self.mouse_pos = pg.mouse.get_pos()

        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1: self.mouse_just_pressed = True