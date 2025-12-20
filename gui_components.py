"""GUI组件模块"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class PreviewManager:
    """预览管理器"""

    def __init__(self, gui):
        self.gui = gui
        self.core = gui.core

        # 预览图片的原始副本 Image.Image类型
        self.original_image = None
        self.displayed_image = None
        self.photo_image = None
        
        # 预览相关变量
        self.canvas = None
        self.scrollbar_x = None
        self.scrollbar_y = None
        self.frame = None
        self.image_item = None
        self.info_frame = None
        self.preview_info = [None] * 3
        self._fit_to_window_enabled = True

        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 3.0

    def setup_preview_frame(self, parent):
        """设置预览框架 - 支持滚动和缩放"""
        # 创建主框架
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 预览信息区域（放在图片上方，横向排列三个信息项）
        self.info_frame = ttk.Frame(main_frame)
        self.info_frame.pack(fill=tk.X, pady=(0, 5))
        
        preview_info_label = [None] * 3
        self.preview_info = [None] * 3

        # 创建三个标签用于显示预览信息，横向排列
        for i in range(3):
            self.preview_info[i] = tk.StringVar(value="")
            preview_info_label[i] = ttk.Label(
                self.info_frame, textvariable=self.preview_info[i]
            )
            preview_info_label[i].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # 控制按钮框架
        control_frame = ttk.Frame(self.info_frame)
        control_frame.pack(side=tk.RIGHT, padx=5)
        
        # 缩放控制
        ttk.Button(control_frame, text="重置", command=self.reset_view, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="适应窗口", command=self.fit_to_window, width=10).pack(side=tk.LEFT, padx=2)
        
        # 更新预览按钮
        ttk.Button(control_frame, text="刷新", command=self.gui.update_preview, width=6).pack(side=tk.LEFT, padx=2)

        # 创建滚动框架
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建水平滚动条
        self.scrollbar_x = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建垂直滚动条
        self.scrollbar_y = ttk.Scrollbar(scroll_frame)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建Canvas用于显示图片
        self.canvas = tk.Canvas(
            scroll_frame,
            bg='#f0f0f0',
            xscrollcommand=self.scrollbar_x.set,
            yscrollcommand=self.scrollbar_y.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        self.scrollbar_x.config(command=self.canvas.xview)
        self.scrollbar_y.config(command=self.canvas.yview)
        
        # 创建图片容器
        self.frame = ttk.Frame(self.canvas)
        self.image_item = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        
        # 绑定Canvas大小变化事件
        self.canvas.bind("<Configure>", self._on_canvas_configure)
    
    def _on_canvas_configure(self, event):
        """Canvas大小变化时调整图片位置"""
        if self.photo_image:
            # 更新Canvas的滚动区域
            self._update_scroll_region()
            
            # 如果开启了适应窗口模式，重新计算
            if hasattr(self, '_fit_to_window_enabled') and self._fit_to_window_enabled:
                self._calculate_fit_to_window()

    def _update_scroll_region(self):
        """更新滚动区域"""
        if self.photo_image:
            # 计算图片的实际显示大小
            img_width = self.photo_image.width()
            img_height = self.photo_image.height()
            
            # 设置Canvas的滚动区域
            self.canvas.config(scrollregion=(0, 0, img_width, img_height))
            
            # 更新滚动条状态
            self._update_scrollbars()


    def _update_scrollbars(self):
        """更新滚动条状态"""
        if not self.photo_image:
            return
            
        # 获取Canvas和图片的尺寸
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = self.photo_image.width()
        img_height = self.photo_image.height()
        
        # 检查是否需要显示滚动条
        need_horizontal = img_width > canvas_width
        need_vertical = img_height > canvas_height
        
        # 先隐藏所有滚动条
        self.scrollbar_x.pack_forget()
        self.scrollbar_y.pack_forget()
        
        # 重新按需显示滚动条
        if need_horizontal:
            # 确保水平滚动条放在canvas下方
            self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X, before=self.canvas if not need_vertical else None)
        
        if need_vertical:
            # 确保垂直滚动条放在canvas右侧
            self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y, before=self.canvas if not need_horizontal else None)
        
        # 确保canvas重新pack到正确位置
        self.canvas.pack_forget()
        if need_horizontal and need_vertical:
            # 两个滚动条都存在时，canvas放在左上角
            self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        elif need_horizontal:
            # 只有水平滚动条时，canvas在上面
            self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        elif need_vertical:
            # 只有垂直滚动条时，canvas在左边
            self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        else:
            # 没有滚动条时
            self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _apply_zoom(self, new_zoom, center_x=None, center_y=None):
        """应用缩放"""
        if not self.original_image:
            return
            
        old_zoom = self.zoom_level
        self.zoom_level = new_zoom
        
        # 计算缩放后的图片尺寸
        original_width, original_height = self.original_image.size
        new_width = int(original_width * self.zoom_level)
        new_height = int(original_height * self.zoom_level)
        
        # 缩放图片
        self.displayed_image = self.original_image.resize(
            (new_width, new_height), 
            Image.Resampling.BILINEAR
        )
        
        # 更新显示
        self._update_displayed_image()
        
        # 保持缩放中心点位置
        if center_x is not None and center_y is not None and old_zoom > 0:
            # 计算缩放比例变化
            scale_ratio = new_zoom / old_zoom
            
            # 计算新的滚动位置
            current_x = self.canvas.canvasx(0)
            current_y = self.canvas.canvasy(0)
            
            new_x = center_x - (center_x - current_x) * scale_ratio
            new_y = center_y - (center_y - current_y) * scale_ratio
            
            # 设置新的滚动位置
            if new_width > 0:
                self.canvas.xview_moveto(max(0, min(new_x / new_width, 1)))
            if new_height > 0:
                self.canvas.yview_moveto(max(0, min(new_y / new_height, 1)))

    def _start_pan(self, event):
        """开始拖拽"""
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.config(cursor="fleur")
        return "break"

    def _on_pan(self, event):
        """处理拖拽"""
        if not self.is_panning:
            return
            
        # 计算移动距离
        delta_x = event.x - self.pan_start_x
        delta_y = event.y - self.pan_start_y
        
        # 移动Canvas视图
        self.canvas.xview_scroll(-delta_x, "pixels")
        self.canvas.yview_scroll(-delta_y, "pixels")
        
        # 更新起始位置
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        return "break"

    def _stop_pan(self, event):
        """停止拖拽"""
        self.is_panning = False
        self.canvas.config(cursor="")
        return "break"

    def _update_displayed_image(self):
        """更新显示的图片"""
        if not self.displayed_image:
            return
            
        # 转换为PhotoImage
        self.photo_image = ImageTk.PhotoImage(self.displayed_image)
        
        # 清除之前的图片
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # 创建新的Label显示图片
        image_label = ttk.Label(self.frame, image=self.photo_image)
        image_label.pack()
        
        # 更新滚动区域
        self._update_scroll_region()

    def _calculate_fit_to_window(self):
        """计算适应窗口的缩放比例"""
        if not self.original_image:
            return
            
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        original_width, original_height = self.original_image.size
        
        # 计算适应窗口的缩放比例
        width_ratio = canvas_width / original_width
        height_ratio = canvas_height / original_height
        fit_ratio = min(width_ratio, height_ratio)
        
        # 设置缩放级别
        self.zoom_level = max(self.min_zoom, min(fit_ratio, self.max_zoom))
        
        # 应用缩放
        self._apply_zoom(self.zoom_level)

    def fit_to_window(self):
        """适应窗口大小"""
        self._fit_to_window_enabled = True
        self._calculate_fit_to_window()

    def reset_view(self):
        """重置视图"""
        self._fit_to_window_enabled = False
        self.zoom_level = 1.0
        self._apply_zoom(1.0)
        
        # 重置滚动位置
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def handle_window_resize(self, event):
        """处理窗口大小变化事件"""
        if event.widget == self.gui.root:
            if hasattr(self, '_fit_to_window_enabled') and self._fit_to_window_enabled:
                self._calculate_fit_to_window()
            else:
                self._update_scrollbars()

    def update_preview(self):
        """更新预览"""
        try:
            # 获取预览图片和信息
            self.original_image, info = self.core.generate_preview()
            self.displayed_image = self.original_image.copy()
            
            # 如果启用了适应窗口模式，重新计算缩放
            if hasattr(self, '_fit_to_window_enabled') and self._fit_to_window_enabled:
                self._calculate_fit_to_window()
            else:
                # 使用当前缩放级别
                self._apply_zoom(self.zoom_level)
            
            # 更新预览信息
            info_parts = info.split("\n")
            if len(info_parts) >= 3:
                for i in range(3):
                    self.preview_info[i].set(info_parts[i])

        except Exception as e:
            # 错误信息也分配到三个标签中
            error_msg = f"预览生成失败: {str(e)}"
            self.preview_info[0].set(error_msg)
            for i in range(1, 3):
                self.preview_info[i].set("")


class StatusManager:
    """状态管理器"""

    def __init__(self, gui):
        self.gui = gui
        self.status_var = None
        self.status_bar = None

    def setup_status_bar(self, parent, row):
        """设置状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(
            parent, textvariable=self.status_var, relief=tk.SUNKEN
        )
        self.status_bar.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    def update_status(self, message: str):
        """更新状态栏"""
        self.status_var.set(message)
        self.gui.root.update_idletasks()