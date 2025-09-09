import pygame as pg
import logging
import sys
import asyncio

from traceback import format_exc, extract_tb
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
            asyncio.run(self.process_crash())

    def prebuild_crash_info(self, exception_summary: str) -> None:
        self.screen = pg.display.get_surface()
        self.WIDTH = self.screen.get_width()
        self.HEIGHT = self.screen.get_height()

        self.rendered_surface = pg.Surface((self.WIDTH, self.HEIGHT), pg.SRCALPHA)

        title_font = pg.font.SysFont(None, 60)
        self.rendered_surface.blit(title_font.render(f"{GAME_NAME} v{GAME_VERSION} HAS CRASHED!", True, (255, 0, 0)), (30, 30))

        disclaimer_font = pg.font.SysFont(None, 45)
        disclaimer_surf = disclaimer_font.render("Your device is fine and no harm has been done. This is an internal error within Farm CEO that most likely isn't known by the developers. Feel free to report it on Google Play in a review. Your savefile should be fine, however there is a chance some data was corrupted. If you are getting these messages when you are launching the game it is likely your save file is corrupted!\n\nTry restarting the game and if the issue persists do not retry until an update is rolled out to avoid savefile being corrupted.", True, (255, 255, 255), wraplength=int(self.WIDTH * 0.95))

        self.rendered_surface.blit(disclaimer_surf, (30, 100))

        exc_type, exc_value, exc_tb = sys.exc_info()
        # Get the last frame (where the exception occurred)
        tb_last = extract_tb(exc_tb)[-1]
        filename = tb_last.filename
        line_no = tb_last.lineno
        func_name = tb_last.name

        error_font = pg.font.SysFont(None, 30)
        self.rendered_surface.blit(error_font.render(f"Error at line {line_no} in {filename}: {exception_summary}\n\n{format_exc()}", True, (255, 255, 0)), (30, disclaimer_surf.get_height() + 150))

    async def process_crash(self) -> None:
        clock = pg.time.Clock()

        while 1:
            self.screen.fill(pg.Color(0, 0, 0))

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit(1)
                    return

            self.screen.blit(self.rendered_surface, (0, 0))

            clock.tick(30)
            pg.display.flip()

            await asyncio.sleep(0)