import pygame as pg
from game.UI.pygame_gui import Button

import tkinter as tk
import sv_ttk

from tkinter import filedialog, messagebox, ttk

from typing import List, Tuple, Dict

pg.init()

class Map:
    def __init__(self, screen: pg.Surface, name: str, author: str, version: str, file_path: str) -> None:
        self.screen: pg.Surface = screen
        
        self.SCREEN_WIDTH: int = self.screen.get_width()
        self.SCREEN_HEIGHT: int = self.screen.get_height()

        self.NAME: str = name
        self.AUTHOR: str = author
        self.VERSION: str = version
        self.FILE_PATH: str = file_path

        self.roads: Dict[str, List[Tuple[int]]] = {}
        self.paddocks: Dict[str, Dict[str, any]] = {}
        self.sell_points: Dict[str, Dict[str, any]] = {}

        self.image: pg.Surface = pg.image.load(self.FILE_PATH).convert_alpha()

        self.x: int = self.SCREEN_WIDTH - self.image.get_width()
        self.y: int = 0

        self.rect: pg.Rect = pg.Rect(self.x, self.y, self.image.get_width(), self.image.get_height())

    def add_road(self, road: int) -> None:
        self.roads[road] = []

    def render(self) -> None:
        self.screen.blit(self.image, (self.x, self.y))

class MapEditor:
    PYGAME_INFO: any = pg.display.Info()
    WIDTH: int = PYGAME_INFO.current_w
    HEIGHT: int = PYGAME_INFO.current_h

    def __init__(self, name: str, author: str, version: str, file_path: str) -> None:
        self.screen: pg.Surface = pg.display.set_mode((self.WIDTH, self.HEIGHT))
        self.map: Map = Map(self.screen, name, author, version, file_path)

        self.title_font: pg.font.Font = pg.font.SysFont(None, 60)
        self.body_font: pg.font.Font = pg.font.SysFont(None, 40)

        self.step_lbls: Tuple[pg.Surface] = (self.title_font.render("Step 1 - Roads", True, (255, 255, 255)),
                                              self.title_font.render("Step 2 - Paddock Gates", True, (255, 255, 255)),
                                              self.title_font.render("Step 3 - Sell Points", True, (255, 255, 255)))
        
        self.step_description_lbls: Tuple[pg.Surface] = (self.render_text(600, self.body_font, "Left click where you want to start a road, then keep left clicking to place road checkpoints. Right click to backtrack.", (255, 255, 255), (27, 31, 35)),
                                                        self.render_text(600, self.body_font, "Left click in the middle of each paddock and then left click where you want the gate to be.", (255, 255, 255), (27, 31, 35)),
                                                        self.render_text(600, self.body_font, "Left click to place a sell point and then left click again ones you get the desired rotation.", (255, 255, 255), (27, 31, 35)))
        
        self.placement_buttons: List[Button] = []

        self.current_road: int = 0
        self.map.add_road(self.current_road)

        self.add_btn: Button = Button(self.screen, 350, 850, 200, 50, (60, 60, 200), (100, 100, 255), (255, 255, 255), "+", 20, (15, 15, 15, 15), 0, 0, True, self.add_step_object)
        self.next_step_btn: Button = Button(self.screen, 350, 950, 200, 50, (60, 200, 60), (100, 255, 100), (255, 255, 255), "Next Step", 20, (15, 15, 15, 15), 0, 0, True, self.next_step)

        self.step: int = 0

        self.lmb_just_pressed: bool = False

    def render_text(self, width: int, font: pg.font.Font, text: str,
                    font_color: Tuple[int, int, int], background_color: Tuple[int, int, int]) -> pg.Surface:
        
        space_width = font.size(" ")[0]
        line_size = font.get_linesize()
        line_count = 1

        font_surface = pg.Surface((width, line_size))
        font_surface.fill(background_color)

        curr_width = 0
        words = text.split(' ')

        for word in words:
            if curr_width + font.size(word)[0] > width:
                line_count += 1
                new_font_surface = pg.Surface((width, line_size*line_count))
                new_font_surface.fill(background_color)
                new_font_surface.blit(font_surface, (0, 0))

                curr_width = 0
                new_font_surface.blit(font.render(word, True, font_color), (curr_width, line_size*(line_count-1)))
                font_surface = new_font_surface
                curr_width += font.size(word)[0] + space_width
            else:
                font_surface.blit(font.render(word, True, font_color), (curr_width, line_size*(line_count-1)))
                curr_width += font.size(word)[0] + space_width

        return font_surface
   
    def add_step_object(self) -> None:
        obj_label = "Object"

        if self.step == 0:
            obj_label = "Road"

            self.current_road += 1
            self.map.add_road(self.current_road)

        self.placement_buttons.append(Button(self.screen, 350, len(self.placement_buttons)*60+300, 200, 50,
                                             (50, 50, 50), (100, 100, 100), (255, 255, 255), f"{obj_label}: {len(self.placement_buttons)+1}", 30,
                                             (10, 10, 10, 10), 0, 0, True, lambda: self.select_step_obj(len(self.placement_buttons))))

    def next_step(self) -> None:
        self.step += 1

    def draw_point_connections(self, points: List[Tuple[int, int]], color: Tuple[int, int, int]) -> None:
        for i, point in enumerate(points):
            pg.draw.circle(self.screen, color, point, 5)

            if i > 0:
                pg.draw.line(self.screen, color, point, points[i-1])

    def draw_step_visualizations(self) -> None:
        if self.step == 0:
            self.draw_point_connections(self.map.roads[self.current_road], (0, 255, 0))

    def process_step_1_event(self, mouse_btn: int, x: int, y: int) -> None:
        if mouse_btn == 1:
            self.map.roads[self.current_road].append((x, y))
        
        elif mouse_btn == 3:
            if len(self.map.roads[self.current_road]) > 0:
                self.map.roads[self.current_road].pop(-1)

    def process_step_2_event(self, mouse_btn: int, x: int, y: int)  -> None:
        ...

    def process_step_3_event(self, mouse_btn: int, x: int, y: int) -> None:
        ...
    
    def process_step_event(self, mouse_btn: int) -> None:
        if not self.map.rect.collidepoint(pg.mouse.get_pos()): return

        mouse_pos = pg.mouse.get_pos()

        lx = int(self.screen.get_width() - mouse_pos[0])
        ly = int(self.map.image.get_height() - mouse_pos[1])

        if self.step == 0: self.process_step_1_event(mouse_btn, mouse_pos[0], mouse_pos[1])
        elif self.step == 1: self.process_step_2_event(mouse_btn, lx, ly)
        elif self.step == 2: self.process_step_3_event(mouse_btn, lx, ly)

    def process_events(self) -> None:
        self.lmb_just_pressed = False

        for event in pg.event.get():
            if event.type == pg.QUIT:
                if messagebox.askokcancel("Quit?", "Are you sure you want to quit? Changes will not be saved!", icon="warning"):
                    pg.quit()
                    exit()
            if event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.lmb_just_pressed = True
                    self.process_step_event(1)
                elif event.button == 3:
                    self.process_step_event(3)

    def main(self) -> None:
        clock = pg.time.Clock()

        pg.display.set_caption(f"Farm CEO ~ Map Editor - {self.map.NAME}")

        while 1:
            self.screen.fill((27, 31, 35))

            self.process_events()

            self.map.render()
            self.draw_step_visualizations()
            
            self.screen.blit(self.step_lbls[self.step], (450 - self.step_lbls[self.step].get_width() / 2, 50))
            self.screen.blit(self.step_description_lbls[self.step], (500 - self.step_description_lbls[self.step].get_width() / 2, 150))

            for button in self.placement_buttons:
                button.draw(self.lmb_just_pressed)

            self.add_btn.draw(self.lmb_just_pressed)
            self.next_step_btn.draw(self.lmb_just_pressed)

            pg.display.flip()
            clock.tick(60)
        
class MapConfigure:
    def __init__(self) -> None:
        self.root: tk.Tk = tk.Tk()
        self.root.geometry("300x300")
        self.root.title("Farm CEO ~ Map Editor - New Map")

        self.header_lbl: ttk.Label = ttk.Label(self.root, text="New Map", font=("TkDefaultFont", 30))
        self.header_lbl.pack()

        # Map Name Entry
        self.name_frame: ttk.Frame = ttk.Frame(self.root)
        self.name_frame.pack(pady=5)
        self.name_lbl: ttk.Label = ttk.Label(self.name_frame, text="Map Name:  ")
        self.name_lbl.pack(side=tk.LEFT)
        self.name_entry: ttk.Entry = ttk.Entry(self.name_frame)
        self.name_entry.pack(side=tk.LEFT)
        self.name_entry.insert(0, "Map name")

        # Authors Name Entry
        self.author_frame: ttk.Frame = ttk.Frame(self.root)
        self.author_frame.pack(pady=5)
        self.author_lbl: ttk.Label = ttk.Label(self.author_frame, text="Author(s):  ")
        self.author_lbl.pack(side=tk.LEFT)
        self.author_entry: ttk.Entry = ttk.Entry(self.author_frame)
        self.author_entry.pack(side=tk.LEFT)
        self.author_entry.insert(0, "Author(s) name(s)")

        self.version = "v1.0.0"
        self.file_path: str = ""

        self.file_path_lbl: ttk.Label = ttk.Label(self.root, text="No file path provided")
        self.file_path_lbl.pack()

        self.get_file_path_btn: ttk.Button = ttk.Button(self.root, text="Open map image 🗾", command=self.get_file_path)
        self.get_file_path_btn.pack(pady=10)

        self.create_map_btn: ttk.Button = ttk.Button(self.root, text="Create map ✅", command=self.load_editor)
        self.create_map_btn.pack(pady=10)

        sv_ttk.set_theme("dark")

        self.root.mainloop()

    def get_file_path(self) -> None:
        self.file_path = filedialog.askopenfilename(title="Select map image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if self.file_path:
            self.file_path_lbl.config(text=f"File path: {self.file_path}")

    def load_editor(self) -> None:
        name = self.name_entry.get()
        
        if name in ("Map name", ""):
            messagebox.showerror(title="Invalid name", message="Please enter a map name")
            return
        
        author = self.author_entry.get()
        if author in ("Author(s) name(s)", ""):
            messagebox.showerror(title="Invalid author(s)", message="Please enter the names of the authors")
            return
        
        if not self.file_path:
            messagebox.showerror(title="Invalid map image path", message="Please select a valid map image")
            return
        
        self.root.destroy()
        load_map_editor(name, author, self.version, self.file_path)
        
def load_map_editor(name: str, author: str, version: str, file_path: str) -> None:
    map_editor = MapEditor(name, author, version, file_path)
    map_editor.main()

def main() -> None:
    map_configure = MapConfigure()

def testing() -> None:
    name = "Example"
    author = "developer"
    version = "v0.0.0dev"
    file_path = "./game/assets/Data/Maps/green_spring.png"

    map_editor = MapEditor(name, author, version, file_path)
    map_editor.main()

if __name__ == "__main__":
    #main()
    testing()
