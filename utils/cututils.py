import os
from datetime import datetime

import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import rasterio
import cv2

# 自定义图像裁剪小工具
class ImageCropper:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Cropper")
        self.master.geometry("800x600")

        self.image = None
        self.start_point = None
        self.end_point = None
        self.drawing = False
        self.scale = 1.0
        self.tool = "rectangle"  # 选择工具类型
        self.channels_to_display = [1, 2, 3]  # 默认显示第2、3、4通道（蓝、红、绿）

        self.canvas = tk.Canvas(master, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 添加左对齐的标签显示有效宽度和高度
        self.size_label = tk.Label(master, text="x: 0, y: 0", height=1)
        self.size_label.place(relx=0, rely=1, anchor='sw')  # 放在画布底部左侧

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
            # 打开文件并读取图像数据
            with rasterio.open(file_path) as src:
                self.image = src.read()  # 读取所有通道
                channel_count = self.image.shape[0]

            # 获取上一级目录名
            file_dir = os.path.dirname(file_path)
            parent_dir_name = os.path.basename(file_dir)  # 获取父目录名

            # 记录文件路径供后续保存操作使用
            self.file_path = file_path

            if self.image is None:
                messagebox.showerror("Error", "Failed to read the image. Please check the file format and try again.")
                return

            self.scale = 1.0
            self.offset_x = 0
            self.offset_y = 0

            # 检查通道数是否符合要求，并显示默认通道
            if channel_count == 10:  # 确保图像有10个通道
                self.display_image()

            else:
                messagebox.showerror("Error", f"Image must have exactly 10 channels, but this image has {channel_count} channels.")
                return

    def save_image(self):
        if self.image is not None and self.start_point and self.end_point:
            # 获取裁剪区域的坐标
            start_x = max(0, self.start_point[0])
            start_y = max(0, self.start_point[1])
            end_x = min(self.image.shape[2], self.end_point[0])
            end_y = min(self.image.shape[1], self.end_point[1])

            # 裁剪区域应用于所有通道
            roi = self.image[:, start_y:end_y, start_x:end_x]

            # 获取上一级目录名
            file_dir = os.path.dirname(self.file_path)
            parent_dir_name = os.path.basename(file_dir)

            # 构造保存目录
            save_dir = os.path.join("D:/multi_img", parent_dir_name)
            os.makedirs(save_dir, exist_ok=True)  # 创建保存目录（如果不存在）

            # 获取当前日期和时间，格式化为 yyyy_mm_dd_HHMMSS
            current_time = datetime.now().strftime("%Y_%m_%d_%H%M%S")

            # 生成保存文件的完整路径
            save_path = os.path.join(save_dir, f"{current_time}.jp2")

            # 保存图像为 JP2 格式
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
        self.size_label.config(text="x: 0, y: 0")  # 重置标签

    def display_image(self):
        if self.image is not None:
            display_image = self.image[self.channels_to_display]  # 选择指定的通道
            display_image = np.moveaxis(display_image, 0, -1)  # 变换轴顺序，以符合显示要求
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
        self.size_label.config(text="x: 0, y: 0")  # 重置标签

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
            dx = event.x - self.last_drag_position[0]
            dy = event.y - self.last_drag_position[1]
            self.offset_x += dx
            self.offset_y += dy
            self.display_image()

    def on_mouse_up(self, event):
        if self.tool == "rectangle":
            self.drawing = False
            self.end_point = (int((event.x - self.offset_x) / self.scale), int((event.y - self.offset_y) / self.scale))
            self.redraw_rectangle()

    def redraw_rectangle(self):
        self.canvas.delete("rect")
        if self.start_point and self.end_point:
            self.canvas.create_rectangle(
                self.start_point[0] * self.scale + self.offset_x, self.start_point[1] * self.scale + self.offset_y,
                self.end_point[0] * self.scale + self.offset_x, self.end_point[1] * self.scale + self.offset_y,
                outline="red", tags="rect"
            )
            # 计算有效宽度和高度
            valid_width = abs(min(self.end_point[0], self.image.shape[2]) - max(0, self.start_point[0]))
            valid_height = abs(min(self.end_point[1], self.image.shape[1]) - max(0, self.start_point[1]))
            self.size_label.config(text=f"x: {valid_width}, y: {valid_height}")

    def on_mouse_wheel(self, event):
        scale_factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= scale_factor
        self.display_image()

def main():
    root = tk.Tk()
    app = ImageCropper(root)
    root.mainloop()

if __name__ == "__main__":
    main()
