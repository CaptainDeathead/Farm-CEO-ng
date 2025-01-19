import pygame as pg

from typing import Sequence, List

pg.init()

class PerformanceMonitor:
    TARGET_FPS: float = 60.0
    TARGET_FRAME_TIME: float = 1000.0 / TARGET_FPS

    def __init__(self, parent_surface: pg.Surface, pos: Sequence[int]) -> None:
        self.parent_surface = parent_surface
        self.pos = pos

        self.rendered_surface = pg.Surface((120, 100), pg.SRCALPHA)
        self.rendered_surface.set_alpha(128)

        self.last_120_frames: List[float] = []

    def get_frame_color(self, frame_percent: float) -> pg.Color:
        r = max(0, min(255, int(255 * (1 - (frame_percent / self.TARGET_FPS)))))
        g = max(0, min(255, int(255 * (frame_percent / self.TARGET_FPS))))
        b = 0

        return pg.Color(r, g, b)

    def draw(self) -> None:
        self.rendered_surface.fill((50, 50, 200))

        for x, frame in enumerate(self.last_120_frames):
            frame_percent = min(100, frame / self.TARGET_FPS * 100)
            pg.draw.line(self.rendered_surface, self.get_frame_color(frame), (x, 100), (x, 100 - frame_percent))

        self.parent_surface.blit(self.rendered_surface, self.pos)

    def update(self, delta_time: float) -> None:
        if len(self.last_120_frames) == 120: self.last_120_frames.pop(0)

        self.last_120_frames.append(round(1.0 / (delta_time / 1000.0 + 0.00000001), 2)) # gets current FPS