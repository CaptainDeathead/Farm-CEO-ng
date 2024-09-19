import pygame as pg

from typing import Tuple, List

pg.init()

class Button:
    def __init__(self, screen: pg.Surface, x: int, y: int, width: int, height: int, parent_rect: pg.Rect,
                 color: Tuple[int, int, int], selectedColor: Tuple[int, int, int], textColor: Tuple[int, int, int],
                 text: str, size: int, radius: Tuple[int, int, int, int], offset_x: int, offset_y: int, center: bool = False,
                 command: callable = None) -> None:
        
        self.screen: pg.Surface = screen
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.parent_rect: pg.Rect = parent_rect
        self.global_rect: pg.Rect= pg.Rect(parent_rect.x + self.x, parent_rect.y + self.y, self.width, self.height)
        self.rect: pg.Rect = pg.Rect(self.x, self.y, self.width, self.height)
        self.active_color: Tuple[int, int, int] = color
        self.color: Tuple[int, int, int] = color
        self.selectedColor: Tuple[int, int, int] = selectedColor
        self.textColor: Tuple[int, int, int] = textColor
        self.text: str = text
        self.radius: int = radius
        self.selected: bool = False
        self.hidden: bool = False
        self.font: pg.font.Font = pg.font.SysFont("Arial", size)
        self.size: int = size
        self.offset_x: int = offset_x
        self.offset_y: int = offset_y
        self.center: bool = center
        self.command: callable = command
        self.rendered_surface: pg.Surface = pg.Surface((width, height), pg.SRCALPHA)

        self.rebuild()

    def rebuild(self) -> None:
        color = self.active_color

        if self.selected:
            # WARNING: Could be a color missmatch between active_color and color
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

    def set_color(self, new_color: any, rebuild_required: bool = False) -> None:
        if self.active_color != new_color:
            self.active_color = new_color
            
            if rebuild_required: self.rebuild()

    def set_text(self, text: str) -> None:
        self.text = text
        self.rebuild_required = True

    def update(self, pressed: bool = False, set_override: callable = lambda x: None) -> None:
        mouse_collision = self.global_rect.collidepoint(pg.mouse.get_pos())

        if not self.hidden:
            if mouse_collision and pressed:
                set_override(True)
                self.command()

        if mouse_collision:
            self.set_color(self.selectedColor, rebuild_required=True)
        else:
            self.set_color(self.color, rebuild_required=True)

    def draw(self) -> None:
        if not self.hidden:
            self.screen.blit(self.rendered_surface, (self.x, self.y))

    def hide(self) -> None:
        self.hidden = True

    def show(self) -> None:
        self.hidden = False

class DropDown:
    def __init__(self, screen: pg.Surface, x: int, y: int, width: int, segment_height: int, parent_rect: pg.Rect,
                 buttons: List[Button], bg_color: Tuple[int, int, int], on_change: callable) -> None:
        
        self.screen = screen
        self.rect = pg.Rect(x, y, width, len(buttons) * segment_height)
        self.parent_rect = parent_rect

        self.rendered_surface = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)

        self.segment_height = segment_height
        self.buttons: List[Button] = []

        for i, button in enumerate(buttons):
            button.screen = self.rendered_surface

            button.x = 0
            button.y = self.segment_height * i
            button.global_rect = pg.Rect(x, self.parent_rect.y + y + segment_height * i, width, segment_height)

            button.command = lambda text=button.text: self.select_button(text)

            self.buttons.append(button)
        
        self.bg_color = bg_color
        self.on_change = on_change

        self.dropped = False

        self.selected_button = Button(self.buttons[0].screen, self.buttons[0].x, self.buttons[0].y, self.buttons[0].width, self.buttons[0].height,
                                      self.buttons[0].parent_rect, self.buttons[0].color, self.buttons[0].selectedColor, self.buttons[0].textColor,
                                      self.buttons[0].text, self.buttons[0].size, self.buttons[0].radius, 0, 0, True, self.toggle_drop)
        
        self.selected_button.global_rect = buttons[0].global_rect

        self.just_changed = False

        self.rebuild()

    def set_dropped(self, dropped: bool) -> None:
        self.dropped = dropped

        if dropped: self.selected_button.hide()
        else: self.selected_button.show()

        self.rebuild()

    def toggle_drop(self) -> None:
        self.set_dropped(not self.dropped)

    def get_selected_text(self) -> str: return self.selected_button.text

    def select_button(self, button_text: str) -> None:
        if not self.dropped: return

        for button in self.buttons:
            if button.text == button_text:
                self.selected_button.text = button.text

                button.rebuild()
                self.selected_button.rebuild()
                
                self.on_change()
                break
        
        self.set_dropped(False)
        self.just_changed = True

        self.rebuild()

    def rebuild(self) -> None:
        pg.draw.rect(self.rendered_surface, self.bg_color, (0, 0, self.rect.w, self.rect.h), border_radius=10)

        for button in self.buttons:
            button.draw()

        self.selected_button.draw()

    def update(self, pressed: bool = False, set_override: callable = lambda x: None) -> None:
        for button in self.buttons:
            button.update(pressed, set_override)

        if self.just_changed:
            self.just_changed = False
            pressed = False

        self.selected_button.update(pressed, set_override)

    def draw(self) -> None:
        self.screen.fill((255, 255, 255), self.rect)

        if self.dropped:
            self.screen.blit(self.rendered_surface, (self.rect.x, self.rect.y))
        else:
            self.screen.blit(self.selected_button.rendered_surface, (self.rect.x, self.rect.y))

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