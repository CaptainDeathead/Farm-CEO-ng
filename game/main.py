import pygame as pg

from events import Events
from farm_ceo import FarmCEO

pg.init()

class Window:
    PYGAME_INFO: any = pg.display.Info()
    WIDTH: int = PYGAME_INFO.current_w
    HEIGHT: int = PYGAME_INFO.current_h

    FPS: int = 60

    def __init__(self) -> None:
        self.screen: pg.Surface = pg.display.set_mode((self.WIDTH, self.HEIGHT), display=1)
        self.clock: pg.time.Clock = pg.time.Clock()
        self.events: Events = Events()

        self.farm_ceo: FarmCEO = FarmCEO(self.screen, self.clock, self.events)

    def main(self) -> None:
        pg.display.set_caption("Farm CEO - Development | Platform: Linux | Build: False")
        while 1:
            self.events.process_events()

            self.farm_ceo.background_render()

            self.farm_ceo.simulate()

            self.farm_ceo.foreground_render()
            self.farm_ceo.ui_render()

            pg.display.flip()
            self.clock.tick(self.FPS)

def main() -> None:
    window = Window()
    window.main()

if __name__ == "__main__":
    main()