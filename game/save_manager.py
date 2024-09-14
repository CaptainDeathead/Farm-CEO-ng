import os
import logging

from resource_manager import ResourceManager

from paddock import Paddock
from machinary import Tractor, Header, Tool
from data import *

if BUILD: from android.storage import app_storage_path
else:
    def app_storage_path() -> str:
        return "./"
    
from typing import Dict, List

class SaveManager:
    SAVE_PATH: str = os.path.join(app_storage_path(), "farmceo_savegame.json")

    def __new__(cls) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(SaveManager, cls).__new__(cls)

        return cls.instance
    
    def init(self, map_config: Dict[str, any], vehicles: List[Tractor | Header], tools: List[Tool],
             add_vehicle: callable, add_tool: callable) -> None:
        
        self.STATIC_VEHICLES_DICT = ResourceManager().load_json("Machinary/Vehicles/vehicles.json")
        self.STATIC_TOOLS_DICT = ResourceManager().load_json("Machinary/Tools/tools.json")
        
        self.money = 500_000.0 # Starting money
        self.xp = 0.0
        self.debt = 0.0 # No dept to start with
        self.time = 0.0
        
        self.vehicles = vehicles
        self.tools = tools
        
        self.add_vehicle = add_vehicle
        self.add_tool = add_tool

        self.vehicles_dict = {
            0: {
                "header": False,
                "brand": "New Holland",
                "model": "T6 145",
                "fuel": 290,
                "fill": 0,
                "fillType": -1,
                "vehicleId": 0,
                "jobId": -1,
                "completionAmount": 0,
                "workingBackwards": False
            },
            1: {
                "header": True,
                "brand": "Case IH",
                "model": "2388",
                "fuel": 700,
                "fill": 0,
                "fillType": 0,
                "vehicleId": 1,
                "jobId": -1,
                "completionAmount": 0,
                "workingBackwards": False
            }
        }
        self.tools_dict = {
            0: {
                "toolType": "Cultivators",
                "brand": "Case IH",
                "model": "490",
                "fill": 0,
                "fillType": -1,
                "toolId": 0,
                "vehicleId": -1,
                "jobId": -1
            },
            1: {
                "toolType": "Seeders",
                "brand": "John Sheerer",
                "model": "Combine 14ft",
                "fill": 0,
                "fillType": 0,
                "toolId": 1,
                "vehicleId": -1,
                "jobId": -1
            },
            2: {
                "toolType": "Trailers",
                "brand": "Marshall",
                "model": "QM-12",
                "fill": 0,
                "fillType": 0,
                "toolId": 2,
                "vehicleId": -1,
                "jobId": -1
            }
        }

        self.load_game()
        if self.save == {}: self.init_savefile(map_config)

    def _load_paddocks_from_conf(self, map_config: Dict[str, any]) -> Dict[int, any]:
        new_paddocks = {}
        for pdk in map_config["paddocks"]:
            new_paddocks[int(pdk)+1] = map_config["paddocks"][pdk]
            new_paddocks[int(pdk)+1]["owned_by"] = "npc"
            new_paddocks[int(pdk)+1]["hectares"] = map_config["paddocks"][pdk]["hectares"]

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
            "vehicles": self.vehicles_dict,
            "tools": self.tools_dict
        }

        new_save["paddocks"] = self._load_paddocks_from_conf(map_config)

        self.save = new_save
        self.save_game(update_equipment_dicts = False)
        self.load_game()

    def load_game(self) -> None:
        logging.debug(f"Loading savegame file: \"{self.SAVE_PATH}\"...")
        self.save = ResourceManager.load_json(self.SAVE_PATH, explicit_path=True)

        if self.save == {}: return # will create one and load values

        self.money = self.save["money"]
        self.xp = self.save["xp"]
        self.debt = self.save["debt"]
        self.time = self.save["time"]
        self.vehicles_dict = self.save["vehicles"]
        self.tools_dict = self.save["tools"]

        self.load_equipment_from_dicts()

    def save_game(self, update_equipment_dicts: bool = True) -> None:
        if update_equipment_dicts:
            self.get_vehicles_dict()
            self.get_tools_dict()
        
        self.set_attr("money", self.money)
        self.set_attr("xp", self.xp)
        self.set_attr("debt", self.debt)
        self.set_attr("time", self.time)
        self.set_attr("vehicles", self.vehicles_dict)
        self.set_attr("tools", self.tools_dict)

        logging.debug(f"Writing savegame file: \"{self.SAVE_PATH}\"...")
        ResourceManager.write_json(self.save, self.SAVE_PATH, explicit_path=True)

    def create_vehicle(self, header: bool, brand: str, model: str, ) -> None:
        if header:
            static_conf = self.STATIC_VEHICLES_DICT["Harvesters"][brand][model]
            vehicle = {
                "header": True,
                "brand": brand,
                "model": model,
                "fuel": static_conf["max_fuel"],
                "fill": 0,
                "fillType": 0,
                "vehicleId": len(self.vehicles),
                "jobId": -1,
                "completionAmount": 0,
                "workingBackwards": False
            }
        else:
            static_conf = self.STATIC_VEHICLES_DICT["Tractors"][brand][model]
            vehicle = {
                "header": False,
                "brand": brand,
                "model": model,
                "fuel": static_conf["max_fuel"],
                "fill": 0,
                "fillType": -1,
                "vehicleId": len(self.vehicles),
                "jobId": -1,
                "completionAmount": 0,
                "workingBackwards": False
            }

        self.add_vehicle(vehicle)

    def create_tool(self, tool_type: str, brand: str, model: str) -> None:
        tool = {
            "toolType": tool_type,
            "brand": brand,
            "model": model,
            "fill": 0,
            "fillType": 0,
            "toolId": len(self.tools),
            "vehicleId": -1,
            "jobId": -1
        }
        
        self.add_tool(tool)

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

    def load_equipment_from_dicts(self) -> None:
        # Cannot reassign these lists because they are references to the shed lists
        for existing_vehicle in self.vehicles: self.vehicles.remove(existing_vehicle)
        for existing_tool in self.tools: self.tools.remove(existing_tool)

        for vehicle in self.vehicles_dict:
            self.add_vehicle(self.vehicles_dict[vehicle])

        for tool in self.tools_dict:
            self.add_tool(self.tools_dict[tool])
            
    def get_vehicles_dict(self) -> Dict[str, any]:
        self.vehicles_dict = {}

        for vehicle in self.vehicles:
            self.vehicles_dict[vehicle.vehicle_id] = {
                "header": isinstance(vehicle, Header),
                "brand": vehicle.brand,
                "model": vehicle.model,
                "fuel": vehicle.fuel,
                "fill": vehicle.fill,
                "fillType": vehicle.fill_type,
                "vehicleId": vehicle.vehicle_id,
                "jobId": vehicle.job_id,
                "completionAmount": vehicle.completion_amount,
                "workingBackwards": vehicle.working_backwards
            }

        return self.vehicles_dict

    def get_tools_dict(self) -> Dict[str, any]:
        self.tools_dict = {}

        for tool in self.tools:
            self.tools_dict[tool.tool_id] = {
                "brand": tool.brand,
                "model": tool.model,
                "fill": tool.fill,
                "fillType": tool.fill_type,
                "toolId": tool.tool_id,
                "vehicleId": tool.vehicle_id,
                "jobId": tool.job_id
            }
        
        return self.tools_dict