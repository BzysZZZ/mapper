import os
from datetime import datetime
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import rasterio
import cv2

class ImageCropper:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Cropper")
        self.master.geometry("800x600")
        self.master.bind("<F12>", self.fit_to_window_height)

        self.image = None
        self.start_point = None
        self.end_point = None
        self.drawing = False
        self.scale = 1.0
        self.tool = "rectangle"  # 默认工具类型
        self.channels_to_display = [1, 2, 3]  # 默认显示第2、3、4通道（蓝、红、绿）
        self.drag_sensitivity = 1.0  # 默认拖动灵敏度

        self.canvas = tk.Canvas(master, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 标签显示有效宽度和高度
        self.size_label = tk.Label(master, text="x: 0, y: 0", height=1)
        self.size_label.place(relx=0, rely=1, anchor='sw')

        self.filename_label = tk.Label(master, text="No file loaded", anchor="se", height=1)
        self.filename_label.place(relx=1.0, rely=1.0, anchor='se')

        # 设置菜单栏
        self.menu_bar = tk.Menu(master)
        master.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=master.quit)
        file_menu.add_command(label="Close", command=self.close_image)

        tool_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tool_menu)
        tool_menu.add_command(label="Rectangle Tool", command=lambda: self.set_tool("rectangle"))
        tool_menu.add_command(label="Hand Tool", command=lambda: self.set_tool("hand"))

        # 添加灵敏度调节子菜单
        sensitivity_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Sensitivity", menu=sensitivity_menu)
        sensitivity_menu.add_command(label="Low", command=lambda: self.update_drag_sensitivity(0.5))
        sensitivity_menu.add_command(label="Medium", command=lambda: self.update_drag_sensitivity(1.0))
        sensitivity_menu.add_command(label="High", command=lambda: self.update_drag_sensitivity(2.0))

        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Control-MouseWheel>", self.on_mouse_wheel)

        self.offset_x = 0
        self.offset_y = 0
        self.last_drag_position = (0, 0)

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jp2;*.jpg;*.png")])
        if file_path:
            with rasterio.open(file_path) as src:
                self.image = src.read()
                channel_count = self.image.shape[0]

            # 获取文件名并显示在状态栏
            filename = os.path.basename(file_path)
            self.filename_label.config(text=f"File: {filename}")

            # 获取文件路径和其他初始化
            self.file_path = file_path
            self.scale = 1.0
            self.offset_x = 0
            self.offset_y = 0

            if channel_count == 10:
                self.display_image()
            else:
                messagebox.showerror("Error", f"Image must have exactly 10 channels, but this image has {channel_count} channels.")
                return

    def save_image(self):
        if self.image is not None and self.start_point and self.end_point:
            start_x = max(0, self.start_point[0])
            start_y = max(0, self.start_point[1])
            end_x = min(self.image.shape[2], self.end_point[0])
            end_y = min(self.image.shape[1], self.end_point[1])

            roi = self.image[:, start_y:end_y, start_x:end_x]

            file_dir = os.path.dirname(self.file_path)
            parent_dir_name = os.path.basename(file_dir)
            save_dir = os.path.join("D:/multi_img", parent_dir_name)
            os.makedirs(save_dir, exist_ok=True)

            current_time = datetime.now().strftime("%Y_%m_%d_%H%M%S")
            save_path = os.path.join(save_dir, f"{current_time}.jp2")

            with rasterio.open(save_path, 'w', driver='JP2OpenJPEG',
                               height=roi.shape[1], width=roi.shape[2],
                               count=roi.shape[0], dtype=roi.dtype) as dst:
                dst.write(roi)

            messagebox.showinfo("Info", f"Image saved successfully at {save_path}")
        else:
            messagebox.showwarning("Warning", "No image selected for saving.")

    def set_tool(self, tool):
        self.tool = tool
        self.canvas.delete("rect")
        self.start_point = None
        self.end_point = None
        self.size_label.config(text="x: 0, y: 0")

    def fit_to_window_height(self, event=None):
        """按F12时，以窗口高度适配比例居中显示图像"""
        if self.image is None:
            messagebox.showwarning("Warning", "No image loaded.")
            return

        # 计算窗口高度适配比例
        canvas_height = self.canvas.winfo_height()
        image_height = self.image.shape[1]  # 获取图像的高度（Y轴）
        self.scale = canvas_height / image_height

        # 重新计算偏移量以水平居中
        canvas_width = self.canvas.winfo_width()
        image_width = int(self.image.shape[2] * self.scale)  # 缩放后的图像宽度
        self.offset_x = (canvas_width - image_width) // 2  # 居中图像
        self.offset_y = 0  # 顶部对齐

        # 显示图像
        self.display_image()
    def display_image(self):
        if self.image is not None:
            display_image = self.image[self.channels_to_display]
            display_image = np.moveaxis(display_image, 0, -1)
            display_image = (display_image - display_image.min()) / (display_image.max() - display_image.min()) * 255
            display_image = display_image.astype(np.uint8)

            scaled_image = cv2.resize(display_image, (0, 0), fx=self.scale, fy=self.scale)
            height, width = scaled_image.shape[:2]
            self.tk_image = ImageTk.PhotoImage(image=Image.fromarray(scaled_image))
            self.canvas.config(width=width, height=height)
            self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.NW, image=self.tk_image)
            self.redraw_rectangle()

    def close_image(self):
        self.image = None
        self.canvas.delete("all")
        self.size_label.config(text="x: 0, y: 0")

    def on_mouse_down(self, event):
        if self.tool == "rectangle":
            self.start_point = (int((event.x - self.offset_x) / self.scale), int((event.y - self.offset_y) / self.scale))
            self.drawing = True
        elif self.tool == "hand":
            self.last_drag_position = (event.x, event.y)

    def on_mouse_move(self, event):
        if self.tool == "rectangle" and self.drawing:
            self.end_point = (int((event.x - self.offset_x) / self.scale), int((event.y - self.offset_y) / self.scale))
            self.redraw_rectangle()
        elif self.tool == "hand":
            dx = (event.x - self.last_drag_position[0]) * self.drag_sensitivity
            dy = (event.y - self.last_drag_position[1]) * self.drag_sensitivity
            self.offset_x += dx
            self.offset_y += dy
            self.last_drag_position = (event.x, event.y)
            self.display_image()

    def on_mouse_up(self, event):
        if self.tool == "rectangle":
            self.drawing = False
            self.end_point = (int((event.x - self.offset_x) / self.scale), int((event.y - self.offset_y) / self.scale))
            self.redraw_rectangle()

    def redraw_rectangle(self):
        if self.image is None or self.start_point is None or self.end_point is None:
            return
        self.canvas.delete("rect")
        if self.start_point and self.end_point:
            self.canvas.create_rectangle(
                self.start_point[0] * self.scale + self.offset_x, self.start_point[1] * self.scale + self.offset_y,
                self.end_point[0] * self.scale + self.offset_x, self.end_point[1] * self.scale + self.offset_y,
                outline="red", tags="rect"
            )
            valid_width = abs(min(self.end_point[0], self.image.shape[2]) - max(0, self.start_point[0]))
            valid_height = abs(min(self.end_point[1], self.image.shape[1]) - max(0, self.start_point[1]))
            self.size_label.config(text=f"x: {valid_width}, y: {valid_height}")

    def on_mouse_wheel(self, event):
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= scale_factor
        self.display_image()

    def update_drag_sensitivity(self, value):
        self.drag_sensitivity = value

def main():
    root = tk.Tk()
    app = ImageCropper(root)
    root.mainloop()

if __name__ == "__main__":
    main()
