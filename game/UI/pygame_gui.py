import pygame as pg

from typing import Tuple, List

from events import Events
from resource_manager import ResourceManager

pg.init()

class Button:
    def __init__(self, screen: pg.Surface, x: int, y: int, width: int, height: int, parent_rect: pg.Rect,
                 color: Tuple[int, int, int], selectedColor: Tuple[int, int, int], textColor: Tuple[int, int, int],
                 text: str, size: int, radius: Tuple[int, int, int, int], offset_x: int, offset_y: int, center: bool = False,
                 command: callable = None, image: pg.Surface = None, authority: bool = False) -> None:
        
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
        self.image: pg.Surface = image
        self.command: callable = command
        self.authority: bool = authority
        self.opacity: int = 256
        self.rendered_surface: pg.Surface = pg.Surface((width, height), pg.SRCALPHA)

        if self.image is not None:
            self.image = pg.transform.scale(image, (self.width, self.height))

        self.rebuild()

    def set_opacity(self, opacity: int) -> None:
        self.opacity = opacity

    def rebuild(self) -> None:
        color = self.active_color

        if self.selected:
            # WARNING: Could be a color missmatch between active_color and color
            color = self.selectedColor
        
        if self.image is not None:
            self.rendered_surface.blit(self.image, (0, 0))
        else:
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

    def set_color(self, new_color: any, rebuild_required: bool = False) -> bool:
        # Returns: If a rebuild has occured

        if self.active_color != new_color:
            self.active_color = new_color
            
            if rebuild_required:
                self.rebuild()
                return True

        return False

    def set_text(self, text: str) -> None:
        self.text = text
        self.rebuild_required = True

    def set_image(self, image: pg.Surface) -> None:
        self.image = image
        self.rebuild_required = True

    def update(self, pressed: bool = False, set_override: callable = lambda x: None) -> bool:
        # Returns: If a redraw is required

        mouse_collision = self.global_rect.collidepoint(pg.mouse.get_pos())
        redraw_required = False

        if not self.hidden:
            if mouse_collision and pressed:
                set_override(True)
                self.command()

        if mouse_collision:
            redraw_required = self.set_color(self.selectedColor, rebuild_required=True)
        else:
            redraw_required = self.set_color(self.color, rebuild_required=True)

        return redraw_required

    def draw(self) -> None:
        if not self.hidden:
            self.rendered_surface.set_alpha(self.opacity)
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
            button.global_rect = pg.Rect(self.parent_rect.x + x + button.x, self.parent_rect.y + button.y + y, width, segment_height)

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
        radius = self.selected_button.radius
        pg.draw.rect(self.rendered_surface, self.selected_button.color, (0, 0, self.rect.w, self.rect.h), 0, -1, radius[0], radius[1], radius[2], radius[3])

        for button in self.buttons:
            button.draw()

        self.selected_button.draw()

        self.draw()

    def update(self, pressed: bool = False, set_override: callable = lambda x: None) -> None:
        selected_button_was_hidden = self.selected_button.hidden
        self.selected_button.update(pressed, set_override)

        if pressed and self.selected_button.global_rect.collidepoint(pg.mouse.get_pos()):
            # Pressed selected button
            if not selected_button_was_hidden: pressed = False

        if self.dropped:
            for button in self.buttons:
                draw = button.update(pressed, set_override)
                if draw: button.draw()

        if self.just_changed:
            self.just_changed = False
            pressed = False

    def draw(self) -> None:
        self.screen.fill(self.bg_color, self.rect)

        if self.dropped:
            self.screen.blit(self.rendered_surface, (self.rect.x, self.rect.y))
        else:
            self.screen.blit(self.selected_button.rendered_surface, (self.rect.x, self.rect.y))

class Table:
    def __init__(self, screen: pg.Surface, x: int, y: int, width: int, height: int, rows: List[str], columns: List[str],
                 color: Tuple[int, int, int], selectedColor: Tuple[int, int, int], font_size: int, grid: List[List[str]]) -> None:
        
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
        self.seg_height: float = self.height / self.columns
        self.grid: List[List[str]] = grid
        self.font: pg.font.Font = pg.font.SysFont(None, font_size)
        self.line_width = 5
        self.rendered_surface: pg.Surface = pg.Surface((self.width, self.height))

        self.rebuild()

    def rebuild(self) -> None:
        self.rendered_surface.fill(self.color) # background

        pg.draw.rect(self.rendered_surface, self.selectedColor, (0, 0, self.seg_width, self.height)) # left bar
        pg.draw.rect(self.rendered_surface, self.selectedColor, (0, 0, self.width, self.seg_height)) # right bar
        
        for x in range(1, self.rows):
            pg.draw.line(self.rendered_surface, (0, 0, 0), (self.seg_width*x, 0),
                         (self.seg_height*x, self.height), self.line_width)

        for y in range(1, self.columns):
            pg.draw.line(self.rendered_surface, (0, 0, 0), (0, self.seg_height*y),
                         (self.width, self.seg_height*y), self.line_width)

        for y in range(self.columns):
            for x in range(self.rows):
                rendered_font = self.font.render(str(self.grid[y][x]), True, (255, 255, 255), wraplength=int(self.seg_width))

                render_x = self.seg_width * x + self.seg_width / 2 - rendered_font.width / 2
                render_y = self.seg_height * y + self.seg_height / 2 - rendered_font.height / 2

                self.rendered_surface.blit(rendered_font, (render_x, render_y))

    def update_table(self, grid: List[List[str]]) -> None:
        self.grid = grid
        ... # TODO

    def draw(self) -> None:
        self.screen.blit(self.rendered_surface, (self.x, self.y))
    
class Widget:
    def __init__(self, parent_surface: pg.Surface, rect: pg.Rect) -> None:
        self.parent_surface = parent_surface
        self.rect = rect

        self.surface = pg.Surface(self.rect.size, pg.SRCALPHA)

    def draw(self) -> None:
        ...

    def update(self) -> None:
        ...

class Popup:
    BANNER_HEIGHT = 80
    TITLE_FONT_SIZE = 80

    def __init__(self, parent_surface: pg.Surface, rect: pg.Rect, parent_rect: pg.Rect, border_radius: int, title: str, contents: Widget,
                 banner_color: tuple[int, int, int], body_color: tuple[int, int, int], exit_function: callable, submit_function: callable,
                 events: Events, show_exit_button: bool = True) -> None:

        self.parent_surface = parent_surface
        self.rect = rect
        self.parent_rect = parent_rect

        self.surface = pg.Surface(self.rect.size, pg.SRCALPHA)

        self.border_radius = border_radius

        self.title = title
        self.contents = contents

        self.title_font = pg.font.SysFont(None, self.TITLE_FONT_SIZE)

        self.banner_color = banner_color
        self.body_color = body_color

        self.exit_function = exit_function
        self.submit_function = submit_function

        self.events = events

        self.show_exit_button = show_exit_button

        self.exit_img = ResourceManager.load_image("Icons/cross.png")
        self.submit_img = ResourceManager.load_image("Icons/tick.png")

        padding = 10
        btn_width = self.BANNER_HEIGHT - padding * 2

        submit_x = self.rect.w - btn_width - padding
        submit_y = self.rect.h - btn_width - padding

        exit_x = submit_x - btn_width - padding * 2
        exit_y = submit_y

        self.exit_btn = Button(self.surface, exit_x, exit_y, btn_width, btn_width, self.parent_rect, (0, 0, 0), (0, 0, 0), (0, 0, 0),
                               "", 10, (0, 0, 0, 0), 0, 0, True, lambda: self.exit_popup(), self.exit_img)
                            
        self.submit_btn = Button(self.surface, submit_x, submit_y, btn_width, btn_width, self.parent_rect, (0, 0, 0), (0, 0, 0), (0, 0, 0),
                                 "", 10, (0, 0, 0, 0), 0, 0, True, lambda: self.submit_popup(), self.submit_img)

        self.rebuild()

    @property
    def x(self) -> int: return self.rect.x

    @property
    def y(self) -> int: return self.rect.y

    @property
    def width(self) -> int: return self.rect.w

    @property
    def height(self) -> int: return self.rect.h

    def exit_popup(self) -> None:
        self.exit_function()
    
    def submit_popup(self) -> None:
        self.submit_function()

    def rebuild(self) -> None:
        pg.draw.rect(self.surface, self.banner_color, self.rect, border_radius = self.border_radius)

        font_surf = self.title_font.render(self.title, True, (255, 255, 255))

        font_x = 10
        font_y = self.BANNER_HEIGHT / 2 - font_surf.get_height() / 2

        self.surface.blit(font_surf, (font_x, font_y))

    def update(self) -> bool:
        mouse_pos = self.events.mouse_pos

        redraw_required = False

        if self.contents.rect.collidepoint(mouse_pos):
            redraw_required = self.contents.update()

        if self.show_exit_button:
            exit_btn_redraw = self.exit_btn.update(self.events.authority_mouse_just_pressed, self.events.set_override)
        else:
            exit_btn_redraw = False

        submit_btn_redraw = self.submit_btn.update(self.events.authority_mouse_just_pressed, self.events.set_override)

        if exit_btn_redraw or submit_btn_redraw:
            redraw_required = True

        if redraw_required: self.draw()

        return redraw_required

    def draw(self) -> None:
        if self.show_exit_button:
            self.exit_btn.draw()

        self.submit_btn.draw()

        self.surface.blit(self.contents.surface, (0, self.BANNER_HEIGHT))