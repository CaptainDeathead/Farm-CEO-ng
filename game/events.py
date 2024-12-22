import pygame as pg

from typing import Tuple, List

class Events:
    def __init__(self) -> None:
        self.mouse_just_pressed = pg.mouse.get_pressed()[0]
        self.mouse_press_override = False

        self.mouse_just_released = False
        self.mouse_start_press_location: Tuple[int, int] = (-1, -1)

        self.mouse_pos: Tuple[int, int] = pg.mouse.get_pos()

        self.override_locked: bool = False

    def set_override(self, override: bool) -> None:
        if not self.override_locked: self.mouse_press_override = override

    def lock_override(self) -> None:
        self.override_locked = True

    def unlock_override(self) -> None:
        self.override_locked = False

    def process_events(self, events: List[pg.event.Event]) -> None:
        self.mouse_just_pressed = False
        self.mouse_just_released = False

        self.mouse_pos = pg.mouse.get_pos()

        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                exit()

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_just_pressed = True

                    self.mouse_start_press_location = self.mouse_pos

            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.set_override(False)
                    self.mouse_just_released = True

        if self.mouse_press_override: self.mouse_just_pressed = False