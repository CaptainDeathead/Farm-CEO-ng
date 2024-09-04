import pygame as pg
import os
import logging
import traceback

from data import *
from paddock import Paddock

if BUILD: from android.storage import app_storage_path
else:
    def app_storage_path() -> str:
        return "./"

from json import loads, dumps, JSONDecodeError
from typing import Tuple, Dict, List

class ResourceManager:
    """
    Manager for all resources.
    
    Manages:
        - Where images and other assets are stored
        - How to load images and assets
        - How to write assets
    """

    PATH: str = os.path.abspath('.')
    ASSETS_PATH: str = f"{PATH}/assets"
    DATA_PATH: str = f"{ASSETS_PATH}/Data"
    MAPS_PATH: str = f"{DATA_PATH}/Maps"

    @staticmethod
    def _fmt_read_error(obj_type: str, obj_path: str, err_msg: str) -> str:
        return f"Error while loading {obj_type}!\n  {obj_type}: \"{obj_path}\"\n  Error: \"{err_msg}\""
    
    @staticmethod
    def _fmt_write_error(obj_type: str, obj_path: str, err_msg: str) -> str:
        return f"Error while writing {obj_type}!\n  {obj_type}: \"{obj_path}\"\n  Error: \"{err_msg}\""

    @staticmethod
    def load_image(image_path: str, expected_size: Tuple[int, int] = (10, 10)) -> pg.Surface:
        """image_path: str (relative to `DATA_PATH`)"""

        image = pg.Surface(expected_size)

        try:
            image = pg.image.load(f"{ResourceManager.DATA_PATH}/{image_path}").convert_alpha()

        except pg.error as message:
            pg.draw.rect(image, (255, 0, 0), (0, 0, expected_size[0], expected_size[1])) # Red rectangle to show image load error to user
            logging.error(traceback.format_exc())
            logging.error(ResourceManager._fmt_read_error("image", image_path, message))

        except OSError as e:
            pg.draw.rect(image, (255, 0, 0), (0, 0, expected_size[0], expected_size[1])) # Red rectangle to show image load error to user
            logging.error(traceback.format_exc())
            logging.error(ResourceManager._fmt_read_error("image", image_path, e))

        return image
    
    @staticmethod
    def load_text_file(file_path: str, explicit_path: bool = False) -> str:
        """file_path: str (relative to `DATA_PATH`)"""

        contents = ""

        full_file_path = ""

        if explicit_path: full_file_path = file_path
        else: full_file_path = f"{ResourceManager.DATA_PATH}/{file_path}"

        try:
            with open(full_file_path, "r") as text_file:
                contents = text_file.read()

        except OSError as e:
            logging.error(traceback.format_exc())
            logging.error(ResourceManager._fmt_read_error("file", full_file_path, e))

        return contents
    
    @staticmethod
    def write_text_file(contents: str, file_path: str, explicit_path: bool = False) -> bool:
        """
        file_path: str (relative to `DATA_PATH`)

        returns -> success status
        """

        success = False

        full_file_path = ""
        
        if explicit_path: full_file_path = file_path
        else: full_file_path = f"{ResourceManager.DATA_PATH}/{file_path}"

        try:
            with open(full_file_path, "w") as text_file:
                text_file.write(contents)
        
        except OSError as e:
            logging.error(traceback.format_exc())
            logging.error(ResourceManager._fmt_write_error("file", full_file_path, e))
            return success
        
        success = True

        return success
    
    @staticmethod
    def load_json(json_path: str, explicit_path: bool = False) -> Dict[any, any]:
        """json_path: str (relative to `DATA_PATH`)"""

        json = {}

        full_json_path = ""

        if explicit_path: full_json_path = json_path
        else: full_json_path = f"{ResourceManager.DATA_PATH}/{json_path}"

        try:
            json = loads(ResourceManager.load_text_file(full_json_path, explicit_path=True))

        except JSONDecodeError as e:
            logging.error(traceback.format_exc())
            logging.error(ResourceManager._fmt_read_error("json", full_json_path, e.msg))

        return json
    
    @staticmethod
    def write_json(py_dict: Dict[any, any], json_path: str, explicit_path: bool = False) -> bool:
        """
        json_path: str (relative to `DATA_PATH`)

        returns -> success
        """

        success = False

        full_json_path = ""

        if explicit_path: full_json_path = json_path
        else: full_json_path = f"{ResourceManager.DATA_PATH}/{json_path}"

        try:
            json_str = dumps(py_dict)
        except JSONDecodeError as e:
            logging.error(traceback.format_exc())
            logging.error(ResourceManager._fmt_write_error("json", full_json_path, e.msg))
            return success

        success = ResourceManager.write_text_file(json_str, full_json_path, explicit_path=True)

        return success
    
    @staticmethod
    def load_map(map_name: str) -> Tuple[pg.Surface, Dict[str, any]]:
        """map_name: str (relative to `MAPS_PATH`)"""

        map_cfg = ResourceManager.load_json(f"Maps/{map_name}")

        if map_cfg == {}:
            logging.error(traceback.format_exc())
            logging.error(ResourceManager._fmt_read_error("map config", map_name, "Map configuration file does not exist or its configuration is invalid!"))
            return (ResourceManager.load_image("", (1000, 1000)), {}) # return blank map

        map_file = map_cfg.get("filename", "")

        return (ResourceManager.load_image(f"Maps/{map_file}", (1000, 1000)), map_cfg)
    
class SaveManager:
    SAVE_PATH: str = os.path.join(app_storage_path(), "farmceo_savegame.json")

    def __new__(cls) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(SaveManager, cls).__new__(cls)

        return cls.instance
    
    def init(self, map_config: Dict[str, any]) -> None:
        self.money = 500_000.0 # Starting money
        self.xp = 0.0
        self.debt = 0.0 # No dept to start with
        self.time = 0.0
        self.vehicles = {
            0: {
                "header": False,
                "brand": "New Holland",
                "model": "T6 145",
                "fuel": 290
            },
            1: {
                "header": True,
                "brand": "Case IH",
                "model": "2388",
                "fuel": 700
            }
        }
        self.tools = {
            0: {
                "toolType": "Cultivators",
                "brand": "Case IH",
                "model": "490"
            },
            1: {
                "toolType": "Seeders",
                "brand": "John Sheerer",
                "model": "Combine 14ft"
            },
            2: {
                "toolType": "Trailers",
                "brand": "Marshall",
                "model": "QM-12"
            }
        }

        self.load_game()
        if self.save == {}: self.init_savefile(map_config)

    def _load_paddocks_from_conf(self, map_config: Dict[str, any]) -> Dict[int, any]:
        new_paddocks = {}
        for pdk in map_config["paddocks"]:
            new_paddocks[int(pdk)+1] = map_config["paddocks"][pdk]

        return new_paddocks

    def init_savefile(self, map_config: Dict[str, any]) -> None:
        self.new_savefile = True

        if map_config == {}:
            raise Exception("Map configuration is EMPTY! Please provide a valid map config in the arguments when creating a new save.")
        
        new_save = {
            "map_name": map_config["name"],
            "money": self.money, # Starting money
            "xp": self.xp,
            "debt": 0.0, # No dept to start with
            "time": 0.0,
            "vehicles": self.vehicles,
            "tools": self.tools
        }

        new_save["paddocks"] = self._load_paddocks_from_conf(map_config)

        self.save = new_save
        self.save_game()
        self.load_game()

    def load_game(self) -> None:
        self.save = ResourceManager.load_json(self.SAVE_PATH, explicit_path=True)

        if self.save == {}: return # will create one and load values

        self.money = self.save["money"]
        self.xp = self.save["xp"]
        self.debt = self.save["debt"]
        self.time = self.save["time"]
        self.vehicles = self.save["vehicles"]
        self.tools = self.save["tools"]

    def save_game(self) -> None:
        self.set_attr("money", self.money)
        self.set_attr("xp", self.xp)
        self.set_attr("debt", self.debt)
        self.set_attr("time", self.time)
        self.set_attr("vehicles", self.vehicles)
        self.set_attr("tools", self.tools)

        ResourceManager.write_json(self.save, self.SAVE_PATH, explicit_path=True)

    def set_money(self, new_money: float) -> None:
        self.money = new_money

    def get_attr(self, attr_name: str) -> any:
        return self.save[attr_name]
    
    def set_attr(self, attr_name: str, value: any) -> None:
        self.save[attr_name] = value

    def get_paddocks(self) -> Dict[int, any]:
        return self.get_attr("paddocks")
    
    def set_paddocks(self, paddocks: List[Paddock]) -> None:
        paddocks_dict = {}

        for paddock in paddocks:
            paddocks_dict[paddock.num] = paddock.__dict__()

        self.set_attr("paddocks", paddocks_dict)

    def add_vehicle(self, header: bool, brand: str, model: str, fuel: int) -> None:
        self.vehicles[len(self.vehicles)] = {"header": header, "brand": brand, "model": model, "fuel": fuel}

    def add_tool(self, tool_type: str, brand: str, model: str) -> None:
        self.tools[len(self.tools)] = {"toolType": tool_type, "brand": brand, "model": model}