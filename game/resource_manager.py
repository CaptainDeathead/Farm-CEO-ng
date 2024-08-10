import pygame as pg
import os
import logging

from json import loads, dumps, JSONDecodeError
from typing import Tuple, Dict

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

    def load_image(self, image_path: str, expected_size: Tuple[int, int] = (10, 10)) -> pg.Surface:
        """image_path: str (relative to `DATA_PATH`)"""

        image = pg.Surface(expected_size)

        try:
            image = pg.image.load(f"{self.DATA_PATH}/{image_path}").convert_alpha()

        except pg.error as message:
            pg.draw.rect(image, (255, 0, 0), (0, 0, expected_size[0], expected_size[1])) # Red rectangle to show image load error to user
            logging.error(self._fmt_read_error("image", image_path, message))

        except OSError as e:
            pg.draw.rect(image, (255, 0, 0), (0, 0, expected_size[0], expected_size[1])) # Red rectangle to show image load error to user
            logging.error(self._fmt_read_error("image", image_path, e))

        return image
    
    def load_text_file(self, file_path: str) -> str:
        """file_path: str (relative to `DATA_PATH`)"""

        contents = ""

        try:
            with open(f"{self.DATA_PATH}/{file_path}", "r") as text_file:
                contents = text_file.read()

        except OSError as e:
            logging.error(self._fmt_read_error("file", file_path, e))

        return contents
    
    def write_text_file(self, contents: str, file_path: str) -> bool:
        """
        file_path: str (relative to `DATA_PATH`)

        returns -> success status
        """

        success = False

        try:
            with open(f"{self.DATA_PATH}/{file_path}", "w") as text_file:
                text_file.write(contents)
        
        except OSError as e:
            logging.error(self._fmt_write_error("file", file_path, e))
            return success
        
        success = True

        return success
    
    def load_json(self, json_path: str) -> Dict[any, any]:
        """json_path: str (relative to `DATA_PATH`)"""

        json = {}

        try:
            with open(f"{self.DATA_PATH}/{json_path}", "r") as json_file:
                json = loads(json_file.read())

        except JSONDecodeError as e:
            logging.error(self._fmt_read_error("json", json_path, e.msg))

        return json
    
    def write_json(self, py_dict: Dict[any, any], json_path: str) -> bool:
        """
        json_path: str (relative to `DATA_PATH`)

        returns -> success
        """

        success = False

        try:
            json_str = dumps(py_dict)
        except JSONDecodeError as e:
            logging.error(self._fmt_write_error("json", json_path, e.msg))
            return success

        success = self.write_text_file(self, json_str, json_path)

        return success
    
    def load_map(self, map_name: str) -> Tuple[pg.Surface, Dict[str, any]]:
        """map_name: str (relative to `MAPS_PATH`)"""

        map_cfg = self.load_json(f"Maps/{map_name}")

        if map_cfg == {}:
            logging.error(self._fmt_read_error("map config", map_name, "Map configuration file does not exist or its configuration is invalid!"))
            return (self.load_image("", (1000, 1000)), {}) # return blank map

        map_file = map_cfg.get("filename", "")

        return (self.load_image(map_file, (1000, 1000)), map_cfg)