import pygame as pg
import logging

from save_manager import SaveManager
from data import *
from typing import Tuple, List

class Events:
    def __init__(self) -> None:
        self.mouse_just_pressed = pg.mouse.get_pressed()[0]
        self.mouse_press_override = False

        self.mouse_just_released = False
        self.mouse_start_press_location = (-1, -1)

        self.authority_mouse_just_pressed = pg.mouse.get_pressed()[0]
        self.authority_mouse_just_released = False
        self.authority_mouse_start_press_location = (-1, -1)

        self.mouse_pos = pg.mouse.get_pos()

        self.override_locked: bool = False
        self.override_requires_authority: bool = False # Allows specific, private access for top-level elements such as popups to the override state, while freezing it for non-authorities

    def set_override(self, override: bool) -> None:
        self.mouse_press_override = override

    def lock_override(self, authority: bool = False) -> None:
        if self.override_requires_authority and not authority: return

        self.override_locked = True

    def unlock_override(self, authority: bool = False) -> None:
        if self.override_requires_authority and not authority: return
        
        self.override_locked = False

    def set_override_authority_requirement(self, authority_requirement: bool) -> None:
        self.override_requires_authority = authority_requirement

        self.mouse_just_pressed = False
        self.mouse_just_released = False

    def log_mouse_events(self) -> None:
        logging.info(f"{self.mouse_just_pressed=}, {self.mouse_just_released=}, {self.authority_mouse_just_pressed=}, {self.authority_mouse_just_released=}, {self.mouse_press_override=}")

    def process_events(self, events: List[pg.event.Event]) -> None:
        if not self.override_requires_authority:
            self.mouse_just_pressed = False
            self.mouse_just_released = False

        self.authority_mouse_just_pressed = False
        self.authority_mouse_just_released = False

        self.mouse_pos = pg.mouse.get_pos()

        for event in events:
            if event.type == pg.QUIT:
                logging.info("Farm CEO is closing (pg.QUIT event recieved)...")
                SaveManager().save_game()

                pg.quit()
                exit()

            elif event.type == pg.ACTIVEEVENT:
                if event.state == 2 and event.gain == 0: # Lost focus
                    logging.info("Farm CEO is no longer in focus (pg.ACTIVEEVENT event recieved)...")
                    SaveManager().save_game()

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.override_requires_authority:
                        self.mouse_just_pressed = True
                        self.mouse_start_press_location = self.mouse_pos

                    self.authority_mouse_just_pressed = True
                    self.authority_mouse_start_press_location = self.mouse_pos

            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.set_override(False)

                    if not self.override_requires_authority:
                        self.mouse_just_released = True

                    self.authority_mouse_just_released = True

                if DEBUG_MOUSE_EVENTS: self.log_mouse_events()

        if self.mouse_press_override:
            if not self.override_requires_authority:
                self.mouse_just_pressed = False

            self.authority_mouse_just_pressed = False