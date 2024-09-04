import pygame as pg

from resource_manager import ResourceManager, SaveManager
from paddock_manager import PaddockManager
from events import Events

from UI.pygame_gui import Button
from utils import utils
from data import *
from typing import List

class Equipment:
    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect) -> None:
        self.parent_surface = parent_surface
        self.events = events
        self.rect = rect

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        