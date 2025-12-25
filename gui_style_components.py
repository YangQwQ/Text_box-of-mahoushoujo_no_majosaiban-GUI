"""组件编辑器模块"""

import tkinter as tk
from tkinter import ttk
import copy
import os
from path_utils import get_resource_path, get_available_fonts

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

# 组件类型映射
COMPONENT_TYPES = {
    "character": "角色",
    "textbox": "文本框",
    "namebox": "名称框",
    "text": "文本组件",
    "extra": "图片组件",
    "background": "背景组件"
}

DEFAULT_VALUES = {
    "overlay": "",
    "name": "",
    "align": "top-left",
    "offset_x": 0,
    "offset_y": 0,
    "scale": 1.0,
    "fill_mode": "fit"
}

COMPONENT_DEFAULTS = {
    "background": {
        "enabled": True,
        # "overlay": "",
        "align": "top-left",
        "offset_x": 0,
        "offset_y": 0,
        "scale": 1.0,
        "layer": 0,
        "fill_mode": "fit",
        "name": "背景",
        "use_fixed_background": False
    },"character": {
        "enabled": True,
        "align": "bottom-left",
        "offset_x": 0,
        "offset_y": 0,
        "scale": 1.6,
        "layer": 2,
        # "character_name": "",
        # "emotion_index": 1,
        "name": "角色",
        "use_fixed_character": False
    },
    "textbox": {
        "enabled": True,
        "overlay": "文本框1.webp",
        "align": "bottom-center",
        "offset_x": 0,
        "offset_y": 0,
        "scale": 1.0,
        "layer": 1,
        "name": "文本框"
    },
    "namebox": {
        "enabled": True,
        "overlay": "名字框.webp",
        "align": "bottom-left",
        "offset_x": 450,
        "offset_y": -400,
        "scale": 1.2,
        "layer": 3,
        "name": "名称框"
    },
    "extra": {
        "enabled": True,
        "overlay": "",
        "align": "top-left",
        "offset_x": 0,
        "offset_y": 0,
        "scale": 1.0,
        "layer": 4,
        "fill_mode": "fit",
        "name": "图片组件"
    },
    "text": {
        "enabled": True,
        "text": "示例文本",
        "font_family": "font3",
        "font_size": 90,
        "text_color": "#FFFFFF",
        "shadow_color": "#000000",
        "shadow_offset_x": 4,
        "shadow_offset_y": 4,
        "max_width": 500,
        "align": "top-left",
        "offset_x": 0,
        "offset_y": 0,
        "layer": 5,
        "name": "文本组件"
    }
}

# 组件属性配置（定义每种组件类型支持的属性）
COMPONENT_PROPERTIES = {
    "background": {
        "required": ["type", "enabled", "overlay", "align"],
        "optional": ["offset_x", "offset_y", "scale", "layer", "fill_mode", "name"],
        "defaults": {
            "type": "background",
            **COMPONENT_DEFAULTS["background"]
        }
    },"character": {
        "required": ["type", "enabled", "align"],
        "optional": ["offset_x", "offset_y", "scale", "layer", "name",
                    "character_name", "emotion_index", "use_fixed_character"],
        "defaults": {
            "type": "character",
            **COMPONENT_DEFAULTS["character"]
        }
    },
    "textbox": {
        "required": ["type", "enabled", "overlay", "align"],
        "optional": ["offset_x", "offset_y", "scale", "layer", "name"],
        "defaults": {
            "type": "textbox",
            **COMPONENT_DEFAULTS["textbox"]
        }
    },
    "namebox": {
        "required": ["type", "enabled", "overlay", "align"],
        "optional": ["offset_x", "offset_y", "scale", "layer", "name"],
        "defaults": {
            "type": "namebox",
            **COMPONENT_DEFAULTS["namebox"]
        }
    },
    "extra": {
        "required": ["type", "enabled", "overlay", "align"],
        "optional": ["offset_x", "offset_y", "scale", "layer", "fill_mode", "name"],
        "defaults": {
            "type": "extra",
            **COMPONENT_DEFAULTS["extra"]
        }
    },
    "text": {
        "required": ["type", "enabled", "text", "align"],
        "optional": ["offset_x", "offset_y", "layer", "font_family", "font_size", 
                     "text_color", "shadow_color", "shadow_offset_x", "shadow_offset_y", 
                     "max_width", "name"],
        "defaults": {
            "type": "text",
            **COMPONENT_DEFAULTS["text"]
        }
    }
}

class ComponentEditor:
    """组件编辑器"""
    
    def __init__(self, parent, style_window, component_config):
        self.parent = parent
        self.style_window = style_window
        # 深拷贝组件配置
        self.component_config = copy.deepcopy(component_config)
        
        # 移除id属性，如果有的话
        if 'id' in self.component_config:
            del self.component_config['id']
        
        # 如果没有layer属性，添加默认值
        if 'layer' not in self.component_config:
            self.component_config['layer'] = 0
        
        # 存储图层值作为标识符
        self.layer = self.component_config.get('layer', 0)
        
        # 存储UI变量
        self.ui_widgets = {}
        
        # 编辑状态
        self.is_expanded = False
        
        # 获取shader文件夹中的图片
        self.shader_files = self._get_shader_files()
        # 获取background文件夹中的图片
        self.background_files = self._get_background_files()
        
        # 获取可用字体
        self.available_fonts = get_available_fonts()
        
        # 创建主框架
        self.main_frame = ttk.Frame(parent, relief="solid", padding=8)
        
        # 创建UI组件
        self._create_ui()
    
    def _create_ui(self):
        """创建UI组件"""
        # 清空框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # 创建顶部框架（始终显示）
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, expand=True)
        
        # 创建属性框架（初始隐藏）
        self.props_frame = ttk.Frame(self.main_frame)
        # 初始状态为隐藏
        
        # 填充顶部框架
        self._fill_top_frame()
        
        # 填充属性框架
        self._fill_props_frame()
    
    def _fill_top_frame(self):
        """填充顶部框架 - 修改为显示组件类型和名称"""
        # 清空顶部框架
        for widget in self.top_frame.winfo_children():
            widget.destroy()
        
        current_config = self.component_config
        component_type = current_config.get("type", "extra")
        type_display = COMPONENT_TYPES.get(component_type, component_type)
        
        # 获取组件名称，优先使用当前配置中的名称
        component_name = current_config.get("name", "")
        if not component_name:
            # 如果配置中没有名称，则根据组件类型生成默认名称
            component_name = self._get_default_component_name(current_config)
        
        # 显示格式：类型 - 名称
        display_text = f"{type_display} - {component_name}"
        
        # 创建一行布局
        row_frame = ttk.Frame(self.top_frame)
        row_frame.pack(fill=tk.X, expand=True)
        
        # 显示组件类型和名称（移除图层号显示）
        name_label = ttk.Label(row_frame, text=display_text, width=35, anchor=tk.W)
        name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 启用复选框
        enabled_var = tk.BooleanVar(value=current_config.get("enabled", True))
        enabled_cb = ttk.Checkbutton(
            row_frame,
            variable=enabled_var,
            command=lambda: self._on_enabled_changed(enabled_var)
        )
        enabled_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # 编辑按钮
        edit_btn = ttk.Button(
            row_frame,
            text="编辑" if not self.is_expanded else "收起",
            width=6,
            command=self.toggle_expand
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 上移按钮
        move_up_btn = ttk.Button(
            row_frame,
            text="↑",
            width=3,
            command=lambda: self._move_component("up")
        )
        move_up_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 下移按钮
        move_down_btn = ttk.Button(
            row_frame,
            text="↓",
            width=3,
            command=lambda: self._move_component("down")
        )
        move_down_btn.pack(side=tk.LEFT)
        
        # 存储UI变量
        self.ui_widgets["enabled_var"] = enabled_var
        self.ui_widgets["edit_btn"] = edit_btn
        
    def _get_default_component_name(self, config):
        """根据配置获取默认组件名称"""
        component_type = config.get("type", "extra")
        
        if component_type == "character":
            return "角色"
        elif component_type == "textbox":
            return "文本框"
        elif component_type == "namebox":
            return "名称框"
        elif component_type == "text":
            # 文本组件显示文本内容前10个字符
            text_content = config.get("text", "")
            return f"文本: {text_content[:10]}{'...' if len(text_content) > 10 else ''}"
        else:
            # 检查是否有overlay文件
            overlay = config.get("overlay", "")
            if overlay:
                # 显示文件名（不含扩展名）
                return os.path.splitext(overlay)[0]
            else:
                return "未命名"
            
    def _fill_props_frame(self):
        """填充属性框架"""
        # 清空属性框架
        for widget in self.props_frame.winfo_children():
            widget.destroy()
        
        current_config = self.component_config
        component_type = current_config.get("type", "extra")
        
        # 创建属性编辑器框架
        prop_frame = ttk.Frame(self.props_frame)
        prop_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 第一行：组件类型选择
        type_frame = ttk.Frame(prop_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(type_frame, text="组件类型:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 获取所有可用的组件类型
        available_types = list(COMPONENT_TYPES.keys())
        
        # 创建类型变量
        type_var = tk.StringVar(value=component_type)
        
        # 创建类型下拉框
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=type_var,
            values=[COMPONENT_TYPES[t] for t in available_types],
            state="readonly",
            width=12
        )
        type_combo.set(COMPONENT_TYPES.get(component_type, "图片组件"))
        type_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        # 绑定类型改变事件
        type_combo.bind("<<ComboboxSelected>>", 
                       lambda e: self._on_type_changed(type_var.get()))
        
        # 组件名称
        ttk.Label(type_frame, text="组件名称:").pack(side=tk.LEFT, padx=(0, 5))
        
        name_var = tk.StringVar(value=current_config.get("name", ""))
        name_entry = ttk.Entry(type_frame, textvariable=name_var, width=20)
        name_entry.pack(side=tk.LEFT)
        
        # 存储变量
        self.ui_widgets["type_var"] = type_var
        self.ui_widgets["name_var"] = name_var
        
        # 根据组件类型创建对应的属性编辑器
        if component_type == "text":
            self._create_text_properties(prop_frame, current_config)
        else:
            self._create_image_properties(prop_frame, current_config, component_type)
        
        # 按钮行
        button_frame = ttk.Frame(self.props_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 删除按钮
        delete_btn = ttk.Button(
            button_frame,
            text="删除组件",
            command=self._delete_component
        )
        delete_btn.pack(side=tk.RIGHT, padx=(0, 10))
    
    def _create_image_properties(self, parent_frame, current_config, component_type):
        """创建图片相关组件的属性编辑器"""
        
        # 如果是背景或角色组件，添加角色选择和固定角色选项
        if component_type in ["character", "background"]:
            # 获取所有角色列表 - 仅保留在character组件中
            if component_type == "character":
                from config import CONFIGS
                character_options = []
                for char_id in CONFIGS.character_list:
                    full_name = CONFIGS.mahoshojo[char_id].get("full_name", char_id)
                    character_options.append(f"{full_name} ({char_id})")
                
                # 角色选择行
                char_frame = ttk.Frame(parent_frame)
                char_frame.pack(fill=tk.X, pady=(0, 5))
                
                # 使用固定角色复选框 - 仅角色组件有
                use_fixed_var = tk.BooleanVar(value=current_config.get("use_fixed_character", False))
                use_fixed_cb = ttk.Checkbutton(
                    char_frame,
                    text="使用固定角色",
                    variable=use_fixed_var,
                    command=lambda: self._update_character_selection_state(use_fixed_var, 
                                                                            char_combo, 
                                                                            emotion_combo)
                )
                use_fixed_cb.pack(side=tk.LEFT, padx=(0, 10))
                
                # 存储变量
                self.ui_widgets["use_fixed_character_var"] = use_fixed_var
                
                # 角色选择
                ttk.Label(char_frame, text="角色:").pack(side=tk.LEFT, padx=(0, 5))
                
                # 获取当前配置的角色
                current_char = current_config.get("character_name", "")
                current_display = ""
                for option in character_options:
                    if current_char in option:
                        current_display = option
                        break
                
                char_var = tk.StringVar(value=current_display)
                char_combo = ttk.Combobox(
                    char_frame,
                    textvariable=char_var,
                    values=character_options,
                    state="readonly",
                    width=25
                )
                char_combo.pack(side=tk.LEFT, padx=(0, 10))
                
                # 表情选择
                ttk.Label(char_frame, text="表情:").pack(side=tk.LEFT, padx=(0, 5))
                
                # 获取当前角色的表情数量
                emotion_index = current_config.get("emotion_index", 1)
                char_id = ""
                for char_option in character_options:
                    if current_display == char_option:
                        char_id = char_option.split("(")[-1].rstrip(")")
                        break
                
                emotion_options = []
                if char_id and char_id in CONFIGS.mahoshojo:
                    emotion_count = CONFIGS.mahoshojo[char_id].get("emotion_count", 1)
                    emotion_options = [f"表情 {i}" for i in range(1, emotion_count + 1)]
                
                emotion_var = tk.StringVar(value=f"表情 {emotion_index}")
                emotion_combo = ttk.Combobox(
                    char_frame,
                    textvariable=emotion_var,
                    values=emotion_options,
                    state="readonly",
                    width=12
                )
                emotion_combo.pack(side=tk.LEFT)
                
                # 绑定角色改变事件，更新表情选项
                char_combo.bind("<<ComboboxSelected>>", 
                            lambda e: self._on_character_selected(char_combo, emotion_combo))
                
                # 存储变量
                self.ui_widgets["character_var"] = char_var
                self.ui_widgets["emotion_index_var"] = emotion_var
                
                # 初始更新状态
                self._update_character_selection_state(use_fixed_var, char_combo, emotion_combo)
            
            else:  # 背景组件
                # 背景组件: 添加"使用指定背景"复选框
                bg_frame = ttk.Frame(parent_frame)
                bg_frame.pack(fill=tk.X, pady=(0, 5))
                
                # 使用指定背景复选框
                use_specified_bg_var = tk.BooleanVar(value=current_config.get("use_fixed_background", False))
                use_specified_bg_cb = ttk.Checkbutton(
                    bg_frame,
                    text="使用指定背景",
                    variable=use_specified_bg_var,
                    command=lambda: self._update_background_selection_state(use_specified_bg_var, 
                                                                        overlay_combo)
                )
                use_specified_bg_cb.pack(side=tk.LEFT, padx=(0, 10))
                
                # 存储变量
                self.ui_widgets["use_fixed_background_var"] = use_specified_bg_var

        # 图片文件选择（根据组件类型选择不同的文件列表）
        if component_type in ["textbox", "namebox", "extra"] or (component_type == "background"):
            row_frame = ttk.Frame(parent_frame)
            row_frame.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Label(row_frame, text="图片文件:").pack(side=tk.LEFT, padx=(0, 5))
            
            # 根据组件类型选择文件列表
            if component_type == "background":
                file_list = [""] + self.background_files
            else:
                file_list = [""] + self.shader_files
            
            overlay_var = tk.StringVar(value=current_config.get("overlay", ""))
            overlay_combo = ttk.Combobox(
                row_frame,
                textvariable=overlay_var,
                values=file_list,
                state="readonly",
                width=25
            )
            overlay_combo.pack(side=tk.LEFT, padx=(0, 15))
            
            # 存储变量
            self.ui_widgets["overlay_var"] = overlay_var
            
            # 如果是背景组件，初始更新状态
            if component_type == "background":
                self._update_background_selection_state(use_specified_bg_var, overlay_combo)
        
        # 对齐方式
        align_row = ttk.Frame(parent_frame)
        align_row.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(align_row, text="对齐方式:").pack(side=tk.LEFT, padx=(0, 5))
        
        align_options = list(ALIGN_MAPPING.values())
        current_align = current_config.get("align", "top-left")
        align_display = ALIGN_MAPPING.get(current_align, "左上")
        
        align_var = tk.StringVar(value=align_display)
        align_combo = ttk.Combobox(
            align_row,
            textvariable=align_var,
            values=align_options,
            state="readonly",
            width=10
        )
        align_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        # 存储变量
        self.ui_widgets["align_var"] = align_var
        
        # 第二行：偏移和缩放
        offset_frame = ttk.Frame(parent_frame)
        offset_frame.pack(fill=tk.X, pady=(0, 5))
        
        # X偏移
        ttk.Label(offset_frame, text="X偏移:").pack(side=tk.LEFT, padx=(0, 5))
        offset_x_var = tk.StringVar(value=str(current_config.get("offset_x", 0)))
        offset_x_entry = ttk.Entry(offset_frame, textvariable=offset_x_var, width=8)
        offset_x_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Y偏移
        ttk.Label(offset_frame, text="Y偏移:").pack(side=tk.LEFT, padx=(0, 5))
        offset_y_var = tk.StringVar(value=str(current_config.get("offset_y", 0)))
        offset_y_entry = ttk.Entry(offset_frame, textvariable=offset_y_var, width=8)
        offset_y_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 缩放（角色、文本框、名称框、额外组件、背景组件都支持缩放）
        if component_type in ["character", "textbox", "namebox", "extra", "background"]:
            ttk.Label(offset_frame, text="缩放:").pack(side=tk.LEFT, padx=(0, 5))
            scale_var = tk.StringVar(value=str(current_config.get("scale", 1.0)))
            scale_entry = ttk.Entry(offset_frame, textvariable=scale_var, width=8)
            scale_entry.pack(side=tk.LEFT)
            
            # 存储变量
            self.ui_widgets["scale_var"] = scale_var
        
        # 存储偏移变量
        self.ui_widgets["offset_x_var"] = offset_x_var
        self.ui_widgets["offset_y_var"] = offset_y_var
        
        # 第三行：填充方式（对extra和background类型）
        if component_type in ["extra", "background"]:
            fill_frame = ttk.Frame(parent_frame)
            fill_frame.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Label(fill_frame, text="填充方式:").pack(side=tk.LEFT, padx=(0, 5))
            
            # 获取当前填充模式并转换为中文显示
            current_fill_mode = current_config.get("fill_mode", "fit")
            fill_mode_mapping = {"fit": "适应边界", "width": "适应宽度", "height": "适应高度"}
            fill_mode_display = fill_mode_mapping.get(current_fill_mode, "适应边界")
            
            fill_mode_var = tk.StringVar(value=fill_mode_display)
            fill_mode_combo = ttk.Combobox(
                fill_frame,
                textvariable=fill_mode_var,
                values=["适应边界", "适应宽度", "适应高度"],
                state="readonly",
                width=12
            )
            fill_mode_combo.pack(side=tk.LEFT)
            
            # 存储变量
            self.ui_widgets["fill_mode_var"] = fill_mode_var

    # 新增辅助方法
    def _update_character_selection_state(self, use_fixed_var, char_combo, emotion_combo):
        """更新角色选择控件的状态"""
        if use_fixed_var.get():
            char_combo.config(state="readonly")
            emotion_combo.config(state="readonly")
        else:
            char_combo.config(state="disabled")
            emotion_combo.config(state="disabled")
    
    def _update_background_selection_state(self, use_specified_var, overlay_combo):
        """更新背景选择控件的状态"""
        if use_specified_var.get():
            # 选中"使用指定背景"时，启用图片选择
            overlay_combo.config(state="readonly")
        else:
            # 未选中"使用指定背景"时，禁用图片选择并清空
            overlay_combo.config(state="disabled")
            
    def _on_character_selected(self, char_combo, emotion_combo):
        """角色选择改变事件"""
        from config import CONFIGS
        
        selected_text = char_combo.get()
        if selected_text:
            # 提取角色ID
            char_id = selected_text.split("(")[-1].rstrip(")")
            
            # 获取角色的表情数量
            if char_id in CONFIGS.mahoshojo:
                emotion_count = CONFIGS.mahoshojo[char_id].get("emotion_count", 1)
                # 更新表情选项
                emotion_options = [f"表情 {i}" for i in range(1, emotion_count + 1)]
                emotion_combo["values"] = emotion_options
                emotion_combo.set("表情 1")
                
    def _create_text_properties(self, parent_frame, current_config):
        """创建文本组件的属性编辑器"""
        # 文本内容
        text_frame = ttk.Frame(parent_frame)
        text_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(text_frame, text="文本内容:").pack(side=tk.LEFT, padx=(0, 5))
        
        text_var = tk.StringVar(value=current_config.get("text", ""))
        text_entry = ttk.Entry(text_frame, textvariable=text_var, width=40)
        text_entry.pack(side=tk.LEFT)
        
        # 存储变量
        self.ui_widgets["text_var"] = text_var
        
        # 字体设置
        font_frame = ttk.Frame(parent_frame)
        font_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(font_frame, text="字体:").pack(side=tk.LEFT, padx=(0, 5))
        
        font_family_var = tk.StringVar(value=current_config.get("font_family", "font3"))
        font_combo = ttk.Combobox(
            font_frame,
            textvariable=font_family_var,
            values=self.available_fonts,
            state="readonly",
            width=15
        )
        font_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(font_frame, text="字号:").pack(side=tk.LEFT, padx=(0, 5))
        
        font_size_var = tk.StringVar(value=str(current_config.get("font_size", 90)))
        font_size_entry = ttk.Entry(font_frame, textvariable=font_size_var, width=8)
        font_size_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(font_frame, text="行宽:").pack(side=tk.LEFT, padx=(0, 5))
        
        max_width_var = tk.StringVar(value=str(current_config.get("max_width", 500)))
        max_width_entry = ttk.Entry(font_frame, textvariable=max_width_var, width=8)
        max_width_entry.pack(side=tk.LEFT)
        
        # 存储变量
        self.ui_widgets["font_family_var"] = font_family_var
        self.ui_widgets["font_size_var"] = font_size_var
        self.ui_widgets["max_width_var"] = max_width_var
        
        # 颜色设置
        color_frame = ttk.Frame(parent_frame)
        color_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(color_frame, text="文字颜色:").pack(side=tk.LEFT, padx=(0, 5))
        
        text_color_var = tk.StringVar(value=current_config.get("text_color", "#FFFFFF"))
        text_color_entry = ttk.Entry(color_frame, textvariable=text_color_var, width=12)
        text_color_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(color_frame, text="阴影颜色:").pack(side=tk.LEFT, padx=(0, 5))
        
        shadow_color_var = tk.StringVar(value=current_config.get("shadow_color", "#000000"))
        shadow_color_entry = ttk.Entry(color_frame, textvariable=shadow_color_var, width=12)
        shadow_color_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 阴影偏移
        shadow_frame = ttk.Frame(parent_frame)
        shadow_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(shadow_frame, text="阴影偏移X:").pack(side=tk.LEFT, padx=(0, 5))
        
        shadow_offset_x_var = tk.StringVar(value=str(current_config.get("shadow_offset_x", 4)))
        shadow_x_entry = ttk.Entry(shadow_frame, textvariable=shadow_offset_x_var, width=6)
        shadow_x_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(shadow_frame, text="Y:").pack(side=tk.LEFT, padx=(0, 5))
        
        shadow_offset_y_var = tk.StringVar(value=str(current_config.get("shadow_offset_y", 4)))
        shadow_y_entry = ttk.Entry(shadow_frame, textvariable=shadow_offset_y_var, width=6)
        shadow_y_entry.pack(side=tk.LEFT)
        
        # 对齐方式（文本组件也需要对齐）
        align_frame = ttk.Frame(parent_frame)
        align_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(align_frame, text="对齐方式:").pack(side=tk.LEFT, padx=(0, 5))
        
        align_options = list(ALIGN_MAPPING.values())
        current_align = current_config.get("align", "top-left")
        align_display = ALIGN_MAPPING.get(current_align, "左上")
        
        align_var = tk.StringVar(value=align_display)
        align_combo = ttk.Combobox(
            align_frame,
            textvariable=align_var,
            values=align_options,
            state="readonly",
            width=10
        )
        align_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(align_frame, text="X偏移:").pack(side=tk.LEFT, padx=(0, 5))
        offset_x_var = tk.StringVar(value=str(current_config.get("offset_x", 0)))
        offset_x_entry = ttk.Entry(align_frame, textvariable=offset_x_var, width=8)
        offset_x_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(align_frame, text="Y偏移:").pack(side=tk.LEFT, padx=(0, 5))
        offset_y_var = tk.StringVar(value=str(current_config.get("offset_y", 0)))
        offset_y_entry = ttk.Entry(align_frame, textvariable=offset_y_var, width=8)
        offset_y_entry.pack(side=tk.LEFT)
        
        # 存储变量
        self.ui_widgets["text_color_var"] = text_color_var
        self.ui_widgets["shadow_color_var"] = shadow_color_var
        self.ui_widgets["shadow_offset_x_var"] = shadow_offset_x_var
        self.ui_widgets["shadow_offset_y_var"] = shadow_offset_y_var
        self.ui_widgets["align_var"] = align_var
        self.ui_widgets["offset_x_var"] = offset_x_var
        self.ui_widgets["offset_y_var"] = offset_y_var
    
    def _on_type_changed(self, new_type_display):
        """组件类型改变事件"""
        # 从显示文本获取类型值
        reverse_type_mapping = {v: k for k, v in COMPONENT_TYPES.items()}
        new_type = reverse_type_mapping.get(new_type_display, "extra")
        
        # 更新组件类型
        self.component_config["type"] = new_type
        
        # 应用新类型的默认值（仅对缺失的属性）
        if new_type in COMPONENT_PROPERTIES:
            defaults = COMPONENT_PROPERTIES[new_type]["defaults"]
            for key, default_value in defaults.items():
                if key not in self.component_config or key == "type":
                    self.component_config[key] = default_value
        
        # 重新填充属性框架
        self._fill_props_frame()
        
        # 更新顶部框架显示
        self._fill_top_frame()
    
    def get_current_config(self):
        """获取当前配置（从UI控件中收集值）"""
        config = copy.deepcopy(self.component_config)
        
        # 从UI控件收集值
        if "enabled_var" in self.ui_widgets:
            config["enabled"] = self.ui_widgets["enabled_var"].get()
        
        if "name_var" in self.ui_widgets:
            config["name"] = self.ui_widgets["name_var"].get()
        
        if "type_var" in self.ui_widgets:
            type_display = self.ui_widgets["type_var"].get()
            reverse_type_mapping = {v: k for k, v in COMPONENT_TYPES.items()}
            config["type"] = reverse_type_mapping.get(type_display, "extra")
        
        # 收集通用属性
        if "align_var" in self.ui_widgets:
            align_display = self.ui_widgets["align_var"].get()
            align_value = REVERSE_ALIGN_MAPPING.get(align_display, "top-left")
            config["align"] = align_value
        
        if "offset_x_var" in self.ui_widgets:
            try:
                config["offset_x"] = int(self.ui_widgets["offset_x_var"].get())
            except ValueError:
                config["offset_x"] = 0
        
        if "offset_y_var" in self.ui_widgets:
            try:
                config["offset_y"] = int(self.ui_widgets["offset_y_var"].get())
            except ValueError:
                config["offset_y"] = 0
        
        # 根据组件类型收集其他属性
        component_type = config.get("type", "extra")
        
        # 收集角色的固定角色属性
        if component_type == "character":
            if "use_fixed_character_var" in self.ui_widgets:
                config["use_fixed_character"] = self.ui_widgets["use_fixed_character_var"].get()
            
            # 只有在使用固定角色时才保存character_name和emotion_index
            if config.get("use_fixed_character", False):
                if "character_var" in self.ui_widgets:
                    selected_char = self.ui_widgets["character_var"].get()
                    if selected_char:
                        # 提取角色ID
                        char_id = selected_char.split("(")[-1].rstrip(")")
                        config["character_name"] = char_id
                    else:
                        # 如果没有选择角色，使用组件配置中的值
                        config["character_name"] = self.component_config.get("character_name", "")
                
                if "emotion_index_var" in self.ui_widgets:
                    try:
                        emotion_text = self.ui_widgets["emotion_index_var"].get()
                        emotion_index = int(emotion_text.split()[-1])
                        config["emotion_index"] = emotion_index
                    except (ValueError, IndexError):
                        config["emotion_index"] = 1
            else:
                # 不使用固定角色时，删除这些字段
                config.pop("character_name", None)
                config.pop("emotion_index", None)
        
        # 收集背景的固定背景属性
        elif component_type == "background":
            if "use_fixed_background_var" in self.ui_widgets:
                config["use_fixed_background"] = self.ui_widgets["use_fixed_background_var"].get()
            
            # 只有在使用固定背景时才保存overlay
            if config.get("use_fixed_background", False):
                if "overlay_var" in self.ui_widgets:
                    config["overlay"] = self.ui_widgets["overlay_var"].get()
            else:
                # 不使用固定背景时，删除overlay字段
                config.pop("overlay", None)
        
        # 处理缩放设置
        if "scale_var" in self.ui_widgets:
            try:
                config["scale"] = float(self.ui_widgets["scale_var"].get())
            except ValueError:
                # 使用默认值
                if component_type == "character":
                    config["scale"] = 1.6  # 角色默认缩放
                elif component_type == "namebox":
                    config["scale"] = 1.2  # 名称框默认缩放
                else:
                    config["scale"] = 1.0  # 其他组件默认缩放
        
        # 处理图片文件设置（除了背景组件，因为背景已经在上面的分支处理了）
        if component_type in ["textbox", "namebox", "extra"]:
            if "overlay_var" in self.ui_widgets:
                config["overlay"] = self.ui_widgets["overlay_var"].get()
        
        # 处理填充模式
        if component_type in ["extra", "background"] and "fill_mode_var" in self.ui_widgets:
            fill_mode_display = self.ui_widgets["fill_mode_var"].get()
            fill_mode_mapping = {"适应边界": "fit", "适应宽度": "width", "适应高度": "height"}
            config["fill_mode"] = fill_mode_mapping.get(fill_mode_display, "fit")
        
        elif component_type == "text":
            # 文本组件属性
            for key in ["text", "font_family", "text_color", "shadow_color"]:
                var_key = f"{key}_var"
                if var_key in self.ui_widgets:
                    config[key] = self.ui_widgets[var_key].get()
            
            for key in ["font_size", "shadow_offset_x", "shadow_offset_y", "max_width"]:
                var_key = f"{key}_var"
                if var_key in self.ui_widgets:
                    try:
                        config[key] = int(self.ui_widgets[var_key].get())
                    except ValueError:
                        config[key] = COMPONENT_DEFAULTS["text"].get(key, 0)
        
        # 移除默认值的属性
        final_config = {}
        for key, value in config.items():
            # 如果键在默认值表中且值等于默认值，跳过保存
            if key in DEFAULT_VALUES and str(value) == str(DEFAULT_VALUES[key]):
                continue
            # 特殊的：对于角色组件，不使用固定角色时，即使有character_name和emotion_index也跳过
            if component_type == "character" and key in ["character_name", "emotion_index"]:
                if not config.get("use_fixed_character", False):
                    continue
            # 特殊的：对于背景组件，不使用固定背景时，即使有overlay也跳过
            elif component_type == "background" and key == "overlay":
                if not config.get("use_fixed_background", False):
                    continue
            final_config[key] = value
        return final_config
    
    def _on_enabled_changed(self, enabled_var):
        """启用状态改变"""
        self.component_config["enabled"] = enabled_var.get()
    
    def _move_component(self, direction):
        """移动组件"""
        # 获取当前配置
        current_config = self.get_current_config()
        current_layer = current_config.get("layer", 0)
        
        # 获取所有组件的图层信息
        all_layers = []
        for editor in self.style_window.component_editors.values():
            if editor != self:  # 排除自己
                config = editor.get_current_config()
                layer = config.get("layer", 0)
                all_layers.append((editor, layer))
        
        if direction == "up":
            # 上移：找到所有比当前图层值大的组件
            higher_components = [(editor, layer) for editor, layer in all_layers if layer > current_layer]
            if not higher_components:
                return  # 已经在最上面
            
            # 找到最接近的更高图层值
            min_higher_layer = min(layer for _, layer in higher_components)
            
            # 找到对应的组件
            target_editor = None
            for editor, layer in higher_components:
                if layer == min_higher_layer:
                    target_editor = editor
                    break
            
            if target_editor:
                # 交换图层值（注意：这里只交换图层值，不更新_max_layer）
                target_config = target_editor.get_current_config()
                
                # 交换图层值
                self.component_config["layer"] = min_higher_layer
                target_config["layer"] = current_layer
                
                # 更新两个组件的配置
                self.component_config = copy.deepcopy(self.component_config)
                target_editor.component_config = copy.deepcopy(target_config)
                
                # 重新填充UI
                self._fill_top_frame()
                self._fill_props_frame()
                target_editor._fill_top_frame()
                target_editor._fill_props_frame()
                
                # 重新排序UI
                self.style_window._reorder_component_editors()
        
        else:  # down
            # 下移：找到所有比当前图层值小的组件
            lower_components = [(editor, layer) for editor, layer in all_layers if layer < current_layer]
            if not lower_components:
                return  # 已经在最下面
            
            # 找到最接近的更低图层值
            max_lower_layer = max(layer for _, layer in lower_components)
            
            # 找到对应的组件
            target_editor = None
            for editor, layer in lower_components:
                if layer == max_lower_layer:
                    target_editor = editor
                    break
            
            if target_editor:
                # 交换图层值（注意：这里只交换图层值，不更新_max_layer）
                target_config = target_editor.get_current_config()
                
                # 交换图层值
                self.component_config["layer"] = max_lower_layer
                target_config["layer"] = current_layer
                
                # 更新两个组件的配置
                self.component_config = copy.deepcopy(self.component_config)
                target_editor.component_config = copy.deepcopy(target_config)
                
                # 重新填充UI
                self._fill_top_frame()
                self._fill_props_frame()
                target_editor._fill_top_frame()
                target_editor._fill_props_frame()
                
                # 重新排序UI
                self.style_window._reorder_component_editors()
    
    def _delete_component(self):
        """删除组件"""
        # 使用图层值作为标识符
        self.style_window._remove_component_by_layer(self.layer)
    
    def toggle_expand(self):
        """切换展开/收起状态"""
        if self.is_expanded:
            # 收起：隐藏属性框架，检查并更新名字
            self._update_name_from_ui()  # 新增：更新名字
            self.props_frame.pack_forget()
            self.ui_widgets["edit_btn"].config(text="编辑")
        else:
            # 展开：显示属性框架
            self.props_frame.pack(fill=tk.X, pady=(10, 0))
            self.ui_widgets["edit_btn"].config(text="收起")
        
        self.is_expanded = not self.is_expanded

    def _update_name_from_ui(self):
        """从UI控件中更新组件名称，并刷新顶部框架显示"""
        # 获取当前配置中的名称
        current_config = self.component_config
        
        # 从UI中获取新名称
        if "name_var" in self.ui_widgets:
            new_name = self.ui_widgets["name_var"].get()
            
            # 如果名称有变化，则更新配置
            if new_name != current_config.get("name", ""):
                current_config["name"] = new_name
                
                # 重新填充顶部框架以显示新名称
                self._fill_top_frame()
                print(f"组件名称已更新为: {new_name}")

    def _get_shader_files(self):
        """获取shader文件夹中的图片文件列表"""
        shader_dir = get_resource_path(os.path.join("assets", "shader"))
        shader_files = []
        
        if os.path.exists(shader_dir):
            for file in os.listdir(shader_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                    shader_files.append(file)
        
        return sorted(shader_files)
    
    def _get_background_files(self):
        """获取background文件夹中的图片文件列表"""
        background_dir = get_resource_path(os.path.join("assets", "background"))
        background_files = []
        
        if os.path.exists(background_dir):
            for file in os.listdir(background_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                    background_files.append(file)
        
        return sorted(background_files)

    def pack(self, **kwargs):
        """包装pack方法"""
        self.main_frame.pack(**kwargs)
    
    def pack_forget(self):
        """包装pack_forget方法"""
        self.main_frame.pack_forget()
    
    def destroy(self):
        """销毁组件"""
        self.main_frame.destroy()