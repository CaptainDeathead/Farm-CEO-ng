import pygame as pg
import logging

from save_manager import SaveManager
from paddock import Paddock
from data import *

from typing import Dict, List, Tuple

class PaddockManager:
    def __new__(cls) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(PaddockManager, cls).__new__(cls)

        return cls.instance
    
    def init(self, screen: pg.Surface, map_image: pg.Surface, active_map_image: pg.Surface, paddocks: Dict[int, any], scale: float) -> None:
        self.screen = screen
        self.map_image = map_image
        self.active_map_image = active_map_image
        self.scale = scale

        self.paddocks = self.parse_paddocks(paddocks)
        self.init_paddocks()

    def parse_paddocks(self, paddocks: Dict[str, any]) -> List[Paddock]:
        pdk_list = []
        for paddock in paddocks:
            pdk_list.append(Paddock(paddocks[paddock], paddock, self.scale))
        
        return pdk_list

    def locate_paddock_boundary(self, paddock: Paddock) -> None:
        logging.debug(f"Locating paddock boundary... Paddock: {paddock.num}")

        def rgb_darker_than(rgb: Tuple[int, int, int], brightness: int) -> bool:
            if rgb[0] < brightness and rgb[1] < brightness and rgb[2] < brightness: return True
            return False
        
        darkness = 110
        
        def get_adj_edge(pos: Tuple[int, int]) -> Tuple[int, int]:
            for x in range(-1, 2):
                for y in range(-1, 2):
                    if x == 0 and y == 0: continue

                    nx, ny = pos[0] + x, pos[1] + y
                    if not rgb_darker_than(self.map_image.get_at((nx, ny)), darkness): return (nx, ny)
            
            return (-1, -1)
        
        if DEBUG_BOUNDARY_LOADING: pg.display.update(pg.display.get_surface().blit(self.map_image, (0, 0)))

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

        surface = pg.display.get_surface()

        while 1:
            if DEBUG_BOUNDARY_LOADING: surface.set_at((curr_x, curr_y), (255, 255, 255))
            found_new_px = False

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
                        edge = get_adj_edge((nx, ny))

                        if edge != (-1, -1):
                            found_new_px = True
                            boundary.append((nx, ny))
                            curr_x, curr_y = nx, ny
                        else:
                            if DEBUG_BOUNDARY_LOADING: surface.set_at((nx, ny), (255, 0, 0))

            if DEBUG_BOUNDARY_LOADING:
                surface.set_at((nx, ny), (255, 0, 0))
                pg.display.flip()

    def fill_paddock(self, paddock: Paddock, color: pg.Color) -> None:
        boundary = paddock.boundary
        pg.draw.polygon(self.active_map_image, color, boundary)

    def load_paddock_state(self, paddock: Paddock) -> None:
        self.fill_paddock(paddock, STATE_COLORS[paddock.state])

    def set_paddock_state(self, paddock_number: int, state: int) -> None:
        paddock = self.paddocks[paddock_number-1]

        paddock.state = state
        paddock.fill(STATE_COLORS[paddock.state])

    def fill_all_paddocks(self) -> None:
        for paddock in self.paddocks:
            self.load_paddock_state(paddock)

    def init_paddocks(self) -> None:
        logging.debug("Initializing paddocks... (This may take some time)")
        
        for paddock in self.paddocks:
            self.locate_paddock_boundary(paddock)
            paddock.init_collision()

            self.load_paddock_state(paddock)

        save_manager = SaveManager()
        save_manager.set_paddocks(self.paddocks)
        save_manager.save_game()

    def draw_paddock_numbers(self) -> None:
        for paddock in self.paddocks:
            self.screen.blit(paddock.number_surface, (PANEL_WIDTH + paddock.center[0], paddock.center[1]))

    def check_paddock_clicks(self) -> Paddock | None:
        pos = pg.mouse.get_pos()

        for paddock in self.paddocks:
            pressed = paddock.update(pos)

            if pressed:
                return paddock