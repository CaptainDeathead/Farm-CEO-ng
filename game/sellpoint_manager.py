import pygame as pg
import logging

from save_manager import SaveManager
from sellpoints import SellPoint
from destination import Destination
from data import *

from random import uniform
from typing import List, Dict

class SellpointManager:
    # TODO: Change this on release to a more *unlockable* state
    STARTING_SILO_STORAGE = {
        "wheat": 5.0,
        "barley": 4.0,
        "canola": 3.0,
        "oat": 2.0
    }

    def __init__(self, game_surface: pg.Surface, map_scale: float) -> None:
        self.game_surface = game_surface
        self.map_scale = map_scale
        self.sellpoints = []
        self.silo = None

        self._save_sellpoints_on_load = False # Does not need to be reset if it becomes true because it should only be used on game load

        self.location_callback = None

    def init(self, sellpoints_dict: Dict[str, Dict]) -> None:
        self.load_sellpoints(sellpoints_dict)

    def generate_prices(self) -> Dict[str, float]:
        new_prices = {}

        for crop in CROP_TYPES:
            if crop == "--": continue

            price_randomness = uniform(0.85, 1.15)
            price = BASE_CROP_PRICES[CROP_IDS[crop]] * price_randomness

            new_prices[crop] = price

        return new_prices

    def load_sellpoints(self, sellpoints: Dict[str, Dict]) -> None:
        logging.debug("Loading sellpoints...")

        for sellpoint_id in sellpoints:
            raw_position = sellpoints[sellpoint_id]["location"]
            rotation = sellpoints[sellpoint_id]["rotation"]
            silo = sellpoints[sellpoint_id]["silo"]
            name = sellpoints[sellpoint_id]["name"]
            contents = sellpoints[sellpoint_id].get("contents", None)
            prices = sellpoints[sellpoint_id].get("prices", None)

            if prices is None:
                if silo:
                    if contents is None:
                        logging.warning("Silo contents not found. Generating...")
                        contents = self.STARTING_SILO_STORAGE

                        self._save_sellpoints_on_load = True
                else:
                    logging.warning("Sellpoint prices not found. Generating...")
                    prices = self.generate_prices()

                    self._save_sellpoints_on_load = True

            game_pos = (raw_position[0] * self.map_scale, raw_position[1] * self.map_scale)

            sellpoint = SellPoint(self.game_surface, raw_position, game_pos, rotation, self.map_scale, name, silo, contents, prices)
            self.sellpoints.append(sellpoint)

            if sellpoint.silo: self.silo = sellpoint

        if self._save_sellpoints_on_load:
            logging.debug("Sellpoint prices have been generated. Sending updated sellpoints to save_manager...")
            packed_sellpoints = self.pack_sellpoints()
            SaveManager().set_sellpoints(packed_sellpoints)

    def pack_sellpoints(self) -> Dict[str, Dict]:
        sellpoints_dict = {}

        for i, sellpoint in enumerate(self.sellpoints):
            sellpoints_dict[str(i)] = {
                "location": sellpoint.raw_position,
                "rotation": sellpoint.rotation,
                "silo": sellpoint.silo,
                "name": sellpoint.name,
                "contents": sellpoint.contents,
                "prices": sellpoint.prices
            }

        return sellpoints_dict

    def get_stored_amount(self, crop_type: str) -> float:
        return self.silo.contents.get(crop_type, 0)

    def get_stored_crops(self, crop_filter: List[str] = []) -> List[str]:
        stored_crops = []

        for crop, amount in self.silo.contents.items():
            if amount > 0 and (crop in crop_filter or crop_filter == []):
                stored_crops.append(crop)

        return stored_crops

    def store_crop(self, crop_type: str, amount: float) -> None:
        return self.silo.store_crop(crop_type, amount)

    def take_crop(self, crop_type: str, desired_amount: float) -> float:
        return self.silo.take_crop(crop_type, desired_amount)

    def render_grids(self) -> None:
        for sellpoint in self.sellpoints:
            sellpoint.draw_grid()

    def render_silos(self) -> None:
        for sellpoint in self.sellpoints:
            sellpoint.draw_silo()

    def check_sellpoint_clicks(self) -> SellPoint | None:
        pos = pg.mouse.get_pos()
        pos = (pos[0] - PANEL_WIDTH, pos[1])

        for sellpoint in self.sellpoints:
            pressed = sellpoint.update(pos)

            if pressed:
                return sellpoint 

    def set_location_click_callback(self, callback: callable) -> None:
        self.location_callback = callback

    def destroy_location_click_callback(self) -> None:
        self.location_callback = None

    def update(self, mouse_just_released: bool) -> None:
        for sellpoint in self.sellpoints:
            if sellpoint.pending_money > 0:
                SaveManager().add_money(sellpoint.pending_money)
                sellpoint.pending_money = 0

        if mouse_just_released and self.location_callback is not None:
            sellpoint_clicked = self.check_sellpoint_clicks()

            if sellpoint_clicked is not None:
                self.location_callback(Destination(sellpoint_clicked))