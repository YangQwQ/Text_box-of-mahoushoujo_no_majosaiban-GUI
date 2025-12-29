"""样式编辑窗口模块"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageDraw
import re

from path_utils import get_available_fonts
from image_loader import clear_cache
from config import CONFIGS
from gui_style_components import ComponentEditor, COMPONENT_TYPES, COMPONENT_PROPERTIES

DEFAULT_VALUES = {
    "aspect_ratio": "3:1",
    "font_family": "font3",
    "font_size": 90,
    "text_color": "#FFFFFF",
    "bracket_color": "#EF4F54",
    "use_character_color": False,
    "shadow_color": "#000000",
    "shadow_offset_x": 4,
    "shadow_offset_y": 4,
    "textbox_x": 760,
    "textbox_y": 355,
    "textbox_width": 1579,
    "textbox_height": 445,
    "text_align": "left",
    "text_valign": "top"
}

PROCESSORS = {
    "aspect_ratio": lambda self, v: self.aspect_ratio_var.get() if hasattr(self, 'aspect_ratio_var') else v,
    "font_family": lambda self, v: self.font_family_var.get() if hasattr(self, 'font_family_var') else v,
    "font_size": lambda self, v: int(self.font_size_var.get() or 90) if hasattr(self, 'font_size_var') else v,
    "text_color": lambda self, v: self.text_color_var.get() if hasattr(self, 'text_color_var') else v,
    "bracket_color": lambda self, v: self.bracket_color_var.get() if hasattr(self, 'bracket_color_var') else v,
    "use_character_color": lambda self, v: self.use_character_color_var.get() if hasattr(self, 'use_character_color_var') else v,
    "shadow_color": lambda self, v: self.shadow_color_var.get() if hasattr(self, 'shadow_color_var') else v,
    "shadow_offset_x": lambda self, v: int(self.shadow_offset_x_var.get() or 4) if hasattr(self, 'shadow_offset_x_var') else v,
    "shadow_offset_y": lambda self, v: int(self.shadow_offset_y_var.get() or 4) if hasattr(self, 'shadow_offset_y_var') else v,
    "textbox_x": lambda self, v: int(self.textbox_x_var.get() or 760) if hasattr(self, 'textbox_x_var') else v,
    "textbox_y": lambda self, v: int(self.textbox_y_var.get() or 355) if hasattr(self, 'textbox_y_var') else v,
    "textbox_width": lambda self, v: int(self.textbox_width_var.get() or 1579) if hasattr(self, 'textbox_width_var') else v,
    "textbox_height": lambda self, v: int(self.textbox_height_var.get() or 445) if hasattr(self, 'textbox_height_var') else v,
    "text_align": lambda self, v: self._get_mapping_value("text_align_var", {"左": "left", "中": "center", "右": "right"}, "左", v),
    "text_valign": lambda self, v: self._get_mapping_value("text_valign_var", {"上": "top", "中": "middle", "下": "bottom"}, "上", v)
}

def validate_and_update_color_preview(color_var, preview_label, color_value=None):
    """通用的颜色验证和预览更新函数"""
    if color_value is None:
        color_value = color_var.get()
    
    # 验证颜色格式
    if _validate_color_format(color_value):
        if preview_label and preview_label.winfo_exists():
            preview_label.configure(background=color_value)
        return True
    return False

def _validate_color_format(color_value):
    """验证颜色格式 - 通用版本"""
    pattern = r'^#([A-Fa-f0-9]{6})$'
    return re.match(pattern, color_value) is not None

class StyleWindow:
    """样式编辑窗口"""
    
    def __init__(self, parent, core, gui):
        self.parent = parent
        self.core = core
        self.gui = gui
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("样式编辑")
        self.window.geometry("600x800")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()

        # 添加图标
        from path_utils import set_window_icon
        set_window_icon(self.window)
        
        # 最大图层值
        self._max_layer = 0

        # 添加窗口关闭事件处理
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 组件编辑器实例存储
        self.component_editors = {}
        
        # 用于优化滚动的变量
        self._scroll_scheduled = False
        self._last_scroll_time = 0
        self._scroll_after_id = None

        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 创建主容器框架
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建Notebook用于标签页
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建常规设置标签页
        self.general_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.general_frame, text="常规设置")
        
        # 创建图层设置标签页
        self.layers_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.layers_frame, text="图层设置")
        
        # 设置常规标签页
        self._setup_general_tab()
        
        # 按钮框架
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=10, padx=20)
        
        ttk.Button(button_frame, text="保存", command=self._on_save_apply).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="应用", command=self._on_apply).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="取消", command=self._on_close).pack(
            side=tk.RIGHT, padx=5
        )
        
        # 延迟设置图层标签页
        self.window.after(100, self._setup_layers_tab)
    
    def _setup_general_tab(self):
        """设置常规设置标签页"""
        # 创建滚动容器
        self.general_canvas = tk.Canvas(self.general_frame, highlightthickness=0, bg='white')
        v_scrollbar = ttk.Scrollbar(self.general_frame, orient=tk.VERTICAL, command=self.general_canvas.yview)
        
        # 配置canvas
        self.general_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # 创建可滚动框架
        scrollable_frame = ttk.Frame(self.general_canvas, style='Scrollable.TFrame')
        
        # 创建窗口并设置合适的宽度
        canvas_frame = self.general_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # 优化滚动性能：减少滚动时的更新频率
        def on_canvas_configure(event):
            # 更新Canvas的滚动区域
            bbox = self.general_canvas.bbox("all")
            if bbox:
                self.general_canvas.configure(scrollregion=bbox)
            
            # 设置框架宽度为Canvas宽度（减去滚动条宽度）
            canvas_width = event.width
            if canvas_width > 10:
                # 设置一个最小宽度，确保内容不会被压缩
                min_width = 450
                frame_width = max(min_width, canvas_width)
                self.general_canvas.itemconfig(canvas_frame, width=frame_width)
        
        def on_frame_configure(event):
            # 延迟更新滚动区域，避免频繁更新
            if not self._scroll_scheduled:
                self._scroll_scheduled = True
                self._scroll_after_id = self.window.after(50, self._update_general_scroll_region)
        
        # 绑定事件
        self.general_canvas.bind("<Configure>", on_canvas_configure)
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        # 绑定鼠标滚轮事件
        def on_mouse_wheel(event):
            # 优化滚动：使用更平滑的滚动
            delta = -1 if event.delta > 0 else 1
            self.general_canvas.yview_scroll(delta, "units")
            return "break"
        
        # 绑定滚轮事件
        self.general_canvas.bind_all("<MouseWheel>", on_mouse_wheel)
        
        # 布局滚动组件
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.general_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加内部边距
        content_frame = ttk.Frame(scrollable_frame, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置文件管理部分
        self._setup_style_management(content_frame)
        
        # 图片比例设置
        self._setup_aspect_ratio(content_frame)
        
        # 字体设置
        self._setup_font_settings(content_frame)
        
        # 文本位置设置
        self._setup_text_settings(content_frame)
        
        # 粘贴图像设置
        self._setup_paste_image_settings(content_frame)
        
        # 初始更新一次滚动区域
        self.window.after(100, self._update_general_scroll_region)
        
        # 禁用所有下拉框的鼠标滚轮
        self._disable_combobox_wheel(content_frame)
    
    def _setup_layers_tab(self):
        """设置图层标签页"""
        # 创建滚动容器
        self.layers_canvas = tk.Canvas(self.layers_frame, highlightthickness=0, bg='white')
        v_scrollbar = ttk.Scrollbar(self.layers_frame, orient=tk.VERTICAL, command=self.layers_canvas.yview)
        
        # 配置canvas
        self.layers_canvas.configure(yscrollcommand=v_scrollbar.set)
        
        # 创建可滚动框架
        self.layers_scrollable_frame = ttk.Frame(self.layers_canvas, style='Scrollable.TFrame')
        
        # 创建窗口并设置合适的宽度
        canvas_frame = self.layers_canvas.create_window((0, 0), window=self.layers_scrollable_frame, anchor="nw")
        
        # 优化滚动性能
        def on_canvas_configure(event):
            bbox = self.layers_canvas.bbox("all")
            if bbox:
                self.layers_canvas.configure(scrollregion=bbox)
            
            canvas_width = event.width
            if canvas_width > 10:
                min_width = 450
                frame_width = max(min_width, canvas_width)
                self.layers_canvas.itemconfig(canvas_frame, width=frame_width)
        
        def on_frame_configure(event):
            if not self._scroll_scheduled:
                self._scroll_scheduled = True
                self._scroll_after_id = self.window.after(50, self._update_layers_scroll_region)
        
        # 绑定事件
        self.layers_canvas.bind("<Configure>", on_canvas_configure)
        self.layers_scrollable_frame.bind("<Configure>", on_frame_configure)
        
        # 绑定鼠标滚轮事件
        def on_mouse_wheel(event):
            delta = -1 if event.delta > 0 else 1
            self.layers_canvas.yview_scroll(delta, "units")
            return "break"
        
        # 绑定滚轮事件
        self.layers_canvas.bind_all("<MouseWheel>", on_mouse_wheel)
        
        # 布局滚动组件
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.layers_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加内部边距
        content_frame = ttk.Frame(self.layers_scrollable_frame, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 图片组件设置
        self._setup_image_components(content_frame)
        
        # 初始更新一次滚动区域
        self.window.after(100, self._update_layers_scroll_region)
    
    def _update_general_scroll_region(self):
        """更新常规标签页滚动区域"""
        self._scroll_scheduled = False
        bbox = self.general_canvas.bbox("all")
        if bbox:
            self.general_canvas.configure(scrollregion=bbox)
    
    def _update_layers_scroll_region(self):
        """更新图层标签页滚动区域"""
        self._scroll_scheduled = False
        bbox = self.layers_canvas.bbox("all")
        if bbox:
            self.layers_canvas.configure(scrollregion=bbox)
    
    def _disable_combobox_wheel(self, parent):
        """禁用所有下拉框的鼠标滚轮"""
        for widget in parent.winfo_children():
            if isinstance(widget, ttk.Combobox):
                # 绑定事件，阻止鼠标滚轮改变值
                widget.bind("<MouseWheel>", lambda e: "break")
                widget.bind("<Button-4>", lambda e: "break")  # Linux
                widget.bind("<Button-5>", lambda e: "break")  # Linux
            elif isinstance(widget, tk.Frame) or isinstance(widget, ttk.Frame):
                # 递归处理子控件
                self._disable_combobox_wheel(widget)
    
    def _setup_style_management(self, parent):
        """设置配置文件管理部分"""
        style_frame = ttk.LabelFrame(parent, text="样式配置文件", padding="10")
        style_frame.pack(fill=tk.X, pady=10)
        
        # 样式选择
        ttk.Label(style_frame, text="当前样式:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 创建选择框架
        selection_frame = ttk.Frame(style_frame)
        selection_frame.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # 获取可用样式列表
        available_styles = list(CONFIGS.style_configs.keys())
        self.style_var = tk.StringVar(value=CONFIGS.current_style)
        
        self.style_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.style_var,
            values=available_styles,
            state="readonly"
        )
        self.style_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.style_combo.bind("<<ComboboxSelected>>", self._on_style_selected)
        
        # 配置列权重
        style_frame.columnconfigure(1, weight=1)
        
        # 禁用下拉框的鼠标滚轮
        self.style_combo.bind("<MouseWheel>", lambda e: "break")
        self.style_combo.bind("<Button-4>", lambda e: "break")
        self.style_combo.bind("<Button-5>", lambda e: "break")
    
    def _setup_aspect_ratio(self, parent):
        """设置图片比例部分"""
        ratio_frame = ttk.LabelFrame(parent, text="图片比例设置", padding="10")
        ratio_frame.pack(fill=tk.X, pady=10)
        
        # 比例选择
        self.aspect_ratio_var = tk.StringVar(value=CONFIGS.style.aspect_ratio)
        
        # 使用Frame将三个选项放在同一行
        ratio_options_frame = ttk.Frame(ratio_frame)
        ratio_options_frame.pack(fill=tk.X, pady=5)
        
        # 创建单选框选项，放在同一行
        ttk.Label(ratio_options_frame, text="比例:").pack(side=tk.LEFT, padx=(0, 10))
        
        for ratio, text in [("3:1", "3:1 (默认)"), ("5:4", "5:4"), ("16:9", "16:9")]:
            ttk.Radiobutton(
                ratio_options_frame,
                text=text,
                variable=self.aspect_ratio_var,
                value=ratio
            ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(
            ratio_frame,
            text="注：修改比例仅改变图片高度，宽度固定为2560像素",
            font=("", 8),
            foreground="gray"
        ).pack(anchor=tk.W, pady=5)
    
    def _setup_font_settings(self, parent):
        """设置字体相关设置"""
        font_frame = ttk.LabelFrame(parent, text="字体设置", padding="10")
        font_frame.pack(fill=tk.X, pady=10)
        
        # 对话框字体和字号放在同一行
        font_row_frame = ttk.Frame(font_frame)
        font_row_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(font_row_frame, text="文本字体:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 获取可用字体列表
        available_fonts = get_available_fonts()
        self.font_family_var = tk.StringVar(value=CONFIGS.style.font_family)
        
        font_combo = ttk.Combobox(
            font_row_frame,
            textvariable=self.font_family_var,
            values=available_fonts,
            state="readonly",
            width=15
        )
        font_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # 禁用下拉框的鼠标滚轮
        font_combo.bind("<MouseWheel>", lambda e: "break")
        font_combo.bind("<Button-4>", lambda e: "break")
        font_combo.bind("<Button-5>", lambda e: "break")
        
        ttk.Label(font_row_frame, text="字号:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.font_size_var = tk.StringVar(value=str(CONFIGS.style.font_size))
        font_size_entry = ttk.Entry(
            font_row_frame,
            textvariable=self.font_size_var,
            width=8
        )
        font_size_entry.pack(side=tk.LEFT)
        
        # 文字颜色和阴影颜色在同一行
        color_frame = ttk.Frame(font_frame)
        color_frame.pack(fill=tk.X, pady=5)
        
        # 文字颜色
        ttk.Label(color_frame, text="文字颜色:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.text_color_var = tk.StringVar(value=CONFIGS.style.text_color)
        text_color_entry = ttk.Entry(
            color_frame,
            textvariable=self.text_color_var,
            width=12
        )
        text_color_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 文字颜色预览
        self.text_color_preview = ttk.Label(
            color_frame,
            text="   ",
            background=self.text_color_var.get(),
            relief="solid",
            width=3
        )
        self.text_color_preview.pack(side=tk.LEFT, padx=(0, 20))
        
        # 阴影颜色
        ttk.Label(color_frame, text="阴影颜色:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.shadow_color_var = tk.StringVar(value=CONFIGS.style.shadow_color)
        shadow_color_entry = ttk.Entry(
            color_frame,
            textvariable=self.shadow_color_var,
            width=12
        )
        shadow_color_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 阴影颜色预览
        self.shadow_color_preview = ttk.Label(
            color_frame,
            text="   ",
            background=self.shadow_color_var.get(),
            relief="solid",
            width=3
        )
        self.shadow_color_preview.pack(side=tk.LEFT)
        
        # 阴影偏移设置
        shadow_offset_frame = ttk.Frame(font_frame)
        shadow_offset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(shadow_offset_frame, text="阴影偏移:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        # 阴影X偏移
        ttk.Label(shadow_offset_frame, text="X:", width=2).pack(side=tk.LEFT, padx=(0, 2))
        self.shadow_offset_x_var = tk.StringVar(value=str(CONFIGS.style.shadow_offset_x))
        shadow_x_entry = ttk.Entry(shadow_offset_frame, textvariable=self.shadow_offset_x_var, width=6)
        shadow_x_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        # 阴影Y偏移
        ttk.Label(shadow_offset_frame, text="Y:", width=2).pack(side=tk.LEFT, padx=(0, 2))
        self.shadow_offset_y_var = tk.StringVar(value=str(CONFIGS.style.shadow_offset_y))
        shadow_y_entry = ttk.Entry(shadow_offset_frame, textvariable=self.shadow_offset_y_var, width=6)
        shadow_y_entry.pack(side=tk.LEFT)
        
        # 绑定颜色变化
        self.text_color_var.trace_add("write", self._update_text_color_preview)
        self.shadow_color_var.trace_add("write", self._update_shadow_color_preview)
        
        # 使用角色颜色作为强调色
        self.use_character_color_var = tk.BooleanVar(value=CONFIGS.style.use_character_color)
        use_char_color_cb = ttk.Checkbutton(
            font_frame,
            text="使用角色颜色作为强调色",
            variable=self.use_character_color_var,
            command=self._update_bracket_color_entry_state
        )
        use_char_color_cb.pack(anchor=tk.W, pady=5)
        
        # 强调颜色
        bracket_color_frame = ttk.Frame(font_frame)
        bracket_color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(bracket_color_frame, text="强调颜色:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.bracket_color_var = tk.StringVar(value=CONFIGS.style.bracket_color)
        self.bracket_color_entry = ttk.Entry(
            bracket_color_frame,
            textvariable=self.bracket_color_var,
            width=12
        )
        self.bracket_color_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 强调颜色预览
        self.bracket_color_preview = ttk.Label(
            bracket_color_frame,
            text="   ",
            background=self.bracket_color_var.get(),
            relief="solid",
            width=3
        )
        self.bracket_color_preview.pack(side=tk.LEFT)
        
        # 绑定强调颜色变化
        self.bracket_color_var.trace_add("write", self._update_bracket_color_preview)
        
        # 更新强调颜色输入框状态
        self._update_bracket_color_entry_state()
    
    def _setup_text_settings(self, parent):
        """设置文本设置"""
        text_frame = ttk.LabelFrame(parent, text="文本设置", padding="10")
        text_frame.pack(fill=tk.X, pady=10)
        
        # 第一行：文本框区域设置
        region_frame = ttk.Frame(text_frame)
        region_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(region_frame, text="文本区域:", width=7).pack(side=tk.LEFT, padx=(0, 5))
        
        # X坐标
        ttk.Label(region_frame, text="X", width=1).pack(side=tk.LEFT, padx=(0, 4))
        self.textbox_x_var = tk.StringVar(value=str(CONFIGS.style.textbox_x))
        x_entry = ttk.Entry(region_frame, textvariable=self.textbox_x_var, width=5)
        x_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Y坐标
        ttk.Label(region_frame, text="Y", width=1).pack(side=tk.LEFT, padx=(0, 4))
        self.textbox_y_var = tk.StringVar(value=str(CONFIGS.style.textbox_y))
        y_entry = ttk.Entry(region_frame, textvariable=self.textbox_y_var, width=5)
        y_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 宽度
        ttk.Label(region_frame, text="宽", width=2).pack(side=tk.LEFT, padx=(0, 2))
        self.textbox_width_var = tk.StringVar(value=str(CONFIGS.style.textbox_width))
        width_entry = ttk.Entry(region_frame, textvariable=self.textbox_width_var, width=4)
        width_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 高度
        ttk.Label(region_frame, text="高", width=2).pack(side=tk.LEFT, padx=(0, 2))
        self.textbox_height_var = tk.StringVar(value=str(CONFIGS.style.textbox_height))
        height_entry = ttk.Entry(region_frame, textvariable=self.textbox_height_var, width=4)
        height_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 预览按钮（放在第一行最右边）
        preview_btn = ttk.Button(
            region_frame,
            text="预览区域",
            command=self._show_textbox_preview,
            width=8
        )
        preview_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 第二行：对齐设置
        align_frame = ttk.Frame(text_frame)
        align_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(align_frame, text="文本对齐:", width=7).pack(side=tk.LEFT, padx=(0, 5))
        
        # 水平对齐
        ttk.Label(align_frame, text="水平", width=4).pack(side=tk.LEFT, padx=(0, 2))
        
        self.text_align_var = tk.StringVar(value=CONFIGS.style.text_align)
        align_mapping = {"left": "左", "center": "中", "right": "右"}
        align_display = align_mapping.get(CONFIGS.style.text_align, "左")
        
        align_combo = ttk.Combobox(
            align_frame,
            textvariable=self.text_align_var,
            values=["左", "中", "右"],
            state="readonly",
            width=6
        )
        align_combo.set(align_display)
        align_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        # 禁用下拉框的鼠标滚轮
        align_combo.bind("<MouseWheel>", lambda e: "break")
        align_combo.bind("<Button-4>", lambda e: "break")
        align_combo.bind("<Button-5>", lambda e: "break")
        
        # 垂直对齐
        ttk.Label(align_frame, text="垂直", width=5).pack(side=tk.LEFT, padx=(0, 2))
        
        self.text_valign_var = tk.StringVar(value=CONFIGS.style.text_valign)
        valign_mapping = {"top": "上", "middle": "中", "bottom": "下"}
        valign_display = valign_mapping.get(CONFIGS.style.text_valign, "上")
        
        valign_combo = ttk.Combobox(
            align_frame,
            textvariable=self.text_valign_var,
            values=["上", "中", "下"],
            state="readonly",
            width=6
        )
        valign_combo.set(valign_display)
        valign_combo.pack(side=tk.LEFT)
        
        # 禁用下拉框的鼠标滚轮
        valign_combo.bind("<MouseWheel>", lambda e: "break")
        valign_combo.bind("<Button-4>", lambda e: "break")
        valign_combo.bind("<Button-5>", lambda e: "break")
        
        # 说明
        ttk.Label(
            text_frame,
            text="注：文本框区域定义文字和图片的绘制范围",
            font=("", 8),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(5, 0))

    def _show_textbox_preview(self):
        """显示文本框区域预览"""
        if not self.gui:
            return
        
        if (hasattr(self, '_is_previewing') and self._is_previewing):
            self._clear_textbox_preview()

        # 获取预览管理器
        preview_manager = self.gui.preview_manager
        
        # 获取当前缩放比例
        zoom_level = preview_manager.zoom_level
        
        # 创建显示图的副本
        display_copy = preview_manager.displayed_image.copy()
        draw = ImageDraw.Draw(display_copy, 'RGBA')
        
        # 计算文本框区域
        try:
            textbox_x = int(self.textbox_x_var.get() or 0)
            textbox_y = int(self.textbox_y_var.get() or 0)
            textbox_width = int(self.textbox_width_var.get() or 0)
            textbox_height = int(self.textbox_height_var.get() or 0)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return
        
        # 将实际区域坐标缩放到当前显示图的大小
        scaled_x1 = int(textbox_x * zoom_level)
        scaled_y1 = int(textbox_y * zoom_level)
        scaled_x2 = int((textbox_x + textbox_width) * zoom_level)
        scaled_y2 = int((textbox_y + textbox_height) * zoom_level)
        
        # 确保坐标在显示图范围内
        img_width, img_height = display_copy.size
        if scaled_x1 < 0:
            scaled_x1 = 0
        if scaled_y1 < 0:
            scaled_y1 = 0
        if scaled_x2 > img_width:
            scaled_x2 = img_width
        if scaled_y2 > img_height:
            scaled_y2 = img_height
        
        # 绘制矩形边框（红色，宽度3）
        draw.rectangle([scaled_x1, scaled_y1, scaled_x2, scaled_y2], 
                    outline=(255, 0, 0, 255), width=3)
        
        # 绘制半透明填充
        draw.rectangle([scaled_x1, scaled_y1, scaled_x2, scaled_y2], 
                    fill=(255, 0, 0, 50))
        
        # 保存当前显示状态
        self._original_display = preview_manager.displayed_image
        self._display_with_box = display_copy
        
        # 更新显示图
        preview_manager.displayed_image = display_copy
        preview_manager._update_displayed_image()
        
        # 标记正在预览
        self._is_previewing = True

    def _clear_textbox_preview(self):
        """清除文本框区域预览"""
        if not hasattr(self, '_is_previewing') or not self._is_previewing:
            return
        
        # 获取预览管理器
        preview_manager = self.gui.preview_manager
        
        # 恢复原始预览图
        if hasattr(self, '_original_display') and self._original_display:
            preview_manager.displayed_image = self._original_display
            preview_manager._update_displayed_image()
        
        # 清除标记
        self._is_previewing = False
        if hasattr(self, '_original_display'):
            delattr(self, '_original_display')
        if hasattr(self, '_preview_with_box'):
            delattr(self, '_preview_with_box')

    def _setup_paste_image_settings(self, parent):
        """设置粘贴图像设置"""
        paste_image_frame = ttk.LabelFrame(parent, text="粘贴图像设置", padding="10")
        paste_image_frame.pack(fill=tk.X, pady=10)
        
        # 第一行：生效情况选择
        enabled_frame = ttk.Frame(paste_image_frame)
        enabled_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(enabled_frame, text="生效情况:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        # 创建生效情况变量
        paste_enabled_var = tk.StringVar(value=CONFIGS.style.paste_image_settings.get("enabled", "off"))
        
        # 存储单选按钮变量
        self.paste_radio_vars = {}
        
        # 选项列表：始终、混合内容、关闭
        options = [
            ("始终", "always"),
            ("混合内容", "mixed"),
            ("关闭", "off")
        ]
        
        # 创建一个框架来容纳所有单选按钮
        radio_frame = ttk.Frame(enabled_frame)
        radio_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        for option in options:
            text, value = option[0], option[1]
            # 使用索引作为键
            var = tk.BooleanVar(value=(paste_enabled_var.get() == value))
            self.paste_radio_vars[value] = var
            
            radio = ttk.Radiobutton(
                radio_frame,
                text=text,
                variable=var,
                width=7,
                command=lambda v=value: self._on_paste_enabled_changed(v)
            )
            radio.pack(side=tk.LEFT, padx=(0, 10))
        
        # 存储主变量
        self.paste_enabled_var = paste_enabled_var
        
        # 第二行：位置和大小设置
        position_frame = ttk.Frame(paste_image_frame)
        position_frame.pack(fill=tk.X, pady=5)
        
        # 创建一个框架来容纳所有位置相关的控件，包括预览按钮
        controls_frame = ttk.Frame(position_frame)
        controls_frame.pack(fill=tk.X)
        
        # 在左侧创建位置设置区域
        position_controls_frame = ttk.Frame(controls_frame)
        position_controls_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(position_controls_frame, text="图片区域:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        # X坐标
        ttk.Label(position_controls_frame, text="X", width=1).pack(side=tk.LEFT, padx=(0, 4))
        self.paste_image_x_var = tk.StringVar(value=str(CONFIGS.style.paste_image_settings.get("x", 0)))
        paste_x_entry = ttk.Entry(position_controls_frame, textvariable=self.paste_image_x_var, width=5)
        paste_x_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Y坐标
        ttk.Label(position_controls_frame, text="Y", width=1).pack(side=tk.LEFT, padx=(0, 4))
        self.paste_image_y_var = tk.StringVar(value=str(CONFIGS.style.paste_image_settings.get("y", 0)))
        paste_y_entry = ttk.Entry(position_controls_frame, textvariable=self.paste_image_y_var, width=5)
        paste_y_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 宽度
        ttk.Label(position_controls_frame, text="宽", width=2).pack(side=tk.LEFT, padx=(0, 2))
        self.paste_image_width_var = tk.StringVar(value=str(CONFIGS.style.paste_image_settings.get("width", 300)))
        paste_width_entry = ttk.Entry(position_controls_frame, textvariable=self.paste_image_width_var, width=4)
        paste_width_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 高度
        ttk.Label(position_controls_frame, text="高", width=2).pack(side=tk.LEFT, padx=(0, 2))
        self.paste_image_height_var = tk.StringVar(value=str(CONFIGS.style.paste_image_settings.get("height", 200)))
        paste_height_entry = ttk.Entry(position_controls_frame, textvariable=self.paste_image_height_var, width=4)
        paste_height_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 预览按钮（放在第二行的最右边）
        paste_preview_btn = ttk.Button(
            controls_frame,
            text="预览区域",
            command=self._show_paste_image_preview,
            width=8
        )
        paste_preview_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 第三行：填充方式
        fill_mode_frame = ttk.Frame(paste_image_frame)
        fill_mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(fill_mode_frame, text="填充方式:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        self.paste_fill_mode_var = tk.StringVar(value=CONFIGS.style.paste_image_settings.get("fill_mode", "fit"))
        
        # 使用Frame将选项放在一行
        fill_options_frame = ttk.Frame(fill_mode_frame)
        fill_options_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        fill_modes = [
            ("适应边界", "fit"),
            ("适应宽度", "width"),
            ("适应高度", "height")
        ]
        
        for text, value in fill_modes:
            ttk.Radiobutton(
                fill_options_frame,
                text=text,
                variable=self.paste_fill_mode_var,
                value=value,
                width=7
            ).pack(side=tk.LEFT, padx=(0,10))
        
        # 第四行：对齐设置
        align_frame = ttk.Frame(paste_image_frame)
        align_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(align_frame, text="对齐方式:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        
        # 水平对齐
        ttk.Label(align_frame, text="水平", width=4).pack(side=tk.LEFT, padx=(0, 2))
        
        self.paste_align_var = tk.StringVar(value=CONFIGS.style.paste_image_settings.get("align", "center"))
        paste_align_mapping = {"left": "左", "center": "中", "right": "右"}
        paste_align_display = paste_align_mapping.get(self.paste_align_var.get(), "中")
        
        paste_align_combo = ttk.Combobox(
            align_frame,
            textvariable=self.paste_align_var,
            values=["左", "中", "右"],
            state="readonly",
            width=6
        )
        paste_align_combo.set(paste_align_display)
        paste_align_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        # 禁用下拉框的鼠标滚轮
        paste_align_combo.bind("<MouseWheel>", lambda e: "break")
        paste_align_combo.bind("<Button-4>", lambda e: "break")
        paste_align_combo.bind("<Button-5>", lambda e: "break")
        
        # 垂直对齐
        ttk.Label(align_frame, text="垂直", width=5).pack(side=tk.LEFT, padx=(0, 2))
        
        self.paste_valign_var = tk.StringVar(value=CONFIGS.style.paste_image_settings.get("valign", "middle"))
        paste_valign_mapping = {"top": "上", "middle": "中", "bottom": "下"}
        paste_valign_display = paste_valign_mapping.get(self.paste_valign_var.get(), "中")
        
        paste_valign_combo = ttk.Combobox(
            align_frame,
            textvariable=self.paste_valign_var,
            values=["上", "中", "下"],
            state="readonly",
            width=6
        )
        paste_valign_combo.set(paste_valign_display)
        paste_valign_combo.pack(side=tk.LEFT)
        
        # 禁用下拉框的鼠标滚轮
        paste_valign_combo.bind("<MouseWheel>", lambda e: "break")
        paste_valign_combo.bind("<Button-4>", lambda e: "break")
        paste_valign_combo.bind("<Button-5>", lambda e: "break")
        
        # 说明
        ttk.Label(
            paste_image_frame,
            text="注：混合内容指同时含有图片和文本",
            font=("", 8),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(5, 0))
        
    def _on_paste_enabled_changed(self, selected_option):
        """粘贴图像生效情况改变事件"""
        # 更新主变量
        self.paste_enabled_var.set(selected_option)
        
        # 更新所有单选按钮状态
        for option, var in self.paste_radio_vars.items():
            var.set(selected_option == option)

    def _show_paste_image_preview(self):
        """显示粘贴图像区域预览"""
        if not self.gui:
            return
        
        if hasattr(self, '_is_paste_previewing') and self._is_paste_previewing:
            self._clear_paste_image_preview()

        # 获取预览管理器
        preview_manager = self.gui.preview_manager
        
        # 确保有显示图片
        if not preview_manager.displayed_image:
            messagebox.showinfo("提示", "请先生成预览图")
            return
        
        # 获取当前缩放比例
        zoom_level = preview_manager.zoom_level
        
        # 创建显示图的副本
        display_copy = preview_manager.displayed_image.copy()
        draw = ImageDraw.Draw(display_copy, 'RGBA')
        
        # 计算粘贴图像区域
        try:
            paste_x = int(self.paste_image_x_var.get() or 0)
            paste_y = int(self.paste_image_y_var.get() or 0)
            paste_width = int(self.paste_image_width_var.get() or 300)
            paste_height = int(self.paste_image_height_var.get() or 200)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return
        
        # 将实际区域坐标缩放到当前显示图的大小
        scaled_x1 = int(paste_x * zoom_level)
        scaled_y1 = int(paste_y * zoom_level)
        scaled_x2 = int((paste_x + paste_width) * zoom_level)
        scaled_y2 = int((paste_y + paste_height) * zoom_level)
        
        # 确保坐标在显示图范围内
        img_width, img_height = display_copy.size
        scaled_x1 = 0 if scaled_x1 < 0 else scaled_x1
        scaled_y1 = 0 if scaled_y1 < 0 else scaled_y1
        scaled_x2 = img_width if scaled_x2 > img_width else scaled_x2
        scaled_y2 = img_height if scaled_y2 > img_height else scaled_y2
        
        # 绘制矩形边框（蓝色，宽度3）
        draw.rectangle([scaled_x1, scaled_y1, scaled_x2, scaled_y2], outline=(0, 0, 255, 255), width=3)
        
        # 绘制半透明填充
        draw.rectangle([scaled_x1, scaled_y1, scaled_x2, scaled_y2], fill=(0, 0, 255, 50))
        
        # 保存当前显示状态
        self._original_paste_display = preview_manager.displayed_image
        self._display_with_paste_box = display_copy
        
        # 更新显示图
        preview_manager.displayed_image = display_copy
        preview_manager._update_displayed_image()
        
        # 标记正在预览
        self._is_paste_previewing = True

    def _clear_paste_image_preview(self):
        """清除粘贴图像区域预览"""
        if not hasattr(self, '_is_paste_previewing') or not self._is_paste_previewing:
            return
        
        # 获取预览管理器
        preview_manager = self.gui.preview_manager
        
        # 恢复原始预览图
        if hasattr(self, '_original_paste_display') and self._original_paste_display:
            preview_manager.displayed_image = self._original_paste_display
            preview_manager._update_displayed_image()
        
        # 清除标记
        self._is_paste_previewing = False
        if hasattr(self, '_original_paste_display'):
            delattr(self, '_original_paste_display')
        if hasattr(self, '_display_with_paste_box'):
            delattr(self, '_display_with_paste_box')
            
    def _setup_image_components(self, parent):
        """设置组件设置 - 简化版本"""
        components_frame = ttk.LabelFrame(parent, text="组件设置", padding="10")
        components_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 组件容器框架
        self.components_container = ttk.Frame(components_frame)
        self.components_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加组件按钮框架 - 修改：重置按钮在左边，添加组件按钮在右边
        add_button_frame = ttk.Frame(components_frame)
        add_button_frame.pack(fill=tk.X, pady=5)
        
        # 重置按钮（新增）
        ttk.Button(
            add_button_frame,
            text="重置组件",
            command=self._reset_components,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 单个添加组件按钮，点击后弹出选择菜单
        ttk.Button(
            add_button_frame,
            text="添加组件",
            command=self._show_add_component_menu,
            width=15
        ).pack(side=tk.LEFT)
        
        # 加载现有组件
        self._load_image_components()
    
    def _reset_components(self):
        """重置组件到默认配置"""
        # 确认操作
        if not messagebox.askyesno("确认重置", "确定要重置所有组件到默认配置吗？\n这将覆盖当前所有组件设置。"):
            return
        
        # 获取当前样式名称
        current_style_name = self.style_var.get()
        
        # 调用现有的样式选择方法，它会从默认配置中加载
        if current_style_name in CONFIGS.style_configs:
            # 从默认样式中获取组件配置
            default_components = CONFIGS.style.default_config[current_style_name].get("image_components", [])
            
            if default_components:
                # 清理缓存
                clear_cache()

                # 更新当前样式的组件
                CONFIGS.style.image_components = default_components
                
                # 重新加载组件
                self._load_image_components()
                
                # 更新状态
                self.gui.update_status(f"已重置样式 '{current_style_name}' 的组件到默认配置")
            else:
                messagebox.showwarning("警告", f"默认配置中没有找到样式 '{current_style_name}' 的组件设置")
    
    def _show_add_component_menu(self):
        """显示添加组件的选择菜单"""
        # 创建菜单
        menu = tk.Menu(self.window, tearoff=0)
        
        # 添加菜单项
        for comp_type, display_name in COMPONENT_TYPES.items():
            menu.add_command(
                label=display_name,
                command=lambda ct=comp_type: self._add_component(ct)
            )
        
        # 显示菜单
        try:
            menu.tk_popup(*self.window.winfo_pointerxy())
        finally:
            menu.grab_release()
    
    def _add_component(self, component_type):
        """添加新的组件 - 简化版本"""
        # 直接使用当前最大图层值+1作为新图层值
        new_layer = self._max_layer + 1
        self._max_layer = new_layer
        
        # 使用组件属性配置中的默认值
        if component_type in COMPONENT_PROPERTIES:
            defaults = COMPONENT_PROPERTIES[component_type]["defaults"]
            component_config = defaults.copy()
            component_config["type"] = component_type
            component_config["layer"] = new_layer
        else:
            return

        # 创建新组件的编辑器
        self._create_component_editor(component_config)
        
        # 立即按图层顺序重新排序所有UI组件
        self._reorder_component_editors()

    def _create_component_editor(self, component_config):
        """创建组件编辑器"""
        # 确保有layer属性
        if 'layer' not in component_config:
            # 分配新的图层值
            existing_layers = []
            for editor in self.component_editors.values():
                config = editor.get_current_config()
                if 'layer' in config:
                    existing_layers.append(config['layer'])
            component_config['layer'] = max(existing_layers) + 1 if existing_layers else 0
        
        # 创建编辑器实例
        editor = ComponentEditor(self.components_container, self, component_config)
        
        # 使用图层值作为键
        layer = component_config.get('layer', 0)
        key = f"layer_{layer}"
        
        # 存储编辑器
        self.component_editors[key] = editor

        return key

    def _remove_component_by_layer(self, layer):
        """根据图层值删除组件"""
        # 查找匹配的组件键
        component_key = None
        for key, editor in self.component_editors.items():
            config = editor.get_current_config()
            if config.get("layer", -1) == layer:
                component_key = key
                break
        
        if component_key and component_key in self.component_editors:
            # 从UI中移除组件的编辑器
            editor = self.component_editors[component_key]
            editor.destroy()
            del self.component_editors[component_key]

    def _reorder_component_editors(self):
        """重新排序组件编辑器"""
        # 从容器中移除所有编辑器
        for editor in self.component_editors.values():
            editor.pack_forget()
        
        # 收集所有组件配置
        component_configs = []
        for editor in self.component_editors.values():
            config = editor.get_current_config()
            component_configs.append((editor, config))
        
        # 按图层值降序排序（图层值大的在上，图层值小的在下）
        component_configs.sort(key=lambda x: x[1].get("layer", 0), reverse=True)
        
        # 按新的图层顺序重新pack
        for editor, config in component_configs:
            editor.pack(fill=tk.X, pady=3, padx=2)
    
    def _load_image_components(self):
        """加载图片组件"""
        # 清空现有组件编辑器
        for editor in self.component_editors.values():
            editor.destroy()
        self.component_editors.clear()
        
        # 重置最大图层值
        self._max_layer = 0
        
        # 从当前样式中加载组件
        current_components = CONFIGS.style.image_components
        
        # 加载所有组件，同时计算最大图层值
        for component in current_components:
            # 移除组件中的id属性
            if 'id' in component:
                del component['id']
            
            # 确保有layer属性，并更新最大图层值
            layer = component.get('layer', 0)
            if 'layer' not in component:
                component['layer'] = layer
                
            # 更新最大图层值
            if layer > self._max_layer:
                self._max_layer = layer
            
            # 创建编辑器实例
            editor = ComponentEditor(self.components_container, self, component)
            
            # 使用图层值作为键
            key = f"layer_{layer}"
            self.component_editors[key] = editor
        
        # 初始加载时也需要按图层排序并显示
        self._reorder_component_editors()
    
    def _on_style_selected(self, event=None):
        style_name = self.style_var.get()
        
        # 清理所有缓存（包括背景、角色和组件缓存）
        clear_cache()

        # 加载新样式配置
        CONFIGS.apply_style(style_name)
        
        # 完全重新加载组件 - 确保清理旧组件
        for widget in self.components_container.winfo_children():
            widget.destroy()
        
        self.component_editors.clear()  # 清空编辑器字典
        self._load_image_components()
        
        # 完全重新构建UI显示
        self._rebuild_ui_from_style()

        # 通知主界面刷新预览
        self.gui.update_preview()
        self.gui.update_status(f"已应用样式: {style_name}")
    
    def _rebuild_ui_from_style(self):
        """完全重新构建UI从当前样式"""
        # 将对齐方式中英文映射
        align_mapping = {"left": "左", "center": "中", "right": "右"}
        valign_mapping = {"top": "上", "middle": "中", "bottom": "下"}

        # 图片比例
        self.aspect_ratio_var.set(CONFIGS.style.aspect_ratio)
        
        # 字体设置
        self.font_family_var.set(CONFIGS.style.font_family)
        self.font_size_var.set(str(CONFIGS.style.font_size))
        self.text_color_var.set(CONFIGS.style.text_color)
        self.use_character_color_var.set(CONFIGS.style.use_character_color)
        self.bracket_color_var.set(CONFIGS.style.bracket_color)
        
        # 更新预览
        self._update_text_color_preview()
        self._update_bracket_color_preview()
        self._update_bracket_color_entry_state()
        
        # 文本设置 - 更新文本框区域和对齐方式
        self.textbox_x_var.set(str(CONFIGS.style.textbox_x))
        self.textbox_y_var.set(str(CONFIGS.style.textbox_y))
        self.textbox_width_var.set(str(CONFIGS.style.textbox_width))
        self.textbox_height_var.set(str(CONFIGS.style.textbox_height))
        
        
        align_display = align_mapping.get(CONFIGS.style.text_align, "左")
        valign_display = valign_mapping.get(CONFIGS.style.text_valign, "上")
        
        # 直接设置Combobox的值
        self.text_align_var.set(align_display)
        self.text_valign_var.set(valign_display)
            
        # 粘贴图像设置
        paste_settings = CONFIGS.style.paste_image_settings
        current_enabled = paste_settings.get("enabled", "off")
        self.paste_enabled_var.set(current_enabled)

        # 更新所有单选按钮状态
        if hasattr(self, 'paste_radio_vars'):
            for option, var in self.paste_radio_vars.items():
                var.set(current_enabled == option)
        
        # 更新位置和大小
        self.paste_image_x_var.set(str(paste_settings.get("x", 0)))
        self.paste_image_y_var.set(str(paste_settings.get("y", 0)))
        self.paste_image_width_var.set(str(paste_settings.get("width", 300)))
        self.paste_image_height_var.set(str(paste_settings.get("height", 200)))
        
        # 更新填充方式
        self.paste_fill_mode_var.set(paste_settings.get("fill_mode", "fit"))
        paste_align_display = align_mapping.get(paste_settings.get("align", "center"), "中")
        paste_valign_display = valign_mapping.get(paste_settings.get("valign", "middle"), "中")
        
        self.paste_align_var.set(paste_align_display)
        self.paste_valign_var.set(paste_valign_display)
    
    def _update_bracket_color_entry_state(self):
        """更新强调颜色输入框状态"""
        if self.use_character_color_var.get():
            # 禁用强调颜色输入框和预览
            self.bracket_color_entry.config(state="disabled")
            self.bracket_color_preview.config(state="disabled")
        else:
            # 启用强调颜色输入框和预览
            self.bracket_color_entry.config(state="normal")
            self.bracket_color_preview.config(state="normal")
        color_value = self.bracket_color_var.get()
        if not validate_and_update_color_preview(self.bracket_color_var, None, color_value):
            self.bracket_color_preview.configure(background="#EF4F54")
    
    def _update_text_color_preview(self, *args):
        """更新文字颜色预览 - 使用通用函数"""
        color_value = self.text_color_var.get()
        if not validate_and_update_color_preview(self.text_color_var, self.text_color_preview, color_value):
            self.text_color_preview.configure(background="#FFFFFF")

    def _update_bracket_color_preview(self, *args):
        """更新强调颜色预览 - 使用通用函数"""
        color_value = self.bracket_color_var.get()
        if not validate_and_update_color_preview(self.bracket_color_var, self.bracket_color_preview, color_value):
            self.bracket_color_preview.configure(background="#EF4F54")

    def _update_shadow_color_preview(self, *args):
        """更新阴影颜色预览 - 使用通用函数"""
        color_value = self.shadow_color_var.get()
        if not validate_and_update_color_preview(self.shadow_color_var, self.shadow_color_preview, color_value):
            self.shadow_color_preview.configure(background="#000000")
    
    def _get_mapping_value(self, attr_name, mapping, default_display, default_value):
        display = getattr(self, attr_name).get() if hasattr(self, attr_name) else default_display
        return mapping.get(display, default_value)
    
    def _collect_style_data(self):
        """收集所有样式设置数据"""
        # 收集组件数据 - 从所有编辑器获取当前配置
        image_components = []
        
        for editor in self.component_editors.values():
            # 获取当前配置
            final_config = editor.get_current_config()
            image_components.append(final_config)
        
        # 按图层排序（图层值小的在下，图层值大的在上）
        image_components.sort(key=lambda x: x.get("layer", 0))
        
        # 收集所有样式设置，使用默认值作为基础
        style_data = {}
        
        # 收集常规设置，总是包含所有字段
        for key, value in DEFAULT_VALUES.items():
            if key in PROCESSORS:
                value = PROCESSORS[key](self, value)
            style_data[key] = value
        
        # 添加粘贴图像设置（需要特殊处理，因为这是一个嵌套字典）
        paste_settings = {}
        paste_settings["enabled"] = self.paste_enabled_var.get()
        paste_settings["x"] = int(self.paste_image_x_var.get() or 0)
        paste_settings["y"] = int(self.paste_image_y_var.get() or 0)
        paste_settings["width"] = int(self.paste_image_width_var.get() or 300)
        paste_settings["height"] = int(self.paste_image_height_var.get() or 200)
        paste_settings["fill_mode"] = self.paste_fill_mode_var.get()
        paste_align_mapping = {"左": "left", "中": "center", "右": "right"}
        paste_settings["align"] = paste_align_mapping.get(self.paste_align_var.get(), "center")
        paste_valign_mapping = {"上": "top", "中": "middle", "下": "bottom"}
        paste_settings["valign"] = paste_valign_mapping.get(self.paste_valign_var.get(), "middle")
        
        # 添加组件配置
        if image_components:
            style_data["image_components"] = image_components
        
        # 添加粘贴图像设置
        if paste_settings:
            style_data["paste_image_settings"] = paste_settings
        
        return style_data

    def _on_apply(self):
        """应用样式设置"""
        style_name = self.style_var.get()
        style_data = self._collect_style_data()
        
        # 检查背景组件数量
        image_components = style_data.get("image_components", [])
        background_components = [comp for comp in image_components if comp.get("type") == "background" and comp.get("enabled", True)]

        if len(background_components) > 1:
            messagebox.showerror("错误", "只能创建一个背景组件。请删除多余的背景组件后再保存。")
            return False

        # 验证颜色格式
        color_errors = []
        
        # 验证文字颜色
        text_color = style_data.get("text_color", self.text_color_var.get())
        if not validate_and_update_color_preview(self.text_color_var, None, text_color):
            color_errors.append("文字颜色")
        
        # 验证强调颜色
        bracket_color = style_data.get("bracket_color", self.bracket_color_var.get())
        if not validate_and_update_color_preview(self.bracket_color_var, None, bracket_color):
            color_errors.append("强调颜色")
        
        # 验证阴影颜色
        shadow_color = style_data.get("shadow_color", self.shadow_color_var.get())
        if not validate_and_update_color_preview(self.shadow_color_var, None, shadow_color):
            color_errors.append("阴影颜色")
        
        if color_errors:
            error_msg = f"以下颜色格式无效，请输入有效的颜色值（例如：#FFFFFF）：\n{', '.join(color_errors)}"
            messagebox.showerror("错误", error_msg)
            return False
        
        # 验证数值输入
        try:
            if not 8 <= style_data["font_size"] <= 250:
                messagebox.showerror("错误", "字体大小必须在8到250之间")
                return False
                                
        except ValueError as e:
            messagebox.showerror("错误", f"数值格式错误: {str(e)}")
            return False
        
        # 更新样式配置
        success = CONFIGS.update_style(style_name, style_data)

        if success:
            # 刷新GUI预览
            if self.gui:
                self.gui.update_preview()
                # 更新状态显示
                self.gui.update_status(f"样式已应用: {self.style_var.get()}")
        return True
    
    def _on_save_apply(self):
        """保存并应用样式设置"""
        if self._on_apply():
            self._on_close()

    def _on_close(self):
        """处理窗口关闭事件"""

        # 取消所有延迟执行的任务
        if hasattr(self, '_scroll_after_id'):
            self.window.after_cancel(self._scroll_after_id)
        
        # 解绑鼠标滚轮事件
        if hasattr(self, 'general_canvas'):
            self.general_canvas.unbind_all("<MouseWheel>")
        if hasattr(self, 'layers_canvas'):
            self.layers_canvas.unbind_all("<MouseWheel>")
        
        # 销毁窗口
        self.window.destroy()
