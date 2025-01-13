import pygame as pg

from paddock import Paddock
from sellpoints import SellPoint

class Destination:
    def __init__(self, destination: Paddock | SellPoint | None) -> None:
        self.destination = destination
        self.name = self.get_name()

    def get_name(self) -> str:
        if isinstance(self.destination, Paddock):
            return f"Paddock {self.destination.num}"
        elif isinstance(self.destination, SellPoint):
            return self.destination.name
        else:
            return "--"