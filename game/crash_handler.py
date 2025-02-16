import pygame as pg
import logging

from traceback import format_exc
from data import *

class CrashHandler:
    def __init__(self, main_func: object) -> None:
        self.main_func = main_func

        try:
            self.main_func()
        except Exception as e:
            logging.critical(f"CRITICAL ERROR HAS OCCURED! SHOWING CRASH SCREEN...")
            print(format_exc())

            self.prebuild_crash_info(str(e))
            self.process_crash()

    def prebuild_crash_info(self, exception_summary: str) -> None:
        self.screen = pg.display.get_surface()
        self.WIDTH = self.screen.width
        self.HEIGHT = self.screen.height

        self.screen.fill(pg.Color(0, 0, 0, 128))

        title_font = pg.font.SysFont(None, 60)
        self.screen.blit(title_font.render(f"{GAME_NAME} v{GAME_VERSION} HAS CRASHED!", True, (255, 0, 0)), (30, 30))

        disclaimer_font = pg.font.SysFont(None, 45)
        disclaimer_surf = disclaimer_font.render("Your device is fine and no harm has been done. This is an internal error within Farm CEO that most likely isn't known by the developers. Feel free to report it on Google Play in a review. Your savefile should be fine, however there is a chance some data was corrupted. If you are getting these messages when you are launching the game it is likely your save file is corrupted!\n\nTry restarting the game and if the issue persists do not retry until an update is rolled out to avoid savefile being corrupted.", True, (255, 255, 255), wraplength=int(self.WIDTH * 0.95))

        self.screen.blit(disclaimer_surf, (30, 100))

        error_font = pg.font.SysFont(None, 30)
        self.screen.blit(error_font.render(f"Error: {exception_summary}\n\n{format_exc()}", True, (255, 255, 0)), (30, disclaimer_surf.get_height() + 150))

        pg.display.flip()
        
    def process_crash(self) -> None:
        clock = pg.time.Clock()

        while 1:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    return

            clock.tick(30)
            pg.display.flip()