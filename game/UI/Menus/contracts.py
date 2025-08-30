import pygame as pg
import logging

from UI.pygame_gui import Button
from UI.popups import OKCancelPopup
from paddock_manager import PaddockManager
from save_manager import SaveManager
from resource_manager import ResourceManager
from events import Events
from data import *
from utils import utils

from random import randint
from typing import Dict

class Contract:
    def __init__(self, contract_id: int, paddock_num: int) -> None:
        self.contract_id = contract_id
        self.paddock_num = paddock_num
        self.paddock = PaddockManager().paddocks[self.paddock_num-1]

        self.required_state = self.paddock.state
        self.required_machine, self.required_fill_type, self.reward, self.fail_cost = self.get_contract_info()

        self.contract_type = TOOL_ACTIVE_NAMES.get(self.required_machine)

        self.active = False

    @property
    def invalid(self) -> bool:
        # Returns True if the contract isn't valid (nothing to do)
        return self.required_machine is None and self.required_fill_type is None and self.reward is None and self.fail_cost is None

    def to_dict(self) -> Dict[str, any]:
        ret_dict = {
            # contract_id doesnt need to be here because it would be the key in the parent dict in the save file
            "paddock_num": self.paddock_num,
            "active": self.active
        }

        return ret_dict

    def activate_reward(self) -> None:
        SaveManager().add_money(self.reward)
    
    def activate_fail(self) -> None:
        SaveManager().take_money(self.fail_cost)

    def get_contract_info(self) -> tuple[str, int]:
        if self.paddock.state == 0:
            if self.paddock.lime_years == 0:
                if randint(0, 1) == 0:
                    return "Spreaders", FILL_TYPES.index("lime"), self.paddock.hectares * 10, 500

            return "Cultivators", -1, self.paddock.hectares * 20, 500

        elif self.paddock.state == 1:
            if self.paddock.lime_years == 0:
                return "Spreaders", FILL_TYPES.index("lime"), self.paddock.hectares * 10, 500
            
            return "Seeders", randint(0, len(CROP_TYPES)-1), self.paddock.hectares * 30, 500

        elif self.paddock.state in (2, 3):
            if not self.paddock.super_spreaded: # TODO: This will probably always get used over the last 2 on stage 2 because it will be the first in line of the 3.
                return "Spreaders", FILL_TYPES.index("super"), self.paddock.hectares * 10, 500
            if not self.paddock.urea_spreaded: # TODO: This will probably always get take over weeds on the 3rd stage if the super contract was done on the 2nd stage.
                return "Spreaders", FILL_TYPES.index("urea"), self.paddock.hectares * 10, 500
            if self.paddock.weeds:
                return "Sprayers", FILL_TYPES.index("herbicide"), self.paddock.hectares * 20, 1000

            return None, None, None, None

        elif self.paddock.state == 5:
            return "Headers", self.paddock.crop_index, self.paddock.hectares * 30, 500

        else:
            logging.warning(f"Paddock state {self.paddock.state} not found in logic.")
            return None, None, None, None

    def get_contract_requirements(self) -> Dict[str, any]:
        if self.required_machine in ("Spreaders", "Sprayers"):
            if self.required_fill_type == FILL_TYPES.index("lime"): return {"lime": 3}
            if self.required_fill_type == FILL_TYPES.index("super"): return {"super": True}
            if self.required_fill_type == FILL_TYPES.index("urea"): return {"urea": True}
            if self.required_fill_type == FILL_TYPES.index("herbicide"): return {"weeds": 0}
            else:
                logging.error(f"Unknown fill type requirement for contract: {self.contract_id}! {self.required_fill_type=}")
                return # Cause exception

        elif self.required_machine == "Cultivators": return {"state": 1}
        elif self.required_machine == "Seeders": return {"state": 2, "crop": self.required_fill_type}
        elif self.required_machine == "Headers": return {"state": 0}
        else:
            logging.error(f"Unknown machine type requirement for contract: {self.contract_id}! {self.required_machine=}")

class Contracts:
    BUTTON_WIDTH = PANEL_WIDTH - 40

    def __init__(self, parent_surface: pg.Surface, events: Events, rect: pg.Rect, set_popup: object) -> None:
        self.parent_surface = parent_surface
        self.events = events

        self.rect = rect
        self.rect.y += 20

        self.set_popup = set_popup

        self.paddock_manager = PaddockManager()

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        self.scrollable_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.title_font = pg.font.SysFont(None, 60)
        self.body_font = pg.font.SysFont(None, 40)

        self.contracts = []

        self.contract_buttons = []
        self.og_contract_button_rects = []

        self.scroll_y = 0.0
        self.max_y = 0.0
        self.scrolling_last_frame = False
        self.in_scroll = False

        self.active = False
        self.redraw_required = False
        self.in_popup = False

        if SaveManager().contracts == {}:
            logging.info(f"Contracts save is empty! Generating new contracts... (Warning: Could cause desync if paddocks have states corresponding to contracts still)")
            self.generate_contracts()
        else:
            self.from_dict(SaveManager().contracts)

    def to_dict(self) -> Dict[str, int]:
        ret_dict = {}

        for contract in self.contracts:
            ret_dict[contract.contract_id] = contract.to_dict()

        return ret_dict

    def from_dict(self, dest_dict: Dict[str, int]) -> None:
        logging.debug(f"Loading contracts from save dict...")

        for contract_id, contract_info in dest_dict.items():
            contract = Contract(contract_id, contract_info["paddock_num"])
            contract.active = contract_info["active"]
            self.contracts.append(contract)

        self.rebuild()

    def accept_contract(self, contract: Contract) -> None:
        if contract.active:
            logging.warning(f"Cannot accept contract! Contract already active.")
            return

        logging.info(f"Accepted contract {contract.contract_id} on paddock {contract.paddock.num}.")

        contract.active = True
        contract.paddock.set_contract(contract.get_contract_requirements())

        SaveManager().set_contracts(self.to_dict())

        self.in_popup = False
        self.rebuild()

    def cancel_contract_accept(self) -> None:
        self.set_popup(None)
        self.in_popup = False

    def trigger_contract_popup(self, contract: Contract) -> None:
        logging.info("Creating contract accept popup...")

        if self.in_popup:
            logging.warning("Already in popup! Refusing to make a new one.")
            return
        elif contract.active:
            logging.warning("Contract already active! Refusing to make a new popup.")
            return

        self.in_popup = True
        self.set_popup(OKCancelPopup(self.events, self.cancel_contract_accept, lambda: self.accept_contract(contract), "Accept Contract", f"Are you sure you wish to accept this contract on paddock {contract.paddock.num}?"))

    def rebuild(self) -> None:
        logging.debug("Rebuilding contracts menu...")

        self.rendered_surface.fill(UI_BACKGROUND_COLOR)
        self.contract_buttons = []
        self.og_contract_button_rects = []
        
        center = PANEL_WIDTH / 2

        button_height = 160
        button_spacing = 20

        y_inc = button_height + button_spacing

        self.scrollable_surface = pg.Surface((self.rect.w, (len(self.contracts)) * (y_inc + 30)), pg.SRCALPHA)

        x, y = center - self.BUTTON_WIDTH / 2, 0

        for contract in self.contracts:
            button = Button(self.scrollable_surface, x, y, self.BUTTON_WIDTH, button_height, self.rect, UI_MAIN_COLOR, pg.Color(255, 100, 0), UI_TEXT_COLOR, "",
                            20, (20, 20, 20, 20), 0, 0, command=lambda contract=contract: self.trigger_contract_popup(contract), authority=True)

            if contract.active:
                button.set_color(pg.Color(255, 150, 0), True)

            button.draw()
            self.contract_buttons.append(button)
            self.og_contract_button_rects.append(button.global_rect)

            title_lbl = self.title_font.render(f"{contract.contract_type.capitalize()} at paddock {contract.paddock.num}", True, UI_TEXT_COLOR)
            self.scrollable_surface.blit(title_lbl, (60, y + 10))

            material_int = contract.required_fill_type
            if material_int == -1: material = "N/A"
            else: material = FILL_TYPES[material_int].capitalize()

            self.scrollable_surface.blit(self.body_font.render(f"Material: {material}", True, UI_TEXT_COLOR), (60, y + 50))
            self.scrollable_surface.blit(self.body_font.render(f"Reward: ${contract.reward}", True, UI_TEXT_COLOR), (60, y + 80))
            self.scrollable_surface.blit(self.body_font.render(f"Fail cost: ${contract.fail_cost}", True, pg.Color(255, 0, 0)), (60, y + 110))

            y += y_inc

        self.max_y = y
        self.redraw_required = True

    def generate_contracts(self) -> None:
        self.contracts = []

        for paddock in self.paddock_manager.paddocks:
            if randint(0, 4) == 0 or paddock.owned_by == "player" or paddock.state == 5: continue # TODO: Currently disabled harvest contracts because they are not fully working

            contract = Contract(len(self.contracts)+1, int(paddock.num))

            if not contract.invalid:
                self.contracts.append(contract)

        SaveManager().set_contracts(self.to_dict())
        self.rebuild()

    def check_paddocks_fulfillment(self, fail_if_not_done: bool = False) -> None:
        for contract in self.contracts:
            if contract.paddock.contract_fulfilled:
                logging.info(f"Contract on paddock {contract.paddock.num} fulfilled!")

                contract.activate_reward()
                contract.paddock.reset_contract()
                self.contracts.remove(contract)

                SaveManager().set_contracts(self.to_dict())
                self.rebuild()

            elif contract.paddock.contract_failed or fail_if_not_done:
                logging.info(f"Contract on paddock {contract.paddock.num} failed!")

                contract.activate_fail()
                contract.paddock.reset_contract()
                self.contracts.remove(contract)

                SaveManager().set_contracts(self.to_dict())
                self.rebuild()

    def update(self) -> bool:
        # This is pretty much an exact copy of the equipment update code so for more detail on how it works visit equipment.py update function
        redraw_required = self.redraw_required
        self.redraw_required = False

        for i, button in enumerate(self.contract_buttons):
            og_button_rect = self.og_contract_button_rects[i]
            button.global_rect = pg.Rect(og_button_rect.x, og_button_rect.y + self.scroll_y, og_button_rect.width, og_button_rect.height)

            if not self.in_scroll and self.events.mouse_pos[1] > NAVBAR_HEIGHT:
                button_press = self.events.authority_mouse_just_pressed and button.global_rect.collidepoint(self.events.authority_mouse_start_press_location)
                button.update(button_press, lambda x: None)

        if self.in_scroll and self.events.authority_mouse_just_released:
            self.in_scroll = False

        if pg.mouse.get_pressed()[0] and self.rect.collidepoint(pg.mouse.get_pos()):
            if not self.scrolling_last_frame: pg.mouse.get_rel()
            rx, ry = pg.mouse.get_rel()

            if (abs(rx) > 10 and abs(ry) > 10) or abs(ry) <= 2:
                self.scrolling_last_frame = True
                return False or redraw_required
            
            self.in_scroll = True

            height = self.rendered_surface.get_height()
            if self.max_y > height:
                new_scroll_y = self.scroll_y + ry
                self.scroll_y = min(0, max((self.max_y - height + 40) * -1, new_scroll_y))

                self.scrolling_last_frame = True
                return True
        
        self.scrolling_last_frame = pg.mouse.get_pressed()[0]
        return False or redraw_required

    def draw(self, rebuild: bool = False) -> None:
        if rebuild:
            self.rebuild()

        self.rendered_surface.fill(UI_BACKGROUND_COLOR)
        self.rendered_surface.blit(self.scrollable_surface, (0, self.scroll_y))

        if self.active:
            self.parent_surface.blit(self.rendered_surface, self.rect)