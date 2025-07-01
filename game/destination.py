import pygame as pg

from paddock import Paddock
from sellpoints import SellPoint
from utils import VarsSingleton

from typing import Tuple, Dict
from typing_extensions import Self

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
        self.load_destination_required = False

    @staticmethod
    def from_dict(dest_dict: Dict[str, any]) -> Self:
        dest = Destination(None)

        if dest_dict is None: return dest

        dest.is_paddock = dest_dict["is_paddock"]
        dest.is_shed = dest_dict["is_shed"]
        dest.is_silo = dest_dict["is_silo"]
        dest.is_sellpoint = dest_dict["is_sellpoint"]
        
        if dest.is_paddock:
            dest.load_destination_required = True
            dest.paddock_num = dest_dict["paddock_num"]

        elif dest.is_sellpoint or dest.is_silo:
            dest.load_destination_required = True
            dest.sellpoint_name = dest_dict["sellpoint_name"]

        return dest

    def to_dict(self) -> Dict[str, any]:
        ret_dict = {
            "is_paddock": self.is_paddock,
            "is_shed": self.is_shed,
            "is_silo": self.is_silo,
            "is_sellpoint": self.is_sellpoint
        }

        if self.is_paddock:
            ret_dict["paddock_num"] = self.destination.num
        elif self.is_silo or self.is_sellpoint:
            ret_dict["sellpoint_name"] = self.destination.name

        return ret_dict

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