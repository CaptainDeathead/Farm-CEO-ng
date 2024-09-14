import pygame as pg
import sys
import logging

from events import Events
from farm_ceo import FarmCEO

from data import *

if CONSOLE_BUILD: from console import PygameConsole

pg.init()

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)

class SpoofedConsole:
    def update(self) -> None:
        return
    
    def write(self, text: str, print: bool = True) -> None:
        # Ignore `print` argument
        sys.__stdout__.write(text)

    def flush(self) -> None:
        sys.__stdout__.flush()

class PygameConsoleHandler(logging.Handler):
    def __init__(self, console: PygameConsole | SpoofedConsole):
        super().__init__()
        self.console = console
        self.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))

    def emit(self, record):
        log_entry = self.format(record)
        self.console.write(log_entry, False)

class Window:
    PYGAME_INFO: any = pg.display.Info()
    WIDTH: int = PYGAME_INFO.current_w
    HEIGHT: int = PYGAME_INFO.current_h

    TITLE: str = f"{GAME_NAME} ({BUILD_TYPE}) | Build: {BUILD} | Platform: {PLATFORM} | Version: v{GAME_VERSION}"

    FPS: int = 60

    def __init__(self) -> None:
        self.screen: pg.Surface = pg.display.set_mode((self.WIDTH, self.HEIGHT), display=int(not BUILD))
        self.clock: pg.time.Clock = pg.time.Clock()
        self.events: Events = Events()

        self.farm_ceo: FarmCEO = FarmCEO(self.screen, self.clock, self.events)

        if CONSOLE_BUILD: self.console: PygameConsole = PygameConsole(self, self.screen)
        else: self.console: SpoofedConsole = SpoofedConsole()

        sys.stdout = self.console
        logging.getLogger().addHandler(PygameConsoleHandler(self.console))

    def main(self) -> None:
        pg.display.set_caption(self.TITLE)
        pg.display.set_icon(self.farm_ceo.RESOURCE_MANAGER.load_image("game_icon.png", (100, 100)))

        while 1:
            events = pg.event.get()
            self.events.process_events(events)

            self.farm_ceo.background_render()

            self.farm_ceo.simulate()

            self.farm_ceo.foreground_render()
            self.farm_ceo.ui_render()

            self.console.update(events)

            pg.display.flip()
            self.clock.tick(self.FPS)

def main() -> None:
    window = Window()
    window.main()

if __name__ == "__main__":
    main()