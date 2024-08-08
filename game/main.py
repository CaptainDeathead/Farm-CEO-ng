import pygame as pg

pg.init()

class Window:
    PYGAME_INFO: any = pg.display.Info()
    WIDTH: int = PYGAME_INFO.current_w
    HEIGHT: int = PYGAME_INFO.current_h

    def __init__(self) -> None:
        self.screen: pg.Surface = pg.display.set_mode((self.WIDTH, self.HEIGHT))
        


def main() -> None:
    window = Window()

if __name__ == "__main__":
    main()