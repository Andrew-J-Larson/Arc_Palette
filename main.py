import ttkbootstrap as tb
from ttkbootstrap import Style
from ttkbootstrap.widgets import Meter
import tkinter as tk
import sv_ttk
import math
from PIL import Image, ImageTk, ImageDraw
import os
from threading import Thread
import random
from tkinter import ttk
from Arc_API.Arc_API import arc_API
import customtkinter as ctk
import pywinstyles
import utils
import darkdetect

class color_picker(tk.Canvas):
    def __init__(self, parent, image_path,size,arc_api, max_colors=10, tab=0, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Arguments
        self.tab = tab
        self.arc_api = arc_api
        self.max_colors = max_colors

        # Sizing
        self.width, self.height = size
        self.center_x = self.width / 2
        self.center_y = self.height / 2
        min_dimension = min(self.width, self.height)

        # Set circle sizes proportional to the canvas size
        self.selected_size = int(min_dimension * 0.038)  # 5% of the smaller dimension
        self.unselected_size = int(min_dimension * 0.031)
        self.border_width_selected_size = int((min_dimension * 0.039) /3.4)
        self.border_width_unselected_size = int((min_dimension * 0.039) /3.5)

        # Circle Info
        self.circles = []
        self.current_circle = None

        # Defualt Settings
        self.mode = "light"
        self.alpha = 0.7
        self.intensity = 1

        self.image_path=image_path
        self.img = self.generate_color_picker_canvas()
        self.dot_grid_image = utils.path_to_img(self.image_path, (self.width, self.height))
        self.create_image(0, 0, anchor=tk.NW, image=self.dot_grid_image)

        self.config(width=self.width, height=self.height, bg=None, highlightthickness=0)
       
        # Color Picker Detection
        self.bind("<Button-1>", self.on_canvas_click)
        self.bind("<B1-Motion>", self.on_canvas_drag)
        self.bind("<ButtonRelease-1>", self.on_canvas_release)


    def get_point_data(self, limit,pos,get_rgb=True): # esures that a x and y point is within the range of the canvas
        pos_x, pos_y = pos
        rgb = None
        x = min(max(limit.x, 0), pos_x)
        y = min(max(limit.y, 0), pos_y)

        if get_rgb == True:
            rgb = self.get_rgb_at_coordinate(x, y)

        return (x,y,rgb)
   
    def spawn_circle(self,pos,rgb,size,border_size,outline_color='white',):
        x,y=pos
        circle_id = self.create_oval(
                x - size, y - size,
                x + size, y + size,
                fill=self.rgb_to_hex(rgb), outline=outline_color, width=border_size
            )
        return circle_id
   
    def update_circle_data(self,x,y,rgb):
        self.current_circle['x'] = x
        self.current_circle['y'] = y
        self.current_circle['rgb'] = rgb

    def on_canvas_click(self,event):
        self.current_circle = None
        x, y, rgb = self.get_point_data(event,(self.width,self.height))

        for circle in self.circles:
            if self.is_within_circle(event.x, event.y, circle):
                self.current_circle = circle
                break
       
        if self.current_circle != None:
            self.delete(self.current_circle['id'])
            self.current_circle['id'] = self.spawn_circle((x,y),rgb,self.selected_size, self.border_width_selected_size)
            self.update_circle_data(x,y,rgb)

        else:
            self.add_color(x=x,y=y)
       
    def on_canvas_drag(self, event):
        if self.current_circle is  not None:
            x, y, rgb = self.get_point_data(event,(self.width,self.height))
           
            self.coords(
                self.current_circle['id'], x - self.selected_size, y - self.selected_size,
                x + self.selected_size, y + self.selected_size
            )

            self.itemconfig(self.current_circle['id'], fill=self.rgb_to_hex(rgb))
            self.update_circle_data(x,y,rgb)

    def on_canvas_release(self, event):
        if self.current_circle is not None:
            self.delete(self.current_circle['id'])
            self.current_circle['id'] = self.spawn_circle((self.current_circle['x'],self.current_circle['y']),self.current_circle['rgb'],self.unselected_size,self.border_width_unselected_size)
            self.current_circle = None  

    def is_within_circle(self, x, y,circle, mod=2,):
        return (circle['x'] - (self.unselected_size + mod) <= x <= circle['x'] + (self.unselected_size + mod) and circle['y'] - (self.unselected_size + mod) <= y <= circle['y'] + (self.unselected_size + mod))

    def generate_color_picker_canvas(self):

        img = Image.new("RGBA", (self.width,self.height))
        draw = ImageDraw.Draw(img)
        for y in range(self.height):
            for x in range(self.width):
                r = int((x / self.width) * 255)
                g = int((y / self.height) * 255)
                b = 255 - int(((x / self.width) + (y / self.height)) / 2 * 255)
                draw.point((x, y), (r, g, b, 255))
        return img
   
    def get_rgb_at_coordinate(self, x, y):
        x = min(max(x, 0), self.width - 1)
        y = min(max(y, 0), self.height - 1)
        image = self.img
        image = image.convert('RGB')
        rgb = image.getpixel((x, y))
        return rgb
   
    def add_color(self,x=None, y=None):
        if len(self.circles) < self.max_colors:
            x = x if x is not None else self.center_x
            y = y if y is not None else self.center_y
            rgb = self.get_rgb_at_coordinate(x,y)
            new_circle = self.spawn_circle((x,y),rgb,self.unselected_size,self.border_width_unselected_size)
            self.circles.append({'id': new_circle, 'x': x, 'y': y, 'rgb': rgb})

    def remove_color(self,):
        if self.circles:
            last_circle = self.circles.pop()
            self.delete(last_circle['id'])

    def rgb_to_hex(self, rgb):
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
   
    def create_smooth_radial_gradient_thread(self,):
        thread = Thread(target=self.create_smooth_radial_gradient)
        thread.start()

    def set_theme(self,):
        colors = []
        if self.arc_api.auto_restart_arc == True:
            self.arc_api.close_arc()
            self.arc_api.kill_arc()
        for id, cirlce in enumerate(self.circles):
            colors.append((cirlce['rgb'][0],cirlce['rgb'][1],cirlce['rgb'][2],self.alpha))
        print(len(colors))
        if len(colors) < 2:
            print("single color")
            print(colors)
            self.arc_api.set_space_theme_color(self.tab,"blendedSingleColor",colors,self.mode,intensityFactor=self.intensity)
        else:
            self.arc_api.set_space_theme_color(self.tab,"blendedGradient",colors,self.mode,intensityFactor=self.intensity)
        if self.arc_api.auto_restart_arc == True:
            self.arc_api.open_arc()
       
    def set_alpha(self,alpha):
        self.alpha = float(alpha/100)
        print(float(alpha/100))


    def set_intensity(self,intensity):
        self.intensity = float(intensity/100)
        print(float(intensity/100))





class TransparentCanvas(tk.Canvas):
    def __init__(self, parent, image_path, *args, **kwargs):
        # Initialize the Canvas with parent and other options
        super().__init__(parent, *args, **kwargs)
        
        # Load the image with transparency
        self.image = Image.open(image_path)
        self.image_with_transparency = ImageTk.PhotoImage(self.image)
        
        # Set the canvas size to the image size
        self.config(width=self.image.width, height=self.image.height, bg=None, highlightthickness=0)
        
        # Add the image to the canvas
        self.create_image(0, 0, anchor=tk.NW, image=self.image_with_transparency)
        

            
class ImageButton:
    def __init__(self, button_frame, img_path, command_function, size=(20,20)):
        self.button_frame = button_frame
        self.button_display_img = Image.open(img_path)
        self.button_display_img = self.button_display_img.resize(size, Image.LANCZOS)
        self.button_imgtk = ImageTk.PhotoImage(self.button_display_img)
        self.button = ttk.Button(button_frame, image=self.button_imgtk, command=command_function)
        self.button.image = self.button_imgtk  # Keep a reference to the image
        self.button.config(image=self.button_imgtk,)
    def pack(self, **kwargs):
        self.button.pack(**kwargs)
def resource_path(relative_path):
    """ Fixes issues with PyInstaller """
    try:
        # PyInstaller creates a temp folder, path found in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class tab_bar(ttk.Notebook):
    def __init__(self, parent, tabs, tab_class, arc_api,window_color_mode, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.window_color_mode = window_color_mode
        self.tabs_count = 0
        self.canvas_h, self.canvas_w = (335, 335)
        self.arc_api = arc_api
       
        for i in range(tabs):
            tab_instance = tab_class(self,self.arc_api)
            self.add(tab_instance, text=f"Tab {i+1}")

            
class space_tab(ttk.Frame):
    def __init__(self, notebook,arc_api, *args, **kwargs):
        super().__init__(notebook, *args, **kwargs)
        def slider_set_alpha(value):
            color_pick.set_alpha(float(value))
        def slider_set_intensity(value):
            print(value)
            color_pick.set_intensity(float(value))
        # Accessing canvas_h and canvas_w from the parent (tab_bar)
        self.canvas_h = notebook.canvas_h
        self.canvas_w = notebook.canvas_w
        self.window_color_mode = notebook.window_color_mode
        self.arc_api = arc_api
        color_pick_tab_frame = ttk.Frame(self, background=None,)
        color_pick_tab_frame.pack(side='top',padx=10,pady=10,)


        color_pick_frame = ttk.Frame(color_pick_tab_frame, background=None,borderwidth=5, relief="solid")
        color_pick_frame.pack(side="top")
        # Pass canvas_h and canvas_w to color_picker
        color_pick = color_picker(color_pick_frame, resource_path(f"resources/img/{self.window_color_mode}/dot_pad.png"), (self.canvas_w, self.canvas_h), self.arc_api, tab=notebook.tabs_count)
        color_pick.pack()
        pywinstyles.set_opacity(color_pick_tab_frame, value=1)


        button_frame = ttk.Frame(color_pick_tab_frame,)
        button_frame.pack(side="top")
        button_frame2 = ttk.Frame(button_frame,)
        button_frame2.pack(side="left")
        minus_button = ImageButton(button_frame2, resource_path(f"resources/img/{self.window_color_mode}/minus_button.png"), color_pick.remove_color)
        minus_button.pack(pady=5,padx=5,side="left")
        slider_frame = ttk.Frame(button_frame,)
        slider_frame.pack(side="right")
        theme_button = ImageButton(button_frame2, resource_path(f"resources/img/{self.window_color_mode}/set_theme.png"), color_pick.set_theme)
        theme_button.pack(pady=5,padx=5,side="left",)
        plus_button = ImageButton(button_frame2, resource_path(f"resources/img/{self.window_color_mode}/plus_button.png"), color_pick.add_color)
        plus_button.pack(pady=5,padx=5,side="left")

        slider_alpha_frame = ttk.Frame(button_frame,)
        slider_alpha_frame.pack(side="top")
        alpha_label = ttk.Label(slider_alpha_frame,text="Opacity")
        alpha_label.pack(pady=5,padx=5,side="left")
        slider = ttk.Scale(slider_alpha_frame, from_=0, to=100, command=slider_set_alpha)
        slider.pack(pady=5,padx=5,side="right")

        slider_transparency_frame = ttk.Frame(button_frame,)
        slider_transparency_frame.pack(side="bottom")
        transparency_label = ttk.Label(slider_transparency_frame,text="Intensity")
        transparency_label.pack(pady=5,padx=5,side="left")
        slider2 = ttk.Scale(slider_transparency_frame, from_=0, to=100, command=slider_set_intensity)
        slider2.pack(pady=5,padx=5,side="right")


        notebook.tabs_count += 1


class Arc_Palette(tk.Tk):
    def __init__(self, window_color_mode):
        super().__init__()
        self.window_color_mode = window_color_mode
        self.title('Arc Palette')
        self.geometry("360x520")

        self.arc_api = arc_API()
        self.spaces_num = self.arc_api.get_number_of_spaces()
        self.tab_count = 0

        # BooleanVar to track the checkbox state
        self.auto_restart_var = tk.BooleanVar(value=self.arc_api.auto_restart_arc)

        check_box_frame = ttk.Frame(self,)
        check_box_frame.pack(side="bottom", fill='both', expand=True)

        notebook = tab_bar(self, self.spaces_num, space_tab, self.arc_api, self.window_color_mode)
        notebook.pack(fill='both', expand=True)
        pywinstyles.set_opacity(notebook, value=0.7)

        # Checkbox for Auto Restart Arc
        check_box = ttk.Checkbutton(check_box_frame, text="Auto Restart Arc",
                                    variable=self.auto_restart_var,
                                    command=self.set_auto_restart_arc)
        check_box.pack()
        pywinstyles.set_opacity(check_box_frame, value=0.7)
        self.apply_window_color_mode()

    def set_auto_restart_arc(self):
        # Update the auto_restart_arc attribute in arc_api
        self.arc_api.set_auto_restart_arc(self.auto_restart_var.get())

    def apply_window_color_mode(self):
        # Sets theme based off of system light/dark
        if theme == "Light":
            sv_ttk.set_theme("light")
            pywinstyles.apply_style(self, "acrylic")
        else:
            sv_ttk.set_theme("dark")
            pywinstyles.apply_style(self, "acrylic")


if __name__ == "__main__":
    theme = darkdetect.theme()
    arc_palette = Arc_Palette(theme)
    arc_palette.iconbitmap(resource_path("resources/img/icon.ico"))
    arc_palette.mainloop()
