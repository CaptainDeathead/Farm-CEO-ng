import pygame as pg
import sys
import logging

from time import sleep
from events import Events
from farm_ceo import FarmCEO
from log_config import setup_logging
from crash_handler import CrashHandler

from data import *

if BUILD and TARGETING_ANDROID: from jnius import autoclass
if CONSOLE_BUILD: from console import PygameConsole

from performance_monitor import PerformanceMonitor

pg.init()

logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)

setup_logging()

class SpoofedConsole:
    def update(self, *args) -> None:
        return
    
    def write(self, text: str, *args) -> None:
        # Ignore `print` argument
        sys.__stdout__.write(text)

    def flush(self) -> None:
        sys.__stdout__.flush()

class PygameConsoleHandler(logging.Handler):
    def __init__(self, console: SpoofedConsole):
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

    FPS: int = TARGET_FPS

    def __init__(self) -> None:
        if BUILD and TARGETING_ANDROID:
            self.setup_android()
            sleep(1)

        self.display = int(not BUILD)
        #self.display = 0
        self.screen: pg.Surface = pg.display.set_mode((self.WIDTH, self.HEIGHT), pg.DOUBLEBUF | pg.HWSURFACE | pg.FULLSCREEN, display=self.display)
        self.clock: pg.time.Clock = pg.time.Clock()
        self.events: Events = Events()

        self.farm_ceo: FarmCEO = FarmCEO(self.screen, self.clock, self.events)

        if CONSOLE_BUILD:
            self.console: PygameConsole = PygameConsole(self, self.screen)

            sys.stdout = self.console
            logging.getLogger().addHandler(PygameConsoleHandler(self.console))

        self.delta_time = 0.0
        self.frame_time = 0.0
        self.performance_monitor = PerformanceMonitor(self.screen, (0, 0))

        self.fps_font = pg.font.SysFont(None, 40)

    def setup_android(self):
        # Get the current activity and decor view
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity_instance = PythonActivity.mActivity

        def _set_ui_flags():
            window = activity_instance.getWindow()
            decor_view = window.getDecorView()

            # System UI flags for immersive fullscreen mode
            SYSTEM_UI_FLAG_FULLSCREEN = 4
            SYSTEM_UI_FLAG_HIDE_NAVIGATION = 2
            SYSTEM_UI_FLAG_IMMERSIVE_STICKY = 4096
            flags = SYSTEM_UI_FLAG_FULLSCREEN | SYSTEM_UI_FLAG_HIDE_NAVIGATION | SYSTEM_UI_FLAG_IMMERSIVE_STICKY

            decor_view.setSystemUiVisibility(flags)

        # Run on the UI thread
        activity_instance.runOnUiThread(_set_ui_flags)

    def main(self) -> None:
        pg.display.set_caption(self.TITLE)
        pg.display.set_icon(self.farm_ceo.RESOURCE_MANAGER.load_image("game_icon.png", (100, 100)))

        while 1:
            #sleep(0.016*2)
            events = pg.event.get()
            self.events.process_events(events)

            if ENABLE_KEYBOARD_CHEATS:
                keys = pg.key.get_pressed()

                if keys[pg.K_SPACE]:
                    self.frame_time *= 10

            self.farm_ceo.background_render()

            if self.events.game_paused:
                self.farm_ceo.simulate(0.0)
            else:
                self.farm_ceo.simulate(self.frame_time)

            self.farm_ceo.foreground_render()
            self.farm_ceo.ui_render()

            if not BUILD: 
                self.performance_monitor.update(self.delta_time)
                self.performance_monitor.draw()

            if CONSOLE_BUILD:
                self.console.update(events)

            if not BUILD:
                fps_rendered = self.fps_font.render(f"{int(self.clock.get_fps())}", True, (255, 255, 255), (0, 0, 255))
                self.screen.blit(fps_rendered, (20, 20))

            pg.display.flip()
            self.delta_time = self.clock.tick(self.FPS)
            self.frame_time = self.delta_time / 1000.0

def main() -> None:
    CrashHandler(lambda: Window().main())

if __name__ == "__main__":
    main()
