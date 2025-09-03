import pygame as pg
import logging

from save_manager import SaveManager
from resource_manager import ResourceManager
from paddock import Paddock
from destination import Destination
from data import *

from math import cos, sin, radians
from typing import Dict, List, Tuple

class PaddockManager:
    def __new__(cls) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(PaddockManager, cls).__new__(cls)

        return cls.instance
    
    def init(self, screen: pg.Surface, map_image: pg.Surface, map_paddocks_surf: pg.Surface, paddocks: Dict[int, any], scale: float) -> None:
        self.screen = screen
        self.map_image = map_image
        self.map_paddocks_surf = map_paddocks_surf
        self.scale = scale

        self.paddocks = self.parse_paddocks(paddocks)
        self.init_paddocks()

        self.location_callback = None

        self.preload_indicators()

    def get_paddocks(self) -> List[Paddock]:
        return self.paddocks

    def parse_paddocks(self, paddocks: Dict[str, any]) -> List[Paddock]:
        pdk_list = []
        for paddock in paddocks:
            pdk_list.append(Paddock(paddocks[paddock], paddock, self.scale, self.map_paddocks_surf))
        
        return pdk_list

    def preload_indicators(self) -> None:
        logging.info("Preloading indicators...")

        self.indicators = {}
        self.indicator_size = 30 * self.scale

        for fill_type in FILL_TYPES:
            processed_fill_type = fill_type.replace('liquid-', '').replace('herbicide', 'weeds')

            clipping_surface = pg.Surface((self.indicator_size, self.indicator_size), pg.SRCALPHA)
            pg.draw.circle(clipping_surface, (255, 255, 255), (self.indicator_size / 2, self.indicator_size / 2), self.indicator_size / 2)

            surface = pg.Surface((self.indicator_size, self.indicator_size), pg.SRCALPHA)
            surface.fill(UI_BACKGROUND_COLOR)
            surface.blit(pg.transform.smoothscale(ResourceManager().load_image(f"Icons/FillTypes/{processed_fill_type}.png"), (self.indicator_size, self.indicator_size)), (0, 0))

            surface.blit(clipping_surface, (0, 0), special_flags=pg.BLEND_RGBA_MIN)

            self.indicators[processed_fill_type] = surface

    def locate_paddock_boundary(self, paddock: Paddock) -> None:
        logging.debug(f"Locating paddock boundary... Paddock: {paddock.num} Center: {paddock.center}")

        def rgb_darker_than(rgb: Tuple[int, int, int], brightness: int) -> bool:
            if rgb[0] < brightness and rgb[1] < brightness and rgb[2] < brightness: return True
            return False
        
        darkness = 110
        
        def get_adj_edge(pos: Tuple[int, int], exclusions: List[Tuple[int, int]]) -> Tuple[int, int]:
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if x == 0 and y == 0: continue

                    nx, ny = pos[0] + x, pos[1] + y
                    
                    if (nx, ny) in exclusions: continue

                    if not rgb_darker_than(self.map_image.get_at((nx, ny)), darkness): return (nx, ny)
            
            return (0, 0)
        
        if DEBUG_BOUNDARY_LOADING: pg.display.update(pg.display.get_surface().blit(self.map_image, (-11000, -2700)))

        boundary = []

        # Starting at center
        cx, cy = paddock.center

        start_x = cx
        start_y = 0

        # find boundary start from center
        y = cy
        while 1:
            if not rgb_darker_than(self.map_image.get_at((cx, y)), darkness):
                start_y = y
                break
            y += 1
        
        # trace boundary
        curr_x = start_x
        curr_y = start_y

        exclusions = []
        backtrack_index = -1

        surface = self.map_image.copy()
        screen = pg.display.get_surface()

        update_index = 0

        while 1:
            if DEBUG_BOUNDARY_LOADING: surface.set_at((curr_x, curr_y), (255, 255, 255))
            found_new_px = False

            update_index += 1

            # get adjacent paddock squares (black)
            for x in range(-1, 2):
                if found_new_px: continue
                
                for y in range(-1, 2):
                    if (x == 0 and y == 0) or found_new_px: continue
                    
                    nx, ny = curr_x + x, curr_y + y

                    if (nx, ny) == (start_x, start_y): # Back to start (Done)
                        if len(boundary) < 2: continue

                        paddock.set_boundary(boundary)
                        return
                    
                    if (nx, ny) in boundary: continue

                    if rgb_darker_than(self.map_image.get_at((nx, ny)), darkness):
                        edge = get_adj_edge((nx, ny), exclusions)

                        if edge != (0, 0):
                            found_new_px = True
                            boundary.append((nx, ny))
                            curr_x, curr_y = nx, ny
                            backtrack_index = -1
                        else:
                            if DEBUG_BOUNDARY_LOADING: surface.set_at((nx, ny), (255, 0, 0))

            if not found_new_px:
                exclusions.append((curr_x, curr_y))
                curr_x, curr_y = boundary[backtrack_index]
                backtrack_index -= 1

            if DEBUG_BOUNDARY_LOADING:
                if BOUNDARY_LOAD_UPDATE_SLOW and not update_index - 200 == 0: continue

                update_index = 0

                screen.fill((0, 0, 0))
                surface.set_at((nx, ny), (255, 0, 0))
                screen.blit(surface, (-curr_x + screen.width / 2, -curr_y + screen.height / 2))
                pg.display.flip()

    def set_paddock_state(self, paddock_number: int, state: int) -> None:
        paddock = self.paddocks[paddock_number-1]

        paddock.state = state
        paddock.fill(STATE_COLORS[paddock.state])

    def fill_all_paddocks(self, exclude_paddocks: List[int] = [], draw_paint: bool = False) -> None:
        for i, paddock in enumerate(self.paddocks):
            if i in exclude_paddocks:
                paddock.fill((0, 0, 0))
            else:
                paddock.load_state()

            paddock.draw_to_map(False, True)

    def init_paddocks(self) -> None:
        logging.debug("Initializing paddocks... (This may take some time)")
        
        for paddock in self.paddocks:
            self.locate_paddock_boundary(paddock)
            paddock.init_collision()

            paddock.load_state()

    def get_indicator_position(self, paddock_center: Tuple[float, float], indicator_angle: int) -> Tuple[float, float]:
        dist = 45 * self.scale
        return (PANEL_WIDTH + paddock_center[0] + cos(radians(indicator_angle)) * dist - self.indicator_size / 2, paddock_center[1] + sin(radians(indicator_angle)) * dist - self.indicator_size / 2)

    def draw_paddock_numbers(self, draw_price: bool = False) -> None:
        for paddock in self.paddocks:
            self.screen.blit(paddock.number_surface, (PANEL_WIDTH + paddock.center[0] - paddock.number_surface.width / 2, paddock.center[1] - paddock.number_surface.height / 2))

            indicator_angle = 270
            self.screen.blit(self.indicators[CROP_TYPES[paddock.crop_index]], self.get_indicator_position(paddock.center, indicator_angle))
            indicator_angle -= 45

            if paddock.lime_years <= 0:
                self.screen.blit(self.indicators["lime"], self.get_indicator_position(paddock.center, indicator_angle))
                indicator_angle -= 45

            if not paddock.super_spreaded:
                self.screen.blit(self.indicators["super"], self.get_indicator_position(paddock.center, indicator_angle))
                indicator_angle -= 45

            if not paddock.urea_spreaded:
                self.screen.blit(self.indicators["urea"], self.get_indicator_position(paddock.center, indicator_angle))
                indicator_angle -= 45

            if paddock.weeds > 0:
                self.screen.blit(self.indicators["weeds"], self.get_indicator_position(paddock.center, indicator_angle))
                indicator_angle -= 45

            if draw_price:
                self.screen.blit(paddock.price_lbl_surface, (PANEL_WIDTH + paddock.center[0] - paddock.price_lbl_surface.width / 2, paddock.center[1] - paddock.price_lbl_surface.height / 2 + 30 * self.scale))

    def check_paddock_clicks(self) -> Paddock | None:
        pos = pg.mouse.get_pos()

        for paddock in self.paddocks:
            pressed = paddock.update(pos)

            if pressed:
                return paddock

    def set_location_click_callback(self, callback: callable) -> None:
        self.location_callback = callback

    def destroy_location_click_callback(self) -> None:
        self.location_callback = None

    def update(self, mouse_just_released: bool) -> None:
        for paddock in self.paddocks:
            if paddock.state_changed:
                logging.info(f"Paddock {paddock.num} state change detected, updating save_manager dict...")
                paddock.state_changed = False
                break

        if mouse_just_released and self.location_callback is not None:
            paddock_clicked = self.check_paddock_clicks()

            if paddock_clicked is not None:
                self.location_callback(Destination(paddock_clicked))