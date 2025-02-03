import pygame as pg
import logging

from save_manager import SaveManager
from sellpoints import SellPoint
from data import *

from random import uniform
from typing import Dict

class SellpointManager:
    def __init__(self, game_surface: pg.Surface, map_scale: float, sellpoints_dict: Dict[str, Dict]) -> None:
        self.game_surface = game_surface
        self.map_scale = map_scale
        self.sellpoints = []

        self._save_sellpoints_on_load = False # Does not need to be reset if it becomes true because it should only be used on game load

        self.load_sellpoints(sellpoints_dict)

    def generate_prices(self) -> Dict[str, float]:
        new_prices = {}

        for crop in CROP_TYPES:
            price_randomness = uniform(0.85, 1.15)
            price = BASE_CROP_PRICES[CROP_IDS[crop]] * price_randomness

            new_prices[crop] = price

        return new_prices

    def load_sellpoints(self, sellpoints: Dict[str, Dict]) -> None:
        logging.debug("Loading sellpoints...")

        for sellpoint_id in sellpoints:
            position = sellpoints[sellpoint_id]["location"]
            rotation = sellpoints[sellpoint_id]["rotation"]
            silo = sellpoints[sellpoint_id]["silo"]
            name = sellpoints[sellpoint_id]["name"]
            contents = sellpoints[sellpoint_id].get("contents", {})
            prices = sellpoints[sellpoint_id].get("prices", {})

            if prices == {} and not silo:
                logging.warning("Sellpoint prices not found. Generating...")
                prices = self.generate_prices()

                self._save_sellpoints_on_load = True

            sellpoint = SellPoint(self.game_surface, position, rotation, self.map_scale, name, silo, contents, prices)
            self.sellpoints.append(sellpoint)

        if self._save_sellpoints_on_load:
            logging.debug("Sellpoint prices have been generated. Sending updated sellpoints to save_manager...")
            packed_sellpoints = self.pack_sellpoints()
            SaveManager().set_sellpoints(packed_sellpoints)

    def pack_sellpoints(self) -> Dict[str, Dict]:
        sellpoints_dict = {}

        for i, sellpoint in enumerate(self.sellpoints):
            sellpoints_dict[str(i)] = {
                "location": sellpoint.pos,
                "rotation": sellpoint.rotation,
                "silo": sellpoint.silo,
                "name": sellpoint.name,
                "contents": sellpoint.contents,
                "prices": sellpoint.prices
            }

        return sellpoints_dict