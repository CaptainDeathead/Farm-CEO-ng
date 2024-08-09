import pygame as pg
import logging

from resource_manager import ResourceManager

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)

class FarmCEO:
    RESOURCE_MANAGER: ResourceManager = ResourceManager()

    def __init__(self, screen: pg.Surface, clock: pg.time.Clock) -> None:
        self.screen: pg.Surface = screen
        self.clock: pg.time.Clock = clock
        self.map: pg.Surface = pg.image.load()