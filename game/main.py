import pygame as pg
import logging
import logger # WARNING: This is required for log formatting to function

from events import Events
from farm_ceo import FarmCEO

from data import *

from performance_monitor import PerformanceMonitor

pg.init()

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
        self.logger = logging.getLogger(__name__)

        self.farm_ceo: FarmCEO = FarmCEO(self.screen, self.clock, self.events)

        self.delta_time = 0.0
        self.performance_monitor = PerformanceMonitor(self.screen, (0, 0))

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

            self.performance_monitor.update(self.delta_time)
            self.performance_monitor.draw()

            pg.display.flip()
            self.delta_time = self.clock.tick(self.FPS)

def main() -> None:
    window = Window()
    window.main()

if __name__ == "__main__":
    main()
