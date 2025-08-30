import pygame as pg
import logging

from resource_manager import ResourceManager

from random import randint
from typing import Dict, List, Tuple
from data import *

class Paddock:
    def __init__(self, attrs: Dict[int, any], num: str, scale: float, map_paddocks_surf: pg.Surface) -> None:
        self.attrs = attrs
        self.num = num
        self.scale = scale
        self.map_paddocks_surf = map_paddocks_surf
        self.state: int = attrs.get("state", randint(0, 5))
        self.owned_by: str = attrs["owned_by"]
        self.hectares: int = attrs["hectares"]

        color = (255, 255, 255)
        if self.owned_by == "player": color = (0, 0, 255)

        self.number_surface = pg.font.SysFont(None, 80).render(str(self.num), True, color)
        self.needs_lime_surface = pg.font.SysFont(None, 30).render("Needs lime", True, (255, 0, 0))
        self.needs_super_surface = pg.font.SysFont(None, 30).render("Needs super", True, (255, 0, 0))
        self.needs_urea_surface = pg.font.SysFont(None, 30).render("Needs urea", True, (255, 0, 0))
        self.needs_herbicide_surface = pg.font.SysFont(None, 30).render("Needs herbicide", True, (255, 0, 0))

        cx, cy = attrs["center"]
        gx, gy = attrs["gate"]

        self.center = (int(cx * scale), int(cy * scale))
        self.gate = (int(gx * scale), int(gy * scale))

        self.boundary: List[Tuple] = attrs.get("boundary", [])
        self.is_painting: bool = False

        self.state_changed = False
        self.last_collision_count = 0

        self.lime_years = attrs.get("lime_years", 3) # Years until lime runs out
        self.super_spreaded = attrs.get("super_spreaded", True)
        self.urea_spreaded = attrs.get("urea_spreaded", True)
        self.weeds = attrs.get("weeds", randint(0, 2))

        self.crop_index = attrs.get("crop_type", randint(0, len(CROP_TYPES)-1)) # Default to wheat

        self.contract_requirements = attrs.get("contract_requirements", {})
        self.contract_fulfilled = attrs.get("contract_fulfilled", False) # I dont think this needs to be saved because the Contracts UI class should pick it up in the same tick (before game quits) so there should be no desync
        self.contract_failed = attrs.get("contract_failed", False)

    @property
    def price(self) -> int:
        return self.hectares * 1200 * 2
        #return self.mask.count() * 2

    def init_collision(self) -> None:
        self.surface, self.rect = self.create_surface()
        self.localised_boundary = self.localise_boundary()

        # Fill the paddock red so the mask can see the red pixels
        self.fill(pg.Color(255, 0, 0))
        self.mask = pg.mask.from_surface(self.surface)

        self.paint_surface = pg.Surface(self.rect.size, pg.SRCALPHA)
        self.paint_mask = pg.mask.from_surface(self.paint_surface)

    def __dict__(self) -> Dict[str, any]:
        return {
            "center": self.attrs["center"],
            "gate": self.attrs["gate"],
            "state": self.state,
            "hectares": self.hectares,
            "owned_by": self.owned_by,
            "lime_years": self.lime_years,
            "super_spreaded": self.super_spreaded,
            "urea_spreaded": self.urea_spreaded,
            "weeds": self.weeds,
            "crop_type": self.crop_index,
            "contract_requirements": self.contract_requirements,
            "contract_fulfilled": self.contract_fulfilled,
            "contract_failed": self.contract_failed
        }

    def save_paint_surface(self, save_path: str) -> None:
        full_path = f"{save_path}/{self.num}_paint_surface.png"

        logging.info(f"Saving paddock paint surface to: {full_path}")
        pg.image.save(self.paint_surface, full_path)

    def load_paint_surface(self, save_path: str) -> None:
        full_path = f"{save_path}/{self.num}_paint_surface.png"

        logging.info(f"Loading paddock paint surface from: {full_path}")
        self.paint_surface = ResourceManager.load_image(full_path, expected_size=(10, 10), explicit_path=True)
    
    def rebuild_num(self) -> None:
        color = (255, 255, 255)
        if self.owned_by == "player": color = (0, 0, 255)
        
        self.number_surface = pg.font.SysFont(None, 80).render(str(self.num), True, color)
    
    def set_boundary(self, boundary: List[Tuple]) -> None:
        self.boundary = boundary

    def create_surface(self) -> tuple[pg.Surface, pg.Rect]:
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = 0, 0

        for coord in self.boundary:
            if coord[0] < min_x: min_x = coord[0]
            if coord[0] > max_x: max_x = coord[0]

            if coord[1] < min_y: min_y = coord[1]
            if coord[1] > max_y: max_y = coord[1]

        buffer = 2 # Just a bit more room in case calculation isnt the most accurate

        width, height = max_x - min_x + buffer, max_y - min_y + buffer
        surface = pg.Surface((width, height), pg.SRCALPHA)
        rect = pg.Rect(min_x, min_y, width, height)

        return surface, rect

    def localise_boundary(self) -> list[tuple]:
        return [(coord[0] - self.rect.x, coord[1] - self.rect.y) for coord in self.boundary]

    def draw_to_map(self, draw_normal_surface: bool = True, draw_paint_surface: bool = False) -> None:
        if draw_normal_surface:
            self.map_paddocks_surf.blit(self.surface, self.rect)

        if draw_paint_surface:
            self.map_paddocks_surf.blit(self.paint_surface, self.rect)

    def fill(self, color: pg.Color) -> None:
        pg.draw.polygon(self.surface, color, self.localised_boundary)
        self.draw_to_map()

    def calculate_yield(self) -> float:
        """Returns a yield bonus percent"""

        crop_yield = CROP_YIELDS[self.crop_index]
        return ((2.0 + int(self.lime_years > 0) + int(self.super_spreaded) + int(self.urea_spreaded)) / (self.weeds + 1)) * crop_yield * 2 # Division by 0

    def is_lime_spreadable(self) -> bool:
        return self.state in LIME_STAGES and self.lime_years > 0

    def is_super_spreadable(self) -> bool:
        return self.state in FERTILISER_STAGES and not self.super_spreaded

    def is_urea_spreadable(self) -> bool:
        return self.state in FERTILISER_STAGES and not self.urea_spreaded
    
    def is_herbicide_sprayable(self) -> bool:
        return self.state in FERTILISER_STAGES and self.weeds > 0

    def set_contract(self, contract_requirements: Dict[str, any]) -> None:
        logging.debug(f"Contract received on paddock {self.num}.")

        self.contract_requirements = contract_requirements
        self.contract_fulfilled = False
        self.contract_failed = False

    def reset_contract(self) -> None:
        self.contract_requirements = {}
        self.contract_fulfilled = False
        self.contract_failed = False

    def check_contract_fulfill(self) -> None:
        required_state = self.contract_requirements.get("state")
        required_lime = self.contract_requirements.get("lime")
        required_super = self.contract_requirements.get("super")
        required_urea = self.contract_requirements.get("urea")
        required_weeds = self.contract_requirements.get("weeds")
        required_crop = self.contract_requirements.get("crop")

        self.contract_failed = True

        if required_state is not None and required_state != self.state: return
        if required_lime is not None and required_lime != self.lime_years: return
        if required_super is not None and required_super != self.super_spreaded: return
        if required_urea is not None and required_urea != self.urea_spreaded: return
        if required_weeds is not None and required_weeds != self.weeds: return
        if required_crop is not None and required_crop != self.crop_index: return

        self.contract_fulfilled = True
        self.contract_failed = False

    def load_state(self) -> None:
        self.fill(STATE_COLORS[self.state])

    def set_state(self, state: int, resetting: bool = False, skip_contract_check: bool = False) -> None:
        self.state = state
        self.load_state()
        self.state_changed = True

        if STATE_NAMES[self.state] == "Harvested" and resetting:
            # End of year
            self.lime_years -= 1
            self.super_spreaded = True
            self.urea_spreaded = True
            self.weeds = min(self.weeds + 1, 2)

        elif STATE_NAMES[self.state] == "Growing 1" and resetting:
            self.super_spreaded = False
            self.urea_spreaded = False

        if not skip_contract_check:
            self.check_contract_fulfill()

    def set_crop_type(self, crop_index: int) -> None:
        logging.info(f"Setting paddock crop to {CROP_TYPES[crop_index]} for paddock {self.num}...")
        self.crop_index = crop_index

    def reset_lime_years(self) -> None:
        self.lime_years = 3

    def reset_paint(self) -> None:
        # Note: this only changes the variable is_painting! to reset the paint on the surface you need to fill this paddock after calling this func
        self.paint_surface = pg.Surface(self.rect.size, pg.SRCALPHA)
        self.paint_mask = pg.mask.from_surface(self.paint_surface)

        self.last_collision_count = 0
        self.is_painting = False

    def paint(self, surface: pg.Surface, pos: Tuple[int, int], color: pg.Color) -> int:
        local_pos = (pos[0] - self.rect.x, pos[1] - self.rect.y)
        surface_mask = pg.mask.from_surface(surface)

        collision_mask = self.mask.overlap_mask(surface_mask, local_pos)
        self.paint_surface.blit(collision_mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0)), (0, 0))

        old_count = self.paint_mask.count()
        self.paint_mask = pg.mask.from_surface(self.paint_surface)
        new_count = self.paint_mask.count() - old_count

        self.draw_to_map(draw_normal_surface=False, draw_paint_surface=True)
        self.is_painting = True

        return new_count * self.scale

    def paint_rect(self, rect: pg.Rect, color: pg.Color) -> None:
        rect_surface = pg.Surface((rect.w, rect.h))
        rect_surface.fill((255, 255, 255))

        self.paint(rect_surface, (rect.x, rect.y), color)

    def update(self, mouse_pos: tuple[int, int]) -> bool:
        # Need to check if it lies in the mask rect first or an error will occur
        if not self.rect.collidepoint((mouse_pos[0] - PANEL_WIDTH, mouse_pos[1])): return False

        mouse_pos_rel = (mouse_pos[0] - self.rect.x - PANEL_WIDTH, mouse_pos[1] - self.rect.y)
        if self.mask.get_at(mouse_pos_rel): return True

        return False