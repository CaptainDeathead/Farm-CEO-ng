import pygame as pg
from game.UI.pygame_gui import Button

import tkinter as tk
import sv_ttk
import os

from tkinter import filedialog, messagebox, simpledialog, ttk
from random import seed, randint
from math import atan2, degrees
from json import dumps
from shutil import copyfile

from typing import List, Tuple, Dict

pg.init()

# https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
def blitRotate(surf, image, pos, originPos, angle):

    # offset from pivot to center
    image_rect = image.get_rect(topleft = (pos[0] - originPos[0], pos[1]-originPos[1]))
    offset_center_to_pivot = pg.math.Vector2(pos) - image_rect.center
    
    # roatated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # roatetd image center
    rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)

    # get a rotated image
    rotated_image = pg.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

    # rotate and blit the image
    surf.blit(rotated_image, rotated_image_rect)

class Map:
    def __init__(self, screen: pg.Surface, name: str, author: str, version: str, file_path: str) -> None:
        self.screen: pg.Surface = screen
        
        self.SCREEN_WIDTH: int = self.screen.get_width()
        self.SCREEN_HEIGHT: int = self.screen.get_height()

        self.NAME: str = name
        self.AUTHOR: str = author
        self.VERSION: str = version
        self.FILE_PATH: str = file_path

        self.roads: Dict[int, List[Tuple[int]]] = {}
        self.paddocks: Dict[int, Dict[str, any]] = {}
        self.sell_points: Dict[int, Dict[str, any]] = {}

        self.image: pg.Surface = pg.image.load(self.FILE_PATH).convert_alpha()

        self.x: int = self.SCREEN_WIDTH - self.image.get_width()
        self.y: int = 0

        self.rect: pg.Rect = pg.Rect(self.x, self.y, self.image.get_width(), self.image.get_height())

    def add_road(self, road: int) -> None:
        self.roads[road] = []

    def add_paddock(self, paddock: int) -> None:
        self.paddocks[paddock] = {"center": None, "gate": None}

    def add_sellpoint(self, sellpoint: int) -> None:
        self.sell_points[sellpoint] = {"location": None, "rotation": None, "silo": False, "name": None}

    def export(self) -> None:
        # Move coordinates from relative to screen to relative to map
        new_roads = {}
        for road in self.roads:
            if len(self.roads[road]) == 0: continue

            new_road_points = []

            for point in self.roads[road]:
                new_road_points.append((point[0]-self.x, point[1]))
            
            new_roads[road] = new_road_points
        
        new_paddocks = {}
        for paddock in self.paddocks:
            center = self.paddocks[paddock]["center"]
            new_pdk_center = (center[0]-self.x, center[1])

            gate = self.paddocks[paddock]["gate"]
            new_pdk_gate = (gate[0]-self.x, gate[1])

            new_paddocks[paddock] = {"center": new_pdk_center, "gate": new_pdk_gate}

        new_sellpoints = {}
        for sellpoint in self.sell_points:
            new_sellpoints[sellpoint] = self.sell_points[sellpoint]
            
            location = self.sell_points[sellpoint]["location"]
            new_location = (location[0]-self.x, location[1])

            new_sellpoints[sellpoint]["location"] = new_location

        # Bundle all data into dict
        map_dict = {
            "name": self.NAME,
            "creator": self.AUTHOR,
            "version": self.VERSION,
            "filename": f"{self.NAME}_map.png",
            "roads": new_roads,
            "paddocks": new_paddocks,
            "sell points": new_sellpoints
        }

        # Write all data to json
        while 1:
            try:
                os.mkdir(f"./{self.NAME}_output")
                break
            except OSError as e:
                print(e)
                messagebox.showwarning("Directory Exists!", f"When exporting the map config and map image are put into this: '{self.NAME}_output/' directory, however it seems it already exists! Please rename the existing directory or delete it.")

        copyfile(self.FILE_PATH, f"./{self.NAME}_output/{self.NAME}_map.png") # copy map to output

        with open(f"./{self.NAME}_output/{self.NAME}_cfg.json", "w") as output:
            output.write(dumps(map_dict))

    def render(self) -> None:
        self.screen.blit(self.image, (self.x, self.y))

class MapEditor:
    PYGAME_INFO: any = pg.display.Info()
    WIDTH: int = PYGAME_INFO.current_w
    HEIGHT: int = PYGAME_INFO.current_h

    def __init__(self, name: str, author: str, version: str, file_path: str) -> None:
        self.screen: pg.Surface = pg.display.set_mode((self.WIDTH, self.HEIGHT), pg.FULLSCREEN, display=1)
        self.map: Map = Map(self.screen, name, author, version, file_path)

        self.title_font: pg.font.Font = pg.font.SysFont(None, 60)
        self.body_font: pg.font.Font = pg.font.SysFont(None, 40)

        self.step_lbls: Tuple[pg.Surface] = (self.title_font.render("Step 1 - Roads", True, (255, 255, 255)),
                                              self.title_font.render("Step 2 - Paddock Gates", True, (255, 255, 255)),
                                              self.title_font.render("Step 3 - Sell Points", True, (255, 255, 255)))
        
        self.step_description_lbls: Tuple[pg.Surface] = (self.render_text(600, self.body_font, "Left click where you want to start a road, then keep left clicking to place road checkpoints. Right click to backtrack.", (255, 255, 255), (27, 31, 35)),
                                                        self.render_text(600, self.body_font, "Left click in the middle of each paddock and then left click where you want the gate to be.", (255, 255, 255), (27, 31, 35)),
                                                        self.render_text(600, self.body_font, "Left click to place a sell point or silo and then left click again once you get the desired rotation.", (255, 255, 255), (27, 31, 35)))
        
        self.placement_buttons: List[Button] = []

        self.quit: bool = False

        self.current_road: int = 0
        self.map.add_road(self.current_road)

        self.current_pdk: int = 0
        self.map.add_paddock(self.current_pdk)

        grid = pg.image.load("./game/assets/Data/Sprites/grid.png").convert_alpha()
        silo = pg.image.load("./game/assets/Data/Sprites/silo.png").convert_alpha()

        self.sell_point_img: pg.Surface = pg.Surface((54, 33), pg.SRCALPHA).convert_alpha()
        self.sell_point_img.blit(grid, (0, 0))
        self.sell_point_img.blit(silo, (8, 0))

        self.sellpoint_w = self.sell_point_img.get_width()
        self.sellpoint_h = self.sell_point_img.get_height()

        self.current_sellpoint: int = 0
        self.map.add_sellpoint(self.current_sellpoint)
        self.last_sellpoint_pos = (0, 0)

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
    
    def show_map_preview(self) -> None:
        self.screen.fill((27, 31, 35))

        self.map.render()
        self.draw_step_visualizations(draw_all=True)

        pg.display.flip()

    def show_export_screen(self) -> None:
        self.screen.fill((27, 31, 35))

        text = self.title_font.render("Exporting your map... Shouldn't take to long.", True, (255, 255, 255))
        tx, ty = text.get_width(), text.get_height()

        self.screen.blit(text, (self.WIDTH/2-tx/2, self.HEIGHT/2-ty/2))

        pg.display.flip()
    
    def save_map(self) -> None:
        self.show_map_preview()

        for sellpoint in self.map.sell_points:
            silo = messagebox.askyesno(f"Sellpoint: {sellpoint+1} - Silo?", "Do you want this to be the farm silo? Players cannot sell crops here and the farm can have only one!", icon="question")
            self.map.sell_points[sellpoint]["silo"] = silo
            
            if silo: self.map.sell_points[sellpoint]["name"] = "Farm Silo"
            else:
                self.map.sell_points[sellpoint]["name"] = simpledialog.askstring(f"Sellpoint: {sellpoint+1} - Name", "What do you want to name this sellpoint?")

        self.show_export_screen()

        self.map.export()

        messagebox.showinfo("Done!", "Your map has finished exporting! The program will exit now.")

        self.quit = True
        pg.quit()
        exit()
    
    def select_step_obj(self, object_index: int) -> None:
        if self.step == 0:
            self.current_road = object_index
        elif self.step == 1:
            self.current_pdk = object_index
   
    def add_step_object(self) -> None:
        obj_label = "Object"
        action = lambda: None
        index = len(self.placement_buttons)

        if self.step == 0:
            obj_label = "Road"
            action = lambda: self.select_step_obj(index)

            self.current_road += 1
            self.map.add_road(self.current_road)

        elif self.step == 1:
            obj_label = "Paddock"

        elif self.step == 2:
            obj_label = "Sell Point / Silo"

        self.placement_buttons.append(Button(self.screen, 350, len(self.placement_buttons)*60+300, 200, 50,
                                             (50, 50, 50), (100, 100, 100), (255, 255, 255), f"{obj_label}: {len(self.placement_buttons)+1}", 30,
                                             (10, 10, 10, 10), 0, 0, True, action))

    def next_step(self) -> None:
        self.step += 1

        if self.step == 1 or self.step == 2:
            self.add_btn.hide()
            if self.step == 2: self.next_step_btn.set_text("Finish map!")

        elif self.step == 3:
            last_pdk = list(self.map.paddocks.keys())[-1]
            last_sellpoint = list(self.map.sell_points.keys())[-1]

            if self.map.paddocks[last_pdk]["gate"] is None:
                del self.map.paddocks[last_pdk]
                self.current_pdk -= 1
            if self.map.sell_points[last_sellpoint]["rotation"] is None:
                del self.map.sell_points[last_sellpoint]
                self.current_sellpoint -= 1

            self.save_map()
        else:
            self.add_btn.show()

        self.placement_buttons = []

    def draw_point_connections(self, points: List[Tuple[int, int]], color: Tuple[int, int, int]) -> None:
        for i, point in enumerate(points):
            pg.draw.circle(self.screen, color, point, 5)

            if i > 0:
                pg.draw.line(self.screen, color, point, points[i-1])

    def draw_step_visualizations(self, draw_all=False) -> None:
        mouse_pos = pg.mouse.get_pos()

        if self.step == 0 or draw_all:
            self.draw_point_connections(self.map.roads[self.current_road], (0, 255, 0))
            
        if self.step == 1 or draw_all:
            for i in range(self.current_pdk+1):
                if self.map.paddocks[i]["gate"] is None:
                    if self.map.paddocks[i]["center"] is None: return

                    connections = [self.map.paddocks[i]["center"], (mouse_pos[0], mouse_pos[1])]
                else:
                    connections = [self.map.paddocks[i]["center"], self.map.paddocks[i]["gate"]]

                seed(i)
                self.draw_point_connections(connections, (randint(0, 255), randint(0, 255), randint(0, 255)))
                
                tx, ty = self.map.paddocks[i]["center"]
                self.screen.blit(self.body_font.render(str(i+1), True, (255, 255, 255)), (tx, ty))
        
        if self.step == 2 or draw_all:
            for i in range(self.current_sellpoint+1):
                if self.map.sell_points[i]["rotation"] is None:
                    if self.map.sell_points[i]["location"] is None: return

                    x, y = mouse_pos

                    x -= self.last_sellpoint_pos[0]
                    y -= self.last_sellpoint_pos[1]

                    rotation = -degrees(atan2(y, x)) - 180
                else:
                    rotation = self.map.sell_points[i]["rotation"]
                
                blitRotate(self.screen, self.sell_point_img, self.map.sell_points[i]["location"], (self.sellpoint_w/2, self.sellpoint_h/2), rotation)

                tx, ty = self.map.sell_points[i]["location"]
                self.screen.blit(self.body_font.render(str(i+1), True, (255, 255, 255)), (tx+30, ty))

    def process_step_1_event(self, mouse_btn: int, x: int, y: int) -> None:
        if mouse_btn == 1:
            self.map.roads[self.current_road].append((x, y))
        
        elif mouse_btn == 3:
            if len(self.map.roads[self.current_road]) > 0:
                self.map.roads[self.current_road].pop(-1)

    def process_step_2_event(self, mouse_btn: int, x: int, y: int)  -> None:
        if mouse_btn == 1:
            if self.map.paddocks[self.current_pdk]["center"] == None:
                self.map.paddocks[self.current_pdk]["center"] = (x, y)
            else:
                self.map.paddocks[self.current_pdk]["gate"] = (x, y)
                self.current_pdk += 1
                self.map.add_paddock(self.current_pdk)
                self.add_step_object()

        elif mouse_btn == 3:
            if self.map.paddocks[self.current_pdk]["gate"] is None:
                self.map.paddocks[self.current_pdk]["center"] = None
            else:
                self.map.paddocks[self.current_pdk]["gate"] = None                                

    def process_step_3_event(self, mouse_btn: int, x: int, y: int) -> None:
        if mouse_btn == 1:
            if self.map.sell_points[self.current_sellpoint]["location"] == None:
                self.map.sell_points[self.current_sellpoint]["location"] = (x, y)
                self.last_sellpoint_pos = (x, y)
            else:
                x, y = pg.mouse.get_pos()

                x -= self.last_sellpoint_pos[0]
                y -= self.last_sellpoint_pos[1]

                self.map.sell_points[self.current_sellpoint]["rotation"] = -degrees(atan2(y, x)) - 180
                self.current_sellpoint += 1
                self.map.add_sellpoint(self.current_sellpoint)
                self.add_step_object()

        elif mouse_btn == 3:
            if self.map.sell_points[self.current_sellpoint]["rotation"] is None:
                self.map.sell_points[self.current_sellpoint]["location"] = None
            else:
                self.map.sell_points[self.current_sellpoint]["rotation"] = None   
    
    def process_step_event(self, mouse_btn: int) -> None:
        if not self.map.rect.collidepoint(pg.mouse.get_pos()): return

        mouse_pos = pg.mouse.get_pos()

        lx = int(self.screen.get_width() - mouse_pos[0])
        ly = int(self.map.image.get_height() - mouse_pos[1])

        if self.step == 0: self.process_step_1_event(mouse_btn, mouse_pos[0], mouse_pos[1])
        elif self.step == 1: self.process_step_2_event(mouse_btn, mouse_pos[0], mouse_pos[1])
        elif self.step == 2: self.process_step_3_event(mouse_btn, mouse_pos[0], mouse_pos[1])

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

        while not self.quit:
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
    main()
    #testing()
