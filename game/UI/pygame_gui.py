import pygame as pg

from typing import Tuple, List

pg.init()

class Button:
    def __init__(self, screen: pg.Surface, x: int, y: int, width: int, height: int,
                 color: Tuple[int, int, int], selectedColor: Tuple[int, int, int], textColor: Tuple[int, int, int],
                 text: str, size: int, radius: int, offset_x: int, offset_y: int, center: bool = False) -> None:
        
        self.screen: pg.Surface = screen
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.rect: pg.Rect = pg.Rect(self.x, self.y, self.width, self.height)
        self.color: Tuple[int, int, int] = color
        self.selectedColor: Tuple[int, int, int] = selectedColor
        self.textColor: Tuple[int, int, int] = textColor
        self.text: str = text
        self.radius: int = radius
        self.selected: bool = False
        self.font: pg.font.Font = pg.font.SysFont("Arial", size)
        self.size: int = size
        self.offset_x: int = offset_x
        self.offset_y: int = offset_y
        self.center: bool = center
        self.rendered_surface: pg.Surface = pg.Surface((width, height), pg.SRCALPHA)
        self.rendered_surface.convert_alpha()

        self.rebuild()

    def rebuild(self) -> None:
        color = self.color

        if self.selected:
            color = self.selectedColor
            
        pg.draw.rect(self.rendered_surface, color, (0, 0, self.width, self.height),
                     border_top_left_radius = self.radius[0], border_bottom_left_radius = self.radius[1],
                     border_top_right_radius = self.radius[2], border_bottom_right_radius = self.radius[3])
            
        rendered_text = self.font.render(str(self.text), True, self.textColor)

        x = self.x + self.offset_x
        y = self.y + self.offset_y

        if self.center:
            x = self.width / 2 - rendered_text.get_width() / 2
            y = self.height / 2 - rendered_text.get_height() / 2

        self.rendered_surface.blit(rendered_text, (x, y))

    def set_selected(self, selected: bool) -> None:
        changed = self.selected != selected

        self.selected = selected
        if changed: self.rebuild()

    def draw(self) -> None:
        self.screen.blit(self.rendered_surface, (self.x, self.y))

class Table:
    def __init__(self, screen: pg.Surface, x: int, y: int, width: int, height: int, rows: List[str], columns: List[str],
                 color: Tuple[int, int, int], selectedColor: Tuple[int, int, int], size: int, grid: List[List[str]]) -> None:
        
        self.screen: pg.Surface = screen
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.rows: List[str] = rows
        self.columns: List[str] = columns
        self.color: Tuple[int, int, int] = color
        self.selectedColor: Tuple[int, int, int] = selectedColor
        self.seg_width: float = self.width / self.rows
        self.seg_height: float = self.width / self.columns
        self.grid: List[List[str]] = grid
        self.font: pg.font.Font = pg.font.SysFont("Arail", size)
        self.line_width = 5
        self.rendered_surface: pg.Surface = pg.Surface((self.width, self.height))

        self.rebuild()

    def rebuild(self) -> None:
        self.rendered_surface.fill(self.color) # background

        pg.draw.rect(self.rendered_surface, self.selectedColor, (self.x, self.y, self.seg_width, self.height)) # left bar
        pg.draw.rect(self.rendered_surface, self.selectedColor, (self.x, self.y, self.width, self.seg_height)) # right bar
        
        for x in range(1, self.rows):
            pg.draw.line(self.rendered_surface, (0, 0, 0), (self.x+self.seg_width*x, self.y),
                         (self.x+self.seg_height*x, self.y+self.height), self.line_width)

        for y in range(1, self.rows):
            pg.draw.line(self.rendered_surface, (0, 0, 0), (self.x, self.y+self.seg_height*y),
                         (self.x+self.width, self.y+self.seg_height*y), self.line_width)

        for y in range(self.columns):
            for x in range(self.rows):
                render_x = self.x + self.seg_width * x + self.seg_width / 16
                render_y = self.y + self.seg_height * y + self.seg_height / 2.5

                rendered_font = self.font.render(str(self.grid[y][x]), True, (255, 255, 255))

                self.rendered_surface.blit(rendered_font, (render_x, render_y))

    def update_table(self, grid: List[List[str]]) -> None:
        self.grid = grid

    def draw(self) -> None:
        return self.rendered_surface