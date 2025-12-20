"""样式编辑窗口模块"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import re

from path_utils import get_resource_path, get_available_fonts
from config import CONFIGS

# 对齐方式的中英文映射
ALIGN_MAPPING = {
    "top-left": "左上",
    "top-center": "上中", 
    "top-right": "右上",
    "middle-left": "左中",
    "middle-center": "中心",
    "middle-right": "右中",
    "bottom-left": "左下",
    "bottom-center": "下中",
    "bottom-right": "右下",
    "custom": "自定义"
}

REVERSE_ALIGN_MAPPING = {v: k for k, v in ALIGN_MAPPING.items()}

# 组件的图层类型映射
COMPONENT_LAYER_TYPES = {
    "character": "角色",
    "textbox": "文本框",
    "namebox": "名称框",
    "extra": "额外组件"
}

class StyleWindow:
    """样式编辑窗口"""
    
    def __init__(self, parent, core, gui):
        self.parent = parent
        self.core = core
        self.gui = gui
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("样式编辑")
        self.window.geometry("500x700")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()
        
        # 添加窗口关闭事件处理
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 组件UI控件存储
        self.component_widgets = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 创建滚动容器
        main_canvas = tk.Canvas(self.window, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=main_canvas.yview)
        h_scrollbar = ttk.Scrollbar(self.window, orient=tk.HORIZONTAL, command=main_canvas.xview)
        
        # 创建可滚动框架
        scrollable_frame = ttk.Frame(main_canvas)
        
        # 配置canvas
        main_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 创建窗口并设置合适的宽度
        canvas_frame = main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # 更新函数确保框架宽度正确
        def update_scrollable_frame_width(event=None):
            # 获取canvas当前宽度
            canvas_width = main_canvas.winfo_width()
            if canvas_width > 10:  # 确保有有效宽度
                # 减少右侧边距，使内容更靠近窗口边缘
                main_canvas.itemconfig(canvas_frame, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.bind("<Configure>", update_scrollable_frame_width)
        
        # 布局滚动组件
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始更新一次宽度
        self.window.after(100, update_scrollable_frame_width)
        
        # 添加内部边距，使用更小的边距
        content_frame = ttk.Frame(scrollable_frame, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置文件管理部分
        self._setup_style_management(content_frame)
        
        # 图片比例设置
        self._setup_aspect_ratio(content_frame)
        
        # 字体设置
        self._setup_font_settings(content_frame)
        
        # 文本位置设置
        self._setup_text_position(content_frame)
        
        # 图片组件设置
        self._setup_image_components(content_frame)
        
        # 按钮框架
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="保存", command=self._on_save_apply).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="应用", command=self._on_apply).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="取消", command=self._on_close).pack(
            side=tk.RIGHT, padx=5
        )
    
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
    
    def _setup_aspect_ratio(self, parent):
        """设置图片比例部分"""
        ratio_frame = ttk.LabelFrame(parent, text="图片比例设置", padding="10")
        ratio_frame.pack(fill=tk.X, pady=10)
        
        # 比例选择
        self.aspect_ratio_var = tk.StringVar(value=CONFIGS.style.aspect_ratio)
        
        # 使用Frame将三个选项放在一行
        ratio_options_frame = ttk.Frame(ratio_frame)
        ratio_options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(
            ratio_options_frame,
            text="3:1 (默认)",
            variable=self.aspect_ratio_var,
            value="3:1",
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            ratio_options_frame,
            text="5:4",
            variable=self.aspect_ratio_var,
            value="5:4",
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            ratio_options_frame,
            text="16:9",
            variable=self.aspect_ratio_var,
            value="16:9",
        ).pack(side=tk.LEFT, padx=10)
        
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
        available_fonts = self._get_available_fonts()
        self.font_family_var = tk.StringVar(value=CONFIGS.style.font_family)
        
        font_combo = ttk.Combobox(
            font_row_frame,
            textvariable=self.font_family_var,
            values=available_fonts,
            state="readonly",
            width=15
        )
        font_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(font_row_frame, text="字号:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.font_size_var = tk.StringVar(value=str(CONFIGS.style.font_size))
        font_size_entry = ttk.Entry(
            font_row_frame,
            textvariable=self.font_size_var,
            width=8
        )
        font_size_entry.pack(side=tk.LEFT)
        
        # 文字颜色
        color_frame = ttk.Frame(font_frame)
        color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(color_frame, text="文字颜色:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.text_color_var = tk.StringVar(value=CONFIGS.style.text_color)
        color_entry = ttk.Entry(
            color_frame,
            textvariable=self.text_color_var,
            width=12
        )
        color_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # 颜色预览
        self.text_color_preview = ttk.Label(
            color_frame,
            text="   ",
            background=self.text_color_var.get(),
            relief="solid",
            width=3
        )
        self.text_color_preview.pack(side=tk.LEFT)
        
        # 绑定颜色变化
        self.text_color_var.trace_add("write", self._update_text_color_preview)
        
        # 使用角色颜色作为强调色
        self.use_character_color_var = tk.BooleanVar(value=CONFIGS.style.use_character_color)
        use_char_color_cb = ttk.Checkbutton(
            font_frame,
            text="使用角色颜色作为强调色",
            variable=self.use_character_color_var,
            command=self._on_use_character_color_changed
        )
        use_char_color_cb.pack(anchor=tk.W, pady=5)
        
        # 强调颜色
        bracket_color_frame = ttk.Frame(font_frame)
        bracket_color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(bracket_color_frame, text="强调颜色:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.bracket_color_var = tk.StringVar(value=CONFIGS.style.bracket_color)
        bracket_color_entry = ttk.Entry(
            bracket_color_frame,
            textvariable=self.bracket_color_var,
            width=12
        )
        bracket_color_entry.pack(side=tk.LEFT, padx=(0, 5))
        
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
    
    def _setup_text_position(self, parent):
        """设置文本位置设置"""
        position_frame = ttk.LabelFrame(parent, text="文本位置设置", padding="10")
        position_frame.pack(fill=tk.X, pady=10)
        
        # 使用Frame和pack布局替代grid
        # 偏移设置 - 第一行
        offset_row1 = ttk.Frame(position_frame)
        offset_row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(offset_row1, text="水平偏移(X):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        
        self.text_offset_x_var = tk.StringVar(value=str(CONFIGS.style.text_offset_x))
        offset_x_entry = ttk.Entry(
            offset_row1,
            textvariable=self.text_offset_x_var,
            width=12
        )
        offset_x_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(offset_row1, text="垂直偏移(Y):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        
        self.text_offset_y_var = tk.StringVar(value=str(CONFIGS.style.text_offset_y))
        offset_y_entry = ttk.Entry(
            offset_row1,
            textvariable=self.text_offset_y_var,
            width=12
        )
        offset_y_entry.pack(side=tk.LEFT)
        
        # 对齐设置 - 第二行
        align_row = ttk.Frame(position_frame)
        align_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(align_row, text="水平对齐(X):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        
        self.text_align_var = tk.StringVar(value=CONFIGS.style.text_align)
        # 将英文值转换为中文显示
        align_mapping = {"left": "左", "center": "中", "right": "右"}
        align_display = align_mapping.get(CONFIGS.style.text_align, "左")
        align_combo = ttk.Combobox(
            align_row,
            textvariable=self.text_align_var,
            values=["左", "中", "右"],
            state="readonly",
            width=12
        )
        align_combo.set(align_display)
        align_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(align_row, text="垂直对齐(Y):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        
        self.text_valign_var = tk.StringVar(value=CONFIGS.style.text_valign)
        valign_mapping = {"top": "上", "middle": "中", "bottom": "下"}
        valign_display = valign_mapping.get(CONFIGS.style.text_valign, "上")
        valign_combo = ttk.Combobox(
            align_row,
            textvariable=self.text_valign_var,
            values=["上", "中", "下"],
            state="readonly",
            width=12
        )
        valign_combo.set(valign_display)
        valign_combo.pack(side=tk.LEFT)
        
        # 说明
        ttk.Label(
            position_frame,
            text="注：偏移值相对于文本框区域的默认位置，正值向右/下偏移",
            font=("", 8),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(10, 0))
    
    def _setup_image_components(self, parent):
        """设置图片组件设置"""
        components_frame = ttk.LabelFrame(parent, text="图片组件设置", padding="10")
        components_frame.pack(fill=tk.X, pady=10)
        
        # 组件容器框架
        self.components_container = ttk.Frame(components_frame)
        self.components_container.pack(fill=tk.X, pady=5)
        
        # 添加新组件按钮
        add_button_frame = ttk.Frame(components_frame)
        add_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            add_button_frame,
            text="添加图片组件",
            command=self._add_image_component,
            width=15
        ).pack(side=tk.LEFT)
        
        # 获取shader文件夹中的图片
        self.shader_files = self._get_shader_files()
        
        # 加载现有组件
        self._load_image_components()
    
    def _create_component_ui(self, component, index=None):
        """创建组件UI - 使用pack布局"""
        component_type = component.get("type", "extra")
        
        # 为内置组件设置固定ID
        if component_type == "character":
            component_id = "character"
        elif component_type == "textbox":
            component_id = "textbox"
        elif component_type == "namebox":
            component_id = "namebox"
        else:
            component_id = component.get("id", f"extra_{len(self.component_widgets)}")
        
        # 获取图层值
        layer_value = component.get("layer", 0)
        
        # 创建组件框架
        comp_frame = ttk.Frame(self.components_container, relief="solid", padding=8)
        comp_frame.pack(fill=tk.X, pady=3, padx=2)
        
        # 在框架右上角显示图层顺序
        layer_label = ttk.Label(
            comp_frame, 
            text=f"图层 {layer_value}", 
            font=("", 9, "bold"),
            foreground="blue"
        )
        layer_label.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
        
        row = 0
        
        # 第一行：类型、启用/禁用、缩放、图层控制
        row_frame1 = ttk.Frame(comp_frame)
        row_frame1.pack(fill=tk.X, pady=(0, 5))
        
        type_display = COMPONENT_LAYER_TYPES.get(component_type, component_type)
        ttk.Label(row_frame1, text=f"{type_display}", width=7).pack(side=tk.LEFT, padx=(0, 10))
        
        # 启用/禁用复选框
        enabled_var = tk.BooleanVar(value=component.get("enabled", True))
        enabled_cb = ttk.Checkbutton(
            row_frame1,
            text="启用",
            variable=enabled_var,
            command=lambda: self._on_component_changed(component_id)
        )
        enabled_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # 缩放控件（放在启用按钮右边）
        ttk.Label(row_frame1, text="缩放:", width=6).pack(side=tk.LEFT, padx=(0, 2))
        
        scale_var = tk.StringVar(value=str(component.get("scale", 1.0)))
        scale_entry = ttk.Entry(
            row_frame1,
            textvariable=scale_var,
            width=8
        )
        scale_entry.pack(side=tk.LEFT, padx=(0, 10))
        scale_entry.bind("<KeyRelease>", lambda e: self._on_component_changed(component_id))
        
        # 图层控制按钮（靠右对齐）
        controls_frame = ttk.Frame(row_frame1)
        controls_frame.pack(side=tk.RIGHT)
        
        # 上移按钮
        move_up_btn = ttk.Button(
            controls_frame,
            text="↑",
            width=3,
            command=lambda: self._move_component_up(component_id)
        )
        move_up_btn.pack(side=tk.LEFT, padx=(0, 2))
        
        # 下移按钮
        move_down_btn = ttk.Button(
            controls_frame,
            text="↓",
            width=3,
            command=lambda: self._move_component_down(component_id)
        )
        move_down_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 删除按钮（如果是额外组件）
        if component_type == "extra":
            delete_btn = ttk.Button(
                controls_frame,
                text="删除",
                width=6,
                command=lambda: self._remove_component(component_id)
            )
            delete_btn.pack(side=tk.LEFT)
        
        # 第二行：图片选择（如果适用）
        overlay_var = None
        align_var = None
        
        if component_type in ["textbox", "namebox", "extra"]:
            row_frame2 = ttk.Frame(comp_frame)
            row_frame2.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Label(row_frame2, text="图片:", width=7).pack(side=tk.LEFT, padx=(0, 5))
            
            overlay_var = tk.StringVar(value=component.get("overlay", ""))
            overlay_combo = ttk.Combobox(
                row_frame2,
                textvariable=overlay_var,
                values=[""] + self.shader_files,
                state="readonly",
                width=20
            )
            overlay_combo.pack(side=tk.LEFT, padx=(0, 20))
            overlay_combo.bind("<<ComboboxSelected>>", lambda e: self._on_component_changed(component_id))
            
            # 对齐方式（如果是额外组件或名称框）
            if component_type in ["namebox", "extra"]:
                ttk.Label(row_frame2, text="对齐:", width=5).pack(side=tk.LEFT, padx=(0, 5))
                
                # 使用中文对齐选项
                align_options = list(ALIGN_MAPPING.values())
                current_align = component.get("align", "top-left")
                align_display = ALIGN_MAPPING.get(current_align, "左上")
                
                align_var = tk.StringVar(value=align_display)
                align_combo = ttk.Combobox(
                    row_frame2,
                    textvariable=align_var,
                    values=align_options,
                    state="readonly",
                    width=12
                )
                align_combo.pack(side=tk.LEFT)
                align_combo.bind("<<ComboboxSelected>>", lambda e: self._on_component_changed(component_id))
        
        # 第三行：偏移设置（X和Y偏移）
        row_frame3 = ttk.Frame(comp_frame)
        row_frame3.pack(fill=tk.X)
        
        ttk.Label(row_frame3, text="X偏移:", width=7).pack(side=tk.LEFT, padx=(0, 5))
        
        offset_x_var = tk.StringVar(value=str(component.get("offset_x", 0)))
        offset_x_entry = ttk.Entry(
            row_frame3,
            textvariable=offset_x_var,
            width=6
        )
        offset_x_entry.pack(side=tk.LEFT, padx=(0, 15))
        offset_x_entry.bind("<KeyRelease>", lambda e: self._on_component_changed(component_id))
        
        ttk.Label(row_frame3, text="Y偏移:", width=7).pack(side=tk.LEFT, padx=(0, 5))
        
        offset_y_var = tk.StringVar(value=str(component.get("offset_y", 0)))
        offset_y_entry = ttk.Entry(
            row_frame3,
            textvariable=offset_y_var,
            width=6
        )
        offset_y_entry.pack(side=tk.LEFT)
        offset_y_entry.bind("<KeyRelease>", lambda e: self._on_component_changed(component_id))
        
        # 存储UI控件
        self.component_widgets[component_id] = {
            "frame": comp_frame,
            "type": component_type,
            "layer_label": layer_label,  # 右上角的图层标签
            "widgets": {
                "enabled_var": enabled_var,
                "layer_var": tk.IntVar(value=layer_value),  # 保留layer_var用于内部跟踪
                "overlay_var": overlay_var,
                "align_var": align_var,
                "offset_x_var": offset_x_var,
                "offset_y_var": offset_y_var,
                "scale_var": scale_var
            }
        }
        
        return component_id
    
    def _add_image_component(self):
        """添加新的图片组件"""
        # 获取所有组件的图层值
        layers = []
        for component in CONFIGS.style.image_components:
            layers.append(component.get("layer", 0))
        
        # 找到可用的最小图层序号
        new_layer = 0
        while new_layer in layers:
            new_layer += 1
        
        # 创建默认的额外组件配置
        component_config = {
            "type": "extra",
            "enabled": True,
            "overlay": "",
            "align": "top-left",
            "offset_x": 0,
            "offset_y": 0,
            "scale": 1.0,
            "layer": new_layer,
            "id": f"extra_{len([c for c in CONFIGS.style.image_components if c.get('type') == 'extra']) + 1}"
        }
        
        # 添加到配置
        CONFIGS.add_extra_component(component_config)
        
        # 重新加载所有组件以确保正确显示
        self._load_image_components()
    
    def _reorder_components(self):
        """重新排序所有组件，确保图层序号唯一且连续"""
        # 获取所有组件
        components = []
        
        # 收集内置组件
        for component_type in ["character", "textbox", "namebox"]:
            component = CONFIGS.get_component_by_type(component_type)
            if component:
                components.append(component)
        
        # 收集额外组件
        components.extend(CONFIGS.get_extra_components())
        
        # 按当前图层排序
        components.sort(key=lambda x: x.get("layer", 0))
        
        # 重新分配图层序号
        for i, component in enumerate(components):
            old_layer = component.get("layer", 0)
            component["layer"] = i
            
            # 更新UI中的显示
            component_id = None
            if component.get("type") == "character":
                component_id = "character"
            elif component.get("type") == "textbox":
                component_id = "textbox"
            elif component.get("type") == "namebox":
                component_id = "namebox"
            else:
                component_id = component.get("id")
            
            if component_id in self.component_widgets:
                self.component_widgets[component_id]["widgets"]["layer_var"].set(i)
        
        # 更新图层显示并重新排序UI
        self._update_layer_display()
        self._reorder_component_uis()

    def _remove_component(self, component_id):
        """删除组件"""
        # 从配置中移除
        CONFIGS.remove_extra_component(component_id)
        
        # 重新加载所有组件以确保UI正确显示
        self._load_image_components()
    
    def _move_component_up(self, component_id):
        """上移组件（增加图层值）并调整UI位置"""
        if component_id not in self.component_widgets:
            return
        
        # 获取当前组件图层值
        current_layer = self.component_widgets[component_id]["widgets"]["layer_var"].get()
        all_layers = [ui["widgets"]["layer_var"].get() for ui in self.component_widgets.values()]
        max_layer = max(all_layers)
        
        # 如果已经是最高层，不执行操作
        if current_layer >= max_layer:
            return
        
        # 找到当前组件之上的组件（图层值比当前大的组件）
        higher_layers = [layer for layer in all_layers if layer > current_layer]
        if not higher_layers:
            return
        
        next_layer = min(higher_layers)
        
        # 找到具有next_layer的组件
        for other_id, other_ui in self.component_widgets.items():
            if other_id != component_id and other_ui["widgets"]["layer_var"].get() == next_layer:
                # 交换图层值
                other_ui["widgets"]["layer_var"].set(current_layer)
                self.component_widgets[component_id]["widgets"]["layer_var"].set(next_layer)
                
                # 更新配置中的组件图层
                self._update_component_config_layers()
                
                # 重新加载UI以正确显示
                self._load_image_components()
                
                # 更新组件状态
                self._on_component_changed(component_id)
                self._on_component_changed(other_id)
                return
        
        # 如果没有找到交换的组件，直接增加图层值
        self.component_widgets[component_id]["widgets"]["layer_var"].set(next_layer)
        
        # 更新配置中的组件图层
        self._update_component_config_layers()
        
        # 重新加载UI以正确显示
        self._load_image_components()
        
        # 更新组件状态
        self._on_component_changed(component_id)
    
    def _move_component_down(self, component_id):
        """下移组件（减少图层值）并调整UI位置"""
        if component_id not in self.component_widgets:
            return
        
        # 获取当前组件图层值
        current_layer = self.component_widgets[component_id]["widgets"]["layer_var"].get()
        all_layers = [ui["widgets"]["layer_var"].get() for ui in self.component_widgets.values()]
        min_layer = min(all_layers)
        
        # 如果已经是最底层，不执行操作
        if current_layer <= min_layer:
            return
        
        # 找到当前组件之下的组件（图层值比当前小的组件）
        lower_layers = [layer for layer in all_layers if layer < current_layer]
        if not lower_layers:
            return
        
        prev_layer = max(lower_layers)
        
        # 找到具有prev_layer的组件
        for other_id, other_ui in self.component_widgets.items():
            if other_id != component_id and other_ui["widgets"]["layer_var"].get() == prev_layer:
                # 交换图层值
                other_ui["widgets"]["layer_var"].set(current_layer)
                self.component_widgets[component_id]["widgets"]["layer_var"].set(prev_layer)
                
                # 更新配置中的组件图层
                self._update_component_config_layers()
                
                # 重新加载UI以正确显示
                self._load_image_components()
                
                # 更新组件状态
                self._on_component_changed(component_id)
                self._on_component_changed(other_id)
                return
        
        # 如果没有找到交换的组件，直接减少图层值
        self.component_widgets[component_id]["widgets"]["layer_var"].set(prev_layer)
        
        # 更新配置中的组件图层
        self._update_component_config_layers()
        
        # 重新加载UI以正确显示
        self._load_image_components()
        
        # 更新组件状态
        self._on_component_changed(component_id)
        
    def _update_component_config_layers(self):
        """更新配置中所有组件的图层值"""
        # 收集所有组件的新图层值
        component_layers = {}
        for component_id, component_ui in self.component_widgets.items():
            component_layers[component_id] = component_ui["widgets"]["layer_var"].get()
        
        # 按图层值排序组件ID
        sorted_ids = sorted(component_layers.items(), key=lambda x: x[1])
        
        # 更新配置中的组件图层
        for component_id, layer in sorted_ids:
            # 查找对应的组件
            for component in CONFIGS.style.image_components:
                # 确定组件ID
                component_type = component.get("type")
                comp_id = None
                
                if component_type == "character":
                    comp_id = "character"
                elif component_type == "textbox":
                    comp_id = "textbox"
                elif component_type == "namebox":
                    comp_id = "namebox"
                else:
                    comp_id = component.get("id")
                
                if comp_id == component_id:
                    component["layer"] = layer
                    break

    def _reorder_component_uis(self):
        """根据图层值重新排序组件UI（图层值大的在上）"""
        # 获取所有组件按图层排序
        components_by_layer = []
        for component_id, component_ui in self.component_widgets.items():
            layer = component_ui["widgets"]["layer_var"].get()
            components_by_layer.append((layer, component_id, component_ui["frame"]))
        
        # 按图层降序排序（图层值大的在上，图层值小的在下）
        components_by_layer.sort(key=lambda x: x[0], reverse=True)
        
        # 从容器中移除所有组件
        for frame in self.components_container.winfo_children():
            frame.pack_forget()
        
        # 按新的图层顺序重新pack（图层值大的在上）
        for layer, component_id, frame in components_by_layer:
            frame.pack(fill=tk.X, pady=3, padx=2)

    def _update_layer_display(self):
        """更新所有组件的图层显示"""
        for component_id, component_ui in self.component_widgets.items():
            layer = component_ui["widgets"]["layer_var"].get()
            component_ui["layer_label"].config(text=f"图层 {layer}")

    def _on_component_changed(self, component_id):
        """组件设置改变"""
        # 标记设置已改变
        pass
    
    def _load_image_components(self):
        """加载图片组件 - 重新创建所有UI"""
        # 清空现有组件UI
        for widget in self.components_container.winfo_children():
            widget.destroy()
        self.component_widgets.clear()
        
        # 按图层值降序加载组件（图层值大的先加载，显示在上方）
        sorted_components = sorted(CONFIGS.style.image_components, 
                                  key=lambda x: x.get("layer", 0), reverse=True)
        
        # 加载所有组件
        for component in sorted_components:
            self._create_component_ui(component)
    
    def _get_available_fonts(self):
        """获取可用字体列表"""
        font_files = get_available_fonts()
        project_fonts = []

        for font_path in font_files:
            if font_path:
                font_name = os.path.splitext(os.path.basename(font_path))[0]
                project_fonts.append(font_name)
        return project_fonts
    
    def _get_shader_files(self):
        """获取shader文件夹中的图片文件列表"""
        shader_dir = get_resource_path(os.path.join("assets", "shader"))
        shader_files = []
        
        if os.path.exists(shader_dir):
            for file in os.listdir(shader_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                    shader_files.append(file)
        
        return sorted(shader_files)
    
    def _on_style_selected(self, event=None):
        """样式选择改变事件 - 修复：完全重新构建UI"""
        style_name = self.style_var.get()
        
        # 加载新样式配置
        CONFIGS.apply_style(style_name)
        
        # 完全重新构建UI显示
        self._rebuild_ui_from_style()
        
        # 通知主界面刷新预览
        if self.gui:
            self.gui.update_preview()
    
    def _rebuild_ui_from_style(self):
        """完全重新构建UI从当前样式"""
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
        
        # 文本位置
        self.text_offset_x_var.set(str(CONFIGS.style.text_offset_x))
        self.text_offset_y_var.set(str(CONFIGS.style.text_offset_y))
        
        # 将对齐方式从英文转换为中文显示
        align_mapping = {"left": "左", "center": "中", "right": "右"}
        valign_mapping = {"top": "上", "middle": "中", "bottom": "下"}
        
        align_display = align_mapping.get(CONFIGS.style.text_align, "左")
        valign_display = valign_mapping.get(CONFIGS.style.text_valign, "上")
        
        # 直接设置Combobox的值
        if hasattr(self, 'text_align_var'):
            self.text_align_var.set(align_display)
        
        if hasattr(self, 'text_valign_var'):
            self.text_valign_var.set(valign_display)
        
        # 完全重新加载图片组件
        self._load_image_components()
            
    def _update_ui_from_style(self):
        """从当前样式更新UI显示"""
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
        
        # 文本位置
        self.text_offset_x_var.set(str(CONFIGS.style.text_offset_x))
        self.text_offset_y_var.set(str(CONFIGS.style.text_offset_y))
        
        # 将对齐方式从英文转换为中文显示
        align_mapping = {"left": "左", "center": "中", "right": "右"}
        valign_mapping = {"top": "上", "middle": "中", "bottom": "下"}
        
        align_display = align_mapping.get(CONFIGS.style.text_align, "左")
        valign_display = valign_mapping.get(CONFIGS.style.text_valign, "上")
        
        # 直接设置Combobox的值
        if hasattr(self, 'text_align_var'):
            self.text_align_var.set(align_display)
        
        if hasattr(self, 'text_valign_var'):
            self.text_valign_var.set(valign_display)
    
    def _on_use_character_color_changed(self):
        """使用角色颜色作为强调色选项改变"""
        self._update_bracket_color_entry_state()
        
        # 如果启用使用角色颜色，更新强调色
        if self.use_character_color_var.get():
            self._update_bracket_color_from_character()
    
    def _update_bracket_color_from_character(self):
        """从当前角色颜色更新强调色"""
        character_name = CONFIGS.get_character()
        if character_name in CONFIGS.text_configs_dict and CONFIGS.text_configs_dict[character_name]:
            first_config = CONFIGS.text_configs_dict[character_name][0]
            font_color = first_config.get("font_color", (255, 255, 255))
            hex_color = f"#{font_color[0]:02x}{font_color[1]:02x}{font_color[2]:02x}"
            self.bracket_color_var.set(hex_color)
    
    def _update_bracket_color_entry_state(self):
        """更新强调颜色输入框状态"""
        if not hasattr(self, 'bracket_color_preview'):
            return
            
        if self.use_character_color_var.get():
            # 禁用强调颜色输入框
            for widget in self.bracket_color_preview.master.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.config(state="disabled")
            if hasattr(self, 'bracket_color_preview'):
                self.bracket_color_preview.config(state="disabled")
        else:
            # 启用强调颜色输入框
            for widget in self.bracket_color_preview.master.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.config(state="normal")
            if hasattr(self, 'bracket_color_preview'):
                self.bracket_color_preview.config(state="normal")
    
    def _update_text_color_preview(self, *args):
        """更新文字颜色预览"""
        if not hasattr(self, 'text_color_preview'):
            return
            
        color_value = self.text_color_var.get()
        if self._validate_color_format(color_value):
            self.text_color_preview.configure(background=color_value)
    
    def _update_bracket_color_preview(self, *args):
        """更新强调颜色预览"""
        if not hasattr(self, 'bracket_color_preview'):
            return
            
        color_value = self.bracket_color_var.get()
        if self._validate_color_format(color_value):
            self.bracket_color_preview.configure(background=color_value)
    
    def _validate_color_format(self, color_value):
        """验证颜色格式"""
        pattern = r'^#([A-Fa-f0-9]{6})$'
        return re.match(pattern, color_value) is not None
    
    def _collect_style_data(self):
        """收集所有样式设置数据"""
        # 收集组件数据
        image_components = []
        
        # 首先收集内置组件（character, textbox, namebox）
        for component_type in ["character", "textbox", "namebox"]:
            component = CONFIGS.get_component_by_type(component_type)
            if component:
                # 查找对应的UI控件
                component_id = component_type  # 使用组件类型作为ID
                if component_id in self.component_widgets:
                    widgets = self.component_widgets[component_id]["widgets"]
                    updated_component = component.copy()
                    
                    # 只更新基本的配置字段
                    updated_component.update({
                        "enabled": widgets["enabled_var"].get(),
                        "layer": int(widgets["layer_var"].get() or component.get("layer", 0)),
                        "offset_x": int(widgets["offset_x_var"].get() or component.get("offset_x", 0)),
                        "offset_y": int(widgets["offset_y_var"].get() or component.get("offset_y", 0)),
                        "scale": float(widgets["scale_var"].get() or component.get("scale", 1.0))
                    })
                    
                    # 对于textbox和namebox，更新overlay
                    if component_type in ["textbox", "namebox"] and widgets["overlay_var"]:
                        updated_component["overlay"] = widgets["overlay_var"].get()
                    
                    # 对于namebox，更新align（需要将中文转换回英文）
                    if component_type == "namebox" and widgets["align_var"]:
                        align_display = widgets["align_var"].get()
                        align_value = REVERSE_ALIGN_MAPPING.get(align_display, "top-left")
                        updated_component["align"] = align_value
                    
                    image_components.append(updated_component)
                else:
                    # 如果没有UI控件，使用原始配置
                    image_components.append(component.copy())
        
        # 收集额外组件
        for component_id, component_ui in self.component_widgets.items():
            if component_ui["type"] == "extra":
                widgets = component_ui["widgets"]
                
                # 将对齐方式从中文转换回英文
                align_display = widgets["align_var"].get() if widgets["align_var"] else "左上"
                align_value = REVERSE_ALIGN_MAPPING.get(align_display, "top-left")
                
                image_components.append({
                    "type": "extra",
                    "id": component_id,
                    "enabled": widgets["enabled_var"].get(),
                    "overlay": widgets["overlay_var"].get() if widgets["overlay_var"] else "",
                    "align": align_value,
                    "offset_x": int(widgets["offset_x_var"].get() or 0),
                    "offset_y": int(widgets["offset_y_var"].get() or 0),
                    "scale": float(widgets["scale_var"].get() or 1.0),
                    "layer": int(widgets["layer_var"].get() or 0)
                })
        
        # 按图层排序（图层值小的在下，图层值大的在上）
        image_components.sort(key=lambda x: x.get("layer", 0))
        
        # 将对齐方式从中文转换回英文
        text_align_display = self.text_align_var.get() if hasattr(self, 'text_align_var') else "左"
        text_valign_display = self.text_valign_var.get() if hasattr(self, 'text_valign_var') else "上"
        
        text_align_mapping = {"左": "left", "中": "center", "右": "right"}
        text_valign_mapping = {"上": "top", "中": "middle", "下": "bottom"}
        
        # 收集其他样式设置
        style_data = {
            "aspect_ratio": self.aspect_ratio_var.get() if hasattr(self, 'aspect_ratio_var') else "3:1",
            "font_family": self.font_family_var.get() if hasattr(self, 'font_family_var') else "font3",
            "font_size": int(self.font_size_var.get() or 90) if hasattr(self, 'font_size_var') else 90,
            "text_color": self.text_color_var.get() if hasattr(self, 'text_color_var') else "#FFFFFF",
            "bracket_color": self.bracket_color_var.get() if hasattr(self, 'bracket_color_var') else "#EF4F54",
            "use_character_color": self.use_character_color_var.get() if hasattr(self, 'use_character_color_var') else False,
            "text_offset_x": int(self.text_offset_x_var.get() or 0) if hasattr(self, 'text_offset_x_var') else 0,
            "text_offset_y": int(self.text_offset_y_var.get() or 0) if hasattr(self, 'text_offset_y_var') else 0,
            "text_align": text_align_mapping.get(text_align_display, "left"),
            "text_valign": text_valign_mapping.get(text_valign_display, "top"),
            "image_components": image_components
        }
        
        return style_data
    
    def _override_button_commands(self, close_callback):
        """覆盖按钮的命令，确保它们正确调用关闭回调"""
        # 查找所有按钮并修改其命令
        for widget in self.window.winfo_children():
            if isinstance(widget, ttk.Button):
                current_cmd = widget.cget("command")
                if current_cmd:
                    # 创建一个包装函数，先执行原命令，然后调用关闭回调
                    def wrapped_cmd(original_cmd=current_cmd, close_cb=close_callback):
                        try:
                            original_cmd()
                        finally:
                            close_cb()
                    widget.config(command=wrapped_cmd)
            
            # 递归查找子部件
            for child in widget.winfo_children():
                if isinstance(child, ttk.Button):
                    current_cmd = child.cget("command")
                    if current_cmd:
                        def wrapped_cmd(original_cmd=current_cmd, close_cb=close_callback):
                            try:
                                original_cmd()
                            finally:
                                close_cb()
                        child.config(command=wrapped_cmd)
    
    def _on_apply(self):
        """应用样式设置"""
        style_name = self.style_var.get()
        style_data = self._collect_style_data()
        
        # 验证颜色格式
        if not self._validate_color_format(style_data["text_color"]):
            messagebox.showerror("错误", "文字颜色格式无效，请输入有效的十六进制颜色值（例如：#FFFFFF）")
            return False
        
        if not self._validate_color_format(style_data["bracket_color"]):
            messagebox.showerror("错误", "强调颜色格式无效，请输入有效的十六进制颜色值（例如：#FFFFFF）")
            return False
        
        # 验证数值输入
        try:
            # 验证字体大小
            if not 8 <= style_data["font_size"] <= 250:
                messagebox.showerror("错误", "字体大小必须在8到250之间")
                return False
            
            # 验证偏移值在合理范围内
            if abs(style_data["text_offset_x"]) > 500:
                messagebox.showerror("错误", "水平偏移值过大，应在-500到500之间")
                return False
                
            if abs(style_data["text_offset_y"]) > 500:
                messagebox.showerror("错误", "垂直偏移值过大，应在-500到500之间")
                return False
                                
        except ValueError as e:
            messagebox.showerror("错误", f"数值格式错误: {str(e)}")
            return False
        
        # 更新样式配置
        success = CONFIGS.update_style(style_name, style_data)
        
        if success:
            # 立即应用样式到当前配置
            CONFIGS.apply_style(style_name)
            # 刷新GUI预览
            if self.gui:
                self.gui.update_preview()
                # 更新状态显示
                self.gui.update_status(f"样式已应用: {self.style_var.get()}")
            return True
        else:
            messagebox.showerror("错误", "应用样式失败")
            return False
    
    def _on_save_apply(self):
        """保存并应用样式设置"""
        self._on_apply()
        self.window.destroy()

    def _on_close(self):
        """处理窗口关闭事件"""
        self.window.destroy()