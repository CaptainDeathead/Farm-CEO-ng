import pygame as pg

from paddock import Paddock
from sellpoints import SellPoint
from utils import VarsSingleton

from typing import Tuple

class Destination:
    def __init__(self, destination: Paddock | SellPoint | None) -> None:
        self.destination = destination
        self.is_paddock = isinstance(destination, Paddock)
        self.is_shed = destination is None
        self.is_silo = False
        self.is_sellpoint = False

        if isinstance(destination, SellPoint):
            if destination.silo:
                self.is_silo = True
            else:
                self.is_sellpoint = True

        self.name = self.get_name()

    def get_name(self) -> str:
        if isinstance(self.destination, Paddock):
            return f"Paddock {self.destination.num}"
        elif isinstance(self.destination, SellPoint):
            return self.destination.name
        else:
            return "--"

    def get_pos(self) -> Tuple[int, int] | None:
        if self.is_shed:
            return VarsSingleton().shed.rect.center
        else:
            if hasattr(self.destination, 'pos'):
                return self.destination.pos
            else:
                return None