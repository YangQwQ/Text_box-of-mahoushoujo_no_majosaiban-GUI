# -*- coding: utf-8 -*-
"""PyQt样式编辑窗口模块 - 简化版本"""

from PySide6.QtCore import Qt, Slot, Signal, QMetaObject
from PySide6.QtWidgets import (QDialog, QMessageBox, QVBoxLayout, QGroupBox, QMenu)
from ui.components import (
    CharacterComponent, BackgroundComponent, 
    ImageComponent, NameboxComponent,
    TextComponent
)
from config import CONFIGS
from image_processor import clear_cache
from path_utils import get_available_fonts

# 组件类型定义
COMPONENT_TYPES = {
    "character": "角色",
    "background": "背景",
    "extra": "图片",
    "namebox": "名字框",
    "text": "文本"
}

# 对齐方式映射
ALIGN_MAPPING = {
    "左上": "top-left",
    "中上": "top-center",
    "右上": "top-right",
    "左中": "middle-left",
    "居中": "middle-center",
    "右中": "middle-right",
    "左下": "bottom-left",
    "中下": "bottom-center",
    "右下": "bottom-right"
}

# 反向映射
REVERSE_ALIGN_MAPPING = {v: k for k, v in ALIGN_MAPPING.items()}

# 统一的默认值定义（不再按组件类型分类）
DEFAULT_VALUES = {
    "overlay": "",
    "name": "",
    "align": "top-left",
    "offset_x": 0,
    "offset_y": 0,
    "scale": 1.0,
    "fill_mode": "fit"
}

class ComponentEditor(QGroupBox):
    """组件编辑器"""
    
    def __init__(self, parent, style_window, component_config, index):
        super().__init__(parent)
        self.parent_widget = parent
        self.style_window = style_window
        self.component_config = component_config.copy()
        self.index = index
        self.component_type = component_config.get("type", "character")

        # 设置组件标题
        comp_type_name = COMPONENT_TYPES.get(self.component_type, self.component_type)
        self.setTitle(f"{comp_type_name}组件 (图层: {self.component_config.get('layer', 0)})")
        
        # 展开状态
        self.is_expanded = False
        
        self.setup_ui()
        self._load_component_config()
        self.setup_connections()

    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 根据组件类型选择对应的UI组件
        if self.component_type == "character":
            self.component_widget = CharacterComponent()
        elif self.component_type == "background":
            self.component_widget = BackgroundComponent()
        elif self.component_type == "extra":
            self.component_widget = ImageComponent()
        elif self.component_type == "namebox":
            self.component_widget = NameboxComponent()
        elif self.component_type == "text":
            self.component_widget = TextComponent()
        else:
            self.component_widget = ImageComponent()
        
        # 将组件添加到布局
        layout.addWidget(self.component_widget)
        
        # 初始设置为收起状态
        if hasattr(self.component_widget, 'widget_detail'):
            self.component_widget.widget_detail.hide()
    
    def setup_connections(self):
        """设置连接"""
        # 展开按钮连接
        if hasattr(self.component_widget, 'button_edit'):
            self.component_widget.button_edit.clicked.connect(self._toggle_expand)
        
        # 角色选择连接（仅角色组件）
        if self.component_type == "character" and hasattr(self.component_widget, 'combo_character'):
            self.component_widget.combo_character.currentIndexChanged.connect(self._on_character_changed)
        
        # 删除按钮连接
        if hasattr(self.component_widget, 'button_delete'):
            self.component_widget.button_delete.clicked.connect(self.delete_component)
        
        # 上移下移按钮
        if hasattr(self.component_widget, 'button_move_up'):
            self.component_widget.button_move_up.clicked.connect(lambda: self.move_component(-1))
        
        if hasattr(self.component_widget, 'button_move_down'):
            self.component_widget.button_move_down.clicked.connect(lambda: self.move_component(1))
    
    def _on_character_changed(self):
        """角色选择改变时更新表情列表"""
        if self.component_type != "character":
            return
        
        # 获取当前选择的角色ID
        character_name = self.component_widget.combo_character.currentData()
        
        if character_name:
            # 更新角色名到配置
            self.component_config["character_name"] = character_name
            
            # 更新表情列表
            self._update_emotion_list(character_name)
            
            # 更新表情筛选列表
            if hasattr(self.component_widget, 'combo_emotion_filter'):
                self._update_emotion_filter_list(character_name)

    def _toggle_expand(self):
        """切换展开/收起状态"""
        if hasattr(self.component_widget, 'widget_detail'):
            if self.is_expanded:
                self.component_widget.widget_detail.hide()
                # self.component_widget.parent().setMaximumHeight(65)
                # self.component_widget.setMaximumHeight(65)
                # self.component_widget.setMinimumHeight(0)
                if hasattr(self.component_widget, 'button_edit'):
                    self.component_widget.button_edit.setText("展开")
            else:
                self.component_widget.widget_detail.show()
                # self.component_widget.parent().setMaximumHeight(650)
                # self.component_widget.setMaximumHeight(16777215)
                # self.component_widget.setMinimumHeight(0)
                if hasattr(self.component_widget, 'button_edit'):
                    self.component_widget.button_edit.setText("收起")
            
            self.is_expanded = not self.is_expanded
    
    def _update_emotion_list(self, character_id):
        """更新表情列表"""
        if not hasattr(self.component_widget, 'combo_emotion'):
            return
        
        char_meta = CONFIGS.mahoshojo.get(character_id, {})
        emotion_count = char_meta.get("emotion_count", 9)
        
        # 清空并重新填充表情列表
        self.component_widget.combo_emotion.clear()
        for i in range(1, emotion_count + 1):
            self.component_widget.combo_emotion.addItem(f"表情 {i}", i)
        
        # 设置默认选择第一个表情
        self.component_widget.combo_emotion.setCurrentIndex(0)

    def _load_component_config(self):
        """加载组件配置到UI"""
        # 设置组件名称
        if hasattr(self.component_widget, 'label_name'):
            name = self.component_config.get("name", "未命名")
            self.component_widget.label_name.setText(name)
        
        if hasattr(self.component_widget, 'edit_component_name'):
            name = self.component_config.get("name", "未命名")
            self.component_widget.edit_component_name.setText(name)
        
        # 设置启用状态
        if hasattr(self.component_widget, 'checkbox_enable'):
            enabled = self.component_config.get("enabled", True)
            self.component_widget.checkbox_enable.setChecked(enabled)
        
        # 初始化并设置对齐方式
        if hasattr(self.component_widget, 'combo_align'):
            # 先清空并初始化选项
            self.component_widget.combo_align.clear()
            align_options = list(ALIGN_MAPPING.keys())
            self.component_widget.combo_align.addItems(align_options)
            
            # 设置当前值
            align_str = self.component_config.get("align", "")
            if align_str and align_str in REVERSE_ALIGN_MAPPING:
                self.component_widget.combo_align.setCurrentText(REVERSE_ALIGN_MAPPING[align_str])
        
        # 设置位置和缩放
        if hasattr(self.component_widget, 'edit_offset_x'):
            offset_x = self.component_config.get("offset_x", 0)
            self.component_widget.edit_offset_x.setText(str(offset_x))
        
        if hasattr(self.component_widget, 'edit_offset_y'):
            offset_y = self.component_config.get("offset_y", 0)
            self.component_widget.edit_offset_y.setText(str(offset_y))
        
        if hasattr(self.component_widget, 'edit_scale'):
            scale = self.component_config.get("scale", 1.0)
            self.component_widget.edit_scale.setText(str(scale))
        
        # 填充方式（背景和图片组件）
        if self.component_type in ["background", "extra"] and hasattr(self.component_widget, 'combo_fill_mode'):
            # 先初始化选项
            self.component_widget.combo_fill_mode.clear()
            fill_mode_options = ["适应边界", "适应宽度", "适应高度"]
            self.component_widget.combo_fill_mode.addItems(fill_mode_options)
            
            # 设置当前值
            fill_mode = self.component_config.get("fill_mode", "")
            if fill_mode:
                fill_mode_map = {
                    "fit": "适应边界",
                    "width": "适应宽度",
                    "height": "适应高度"
                }
                if fill_mode in fill_mode_map:
                    self.component_widget.combo_fill_mode.setCurrentText(fill_mode_map[fill_mode])
        
        # 组件类型特定配置
        if self.component_type == "character":
            self._load_character_config()
        elif self.component_type == "background":
            self._load_background_config()
        elif self.component_type == "extra":
            self._load_extra_config()
        elif self.component_type == "namebox":
            self._load_namebox_config()
        elif self.component_type == "text":
            self._load_text_config()
        
    def _load_character_config(self):
        """加载角色组件配置"""
        if not hasattr(self.component_widget, 'combo_character'):
            return
        
        # 初始化角色选择下拉框
        self.component_widget.combo_character.clear()
        for char_id in CONFIGS.character_list:
            char_name = CONFIGS.get_character(char_id, full_name=True)
            self.component_widget.combo_character.addItem(char_name, char_id)
        
        # 设置当前角色
        character_name = self.component_config.get("character_name", "")
        if character_name:
            index = self.component_widget.combo_character.findData(character_name)
            if index >= 0:
                self.component_widget.combo_character.setCurrentIndex(index)
            else:
                # 如果找不到对应的角色，选择第一个
                self.component_widget.combo_character.setCurrentIndex(0)
                if CONFIGS.character_list:
                    character_name = CONFIGS.character_list[0]
                    self.component_config["character_name"] = character_name
        else:
            # 如果没有设置角色，选择第一个
            self.component_widget.combo_character.setCurrentIndex(0)
            if CONFIGS.character_list:
                character_name = CONFIGS.character_list[0]
                self.component_config["character_name"] = character_name
        
        # 初始化表情筛选下拉框
        if hasattr(self.component_widget, 'combo_emotion_filter'):
            self.component_widget.combo_emotion_filter.clear()
            emotion_filters, _ = CONFIGS.get_emotion_filter_options(character_name if character_name else None)
            self.component_widget.combo_emotion_filter.addItems(emotion_filters)
        
        # 使用固定角色
        use_fixed = self.component_config.get("use_fixed_character", False)
        if hasattr(self.component_widget, 'checkbox_fixed_emotion'):
            self.component_widget.checkbox_fixed_emotion.setChecked(use_fixed)
        
        # 初始化表情选择下拉框
        if hasattr(self.component_widget, 'combo_emotion'):
            self.component_widget.combo_emotion.clear()
            # 填充表情列表
            if character_name:
                char_meta = CONFIGS.mahoshojo.get(character_name, {})
                emotion_count = char_meta.get("emotion_count", 9)
                for i in range(1, emotion_count + 1):
                    self.component_widget.combo_emotion.addItem(f"表情 {i}", i)
            
            # 设置当前表情
            emotion_index = self.component_config.get("emotion_index", 1)
            index = self.component_widget.combo_emotion.findData(emotion_index)
            if index >= 0:
                self.component_widget.combo_emotion.setCurrentIndex(index)
    
    def _load_background_config(self):
        """加载背景组件配置"""
        # 使用固定背景
        use_fixed = self.component_config.get("use_fixed_background", False)
        if hasattr(self.component_widget, 'checkbox_fixed_background'):
            self.component_widget.checkbox_fixed_background.setChecked(use_fixed)
        
        # 背景图片 - 从 CONFIGS.background_list 加载
        overlay = self.component_config.get("overlay", "")
        if hasattr(self.component_widget, 'combo_background'):
            # 清空现有选项
            self.component_widget.combo_background.clear()
            self.component_widget.combo_background.addItem("无", "")
            
            # 从 CONFIGS.background_list 添加背景文件
            for bg_file in CONFIGS.background_list:
                self.component_widget.combo_background.addItem(bg_file, bg_file)
            
            # 如果 overlay 存在但不在列表中（可能是用户手动输入的），也要添加
            if overlay and not overlay.startswith("#") and overlay not in CONFIGS.background_list:
                self.component_widget.combo_background.addItem(overlay, overlay)
            
            # 设置当前值
            if overlay:
                index = self.component_widget.combo_background.findData(overlay)
                if index >= 0:
                    self.component_widget.combo_background.setCurrentIndex(index)
    
    def _load_extra_config(self):
        """加载图片组件配置"""
        overlay = self.component_config.get("overlay", "")
        if overlay and hasattr(self.component_widget, 'combo_image'):
            self.component_widget.combo_image.addItem(overlay, overlay)
            self.component_widget.combo_image.setCurrentIndex(0)
    
    def _load_namebox_config(self):
        """加载名字框组件配置"""
        overlay = self.component_config.get("overlay", "")
        if overlay and hasattr(self.component_widget, 'combo_image'):
            self.component_widget.combo_image.addItem(overlay, overlay)
            self.component_widget.combo_image.setCurrentIndex(0)
    
    def _load_text_config(self):
        """加载文本组件配置"""
        # 文本内容
        text = self.component_config.get("text", "")
        if text and hasattr(self.component_widget, 'edit_text_content'):
            self.component_widget.edit_text_content.setText(text)
        
        # 字体
        font_family = self.component_config.get("font_family", "font2")
        if hasattr(self.component_widget, 'combo_font'):
            fonts = get_available_fonts()
            self.component_widget.combo_font.addItems(fonts)
            index = self.component_widget.combo_font.findText(font_family)
            if index >= 0:
                self.component_widget.combo_font.setCurrentIndex(index)
        
        # 字号
        font_size = self.component_config.get("font_size", 60)
        if hasattr(self.component_widget, 'edit_text_size'):
            self.component_widget.edit_text_size.setText(str(font_size))
        
        # 文本颜色
        text_color = self.component_config.get("text_color", "#000000")
        if hasattr(self.component_widget, 'edit_text_color'):
            self.component_widget.edit_text_color.setText(text_color)
        
        # 最大宽度
        max_width = self.component_config.get("max_width", 500)
        if hasattr(self.component_widget, 'edit_line_width'):
            self.component_widget.edit_line_width.setText(str(max_width))
        
        # 阴影设置
        shadow_color = self.component_config.get("shadow_color", "#000000")
        if hasattr(self.component_widget, 'edit_shadow_color'):
            self.component_widget.edit_shadow_color.setText(shadow_color)
        
        shadow_x = self.component_config.get("shadow_offset_x", 0)
        if hasattr(self.component_widget, 'edit_shadow_x'):
            self.component_widget.edit_shadow_x.setText(str(shadow_x))
        
        shadow_y = self.component_config.get("shadow_offset_y", 0)
        if hasattr(self.component_widget, 'edit_shadow_y'):
            self.component_widget.edit_shadow_y.setText(str(shadow_y))
    
    def get_current_config(self):
        """获取当前组件配置 - 简化版本，移除默认值"""
        config = {}
        
        # 基本属性
        config["type"] = self.component_type
        
        # 图层
        config["layer"] = self.component_config.get("layer", 0)
        
        # 组件名称
        if hasattr(self.component_widget, 'edit_component_name'):
            name = self.component_widget.edit_component_name.text()
            if name and name != "未命名":
                config["name"] = name
        elif hasattr(self.component_widget, 'label_name'):
            name = self.component_widget.label_name.text()
            if name and name != "未命名":
                config["name"] = name
        
        # 启用状态
        enabled = self.component_widget.checkbox_enable.isChecked()
        config["enabled"] = enabled
        
        # 对齐方式
        if hasattr(self.component_widget, 'combo_align'):
            align_name = self.component_widget.combo_align.currentText()
            if align_name in ALIGN_MAPPING:
                align_str = ALIGN_MAPPING[align_name]
                if align_str != DEFAULT_VALUES.get("align", ""):
                    config["align"] = align_str
        
        # 位置和缩放
        if hasattr(self.component_widget, 'edit_offset_x'):
            offset_x_text = self.component_widget.edit_offset_x.text()
            try:
                offset_x = int(offset_x_text) if offset_x_text else 0
                if offset_x != DEFAULT_VALUES.get("offset_x", 0):
                    config["offset_x"] = offset_x
            except:
                pass
        
        if hasattr(self.component_widget, 'edit_offset_y'):
            offset_y_text = self.component_widget.edit_offset_y.text()
            try:
                offset_y = int(offset_y_text) if offset_y_text else 0
                if offset_y != DEFAULT_VALUES.get("offset_y", 0):
                    config["offset_y"] = offset_y
            except:
                pass
        
        if hasattr(self.component_widget, 'edit_scale'):
            scale_text = self.component_widget.edit_scale.text()
            try:
                scale = float(scale_text) if scale_text else 1.0
                if scale != DEFAULT_VALUES.get("scale", 1.0):
                    config["scale"] = scale
            except:
                pass
        
        # 填充方式（背景和图片组件）
        if self.component_type in ["background", "extra"] and hasattr(self.component_widget, 'combo_fill_mode'):
            fill_text = self.component_widget.combo_fill_mode.currentText()
            fill_mode_map = {
                "适应宽度": "width",
                "适应高度": "height",
                "适应边界": "fit"
            }
            fill_mode = fill_mode_map.get(fill_text, "fit")
            if fill_mode != DEFAULT_VALUES.get("fill_mode", "fit"):
                config["fill_mode"] = fill_mode
        
        # 组件类型特定配置
        if self.component_type == "character":
            self._get_character_config(config)
        elif self.component_type == "background":
            self._get_background_config(config)
        elif self.component_type == "extra":
            self._get_extra_config(config)
        elif self.component_type == "namebox":
            self._get_namebox_config(config)
        elif self.component_type == "text":
            self._get_text_config(config)
        
        # 移除空值
        # config = {k: v for k, v in config.items() if v not in [None, ""]}
        
        return config
    
    def _get_character_config(self, config):
        """获取角色组件配置"""
        # 使用固定角色（默认是False，只保存True）
        if hasattr(self.component_widget, 'checkbox_fixed_emotion'):
            use_fixed = self.component_widget.checkbox_fixed_emotion.isChecked()
            
            # 保存角色名
            if hasattr(self.component_widget, 'combo_character'):
                character_name = self.component_widget.combo_character.currentData()
                if character_name:
                    config["character_name"] = character_name
            
            if use_fixed:
                config["use_fixed_character"] = use_fixed
                # 只有使用固定角色时，才保存表情索引（默认是1，只保存非1的值）
                if hasattr(self.component_widget, 'combo_emotion'):
                    emotion_index = self.component_widget.combo_emotion.currentData()
                    if emotion_index and emotion_index != 1:
                        config["emotion_index"] = emotion_index
    
    def _get_background_config(self, config):
        """获取背景组件配置"""
        # 使用固定背景（默认是False，只保存True）
        if hasattr(self.component_widget, 'checkbox_fixed_background'):
            use_fixed = self.component_widget.checkbox_fixed_background.isChecked()
            if use_fixed:
                config["use_fixed_background"] = use_fixed
        
        # 背景图片
        if hasattr(self.component_widget, 'combo_background'):
            overlay = self.component_widget.combo_background.currentData()
            if overlay and overlay != DEFAULT_VALUES.get("overlay", ""):
                config["overlay"] = overlay
    
    def _get_extra_config(self, config):
        """获取图片组件配置"""
        # 图片
        if hasattr(self.component_widget, 'combo_image'):
            overlay = self.component_widget.combo_image.currentData()
            if overlay and overlay != DEFAULT_VALUES.get("overlay", ""):
                config["overlay"] = overlay
    
    def _get_namebox_config(self, config):
        """获取名字框组件配置"""
        # 图片
        if hasattr(self.component_widget, 'combo_image'):
            overlay = self.component_widget.combo_image.currentData()
            if overlay and overlay != DEFAULT_VALUES.get("overlay", ""):
                config["overlay"] = overlay
    
    def _get_text_config(self, config):
        """获取文本组件配置"""
        # 文本内容 - 如果没有文本内容，文本组件就没有意义，所以不保存空的文本
        if hasattr(self.component_widget, 'edit_text_content'):
            text = self.component_widget.edit_text_content.text().strip()
            if text:
                config["text"] = text
        
        # 字体
        if hasattr(self.component_widget, 'combo_font'):
            font_family = self.component_widget.combo_font.currentText()
            if font_family:  # 确保字体不为空
                config["font_family"] = font_family
        
        # 字号
        if hasattr(self.component_widget, 'edit_text_size'):
            font_size_text = self.component_widget.edit_text_size.text()
            if font_size_text:
                font_size = int(font_size_text)
                config["font_size"] = font_size
        
        # 文本颜色
        if hasattr(self.component_widget, 'edit_text_color'):
            text_color = self.component_widget.edit_text_color.text()
            if text_color:
                config["text_color"] = text_color
        
        # 最大宽度
        if hasattr(self.component_widget, 'edit_line_width'):
            max_width_text = self.component_widget.edit_line_width.text()
            if max_width_text:
                max_width = int(max_width_text)
                config["max_width"] = max_width
        
        # 阴影颜色
        if hasattr(self.component_widget, 'edit_shadow_color'):
            shadow_color = self.component_widget.edit_shadow_color.text()
            if shadow_color:
                config["shadow_color"] = shadow_color
        
        # 阴影偏移
        if hasattr(self.component_widget, 'edit_shadow_x'):
            shadow_x_text = self.component_widget.edit_shadow_x.text()
            if shadow_x_text:
                shadow_x = int(shadow_x_text)
                config["shadow_offset_x"] = shadow_x
        
        if hasattr(self.component_widget, 'edit_shadow_y'):
            shadow_y_text = self.component_widget.edit_shadow_y.text()
            if shadow_y_text:
                shadow_y = int(shadow_y_text)
                config["shadow_offset_y"] = shadow_y
    
    def delete_component(self):
        """删除组件"""
        if self.style_window:
            self.style_window.remove_component(self.index)
        self.deleteLater()
    
    def move_component(self, direction):
        """移动组件位置"""
        if self.style_window:
            self.style_window.move_component(self.index, direction)


class StyleWindow(QDialog):
    """样式编辑窗口"""
    
    style_changed = Signal(str)  # 样式改变信号
    
    def __init__(self, parent=None, core=None, gui=None, current_style=None):
        super().__init__(parent)
        self.parent = parent
        self.core = core
        self.gui = gui
        self.initial_style = current_style  # 记录打开时的样式
        
        # 组件编辑器列表
        self.component_editors = []
        
        # 跟踪组件数量是否变化
        self.original_component_count = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI界面"""
        from ui.style_window import Ui_StyleWindow
        self.ui = Ui_StyleWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("样式编辑")

        # 初始化对齐方式下拉框
        self.init_align_combos()

        # 初始化字体列表
        self.ui.comboBox_textFont.addItems(get_available_fonts())
        
        # 初始化填充模式下拉框
        fill_mode_options = ["适应边界", "适应宽度", "适应高度"]
        self.ui.comboBox_imgFillMode.clear()
        self.ui.comboBox_imgFillMode.addItems(fill_mode_options)
        
        # 加载样式
        self.load_current_style()
        
        # 连接颜色预览
        self.ui.lineEdit_textColor.textChanged.connect(self.update_text_color_preview)
        self.ui.lineEdit_shadowColor.textChanged.connect(self.update_shadow_color_preview)
        self.ui.lineEdit_bracketColor.textChanged.connect(self.update_bracket_color_preview)
        
        # 连接使用角色颜色复选框
        self.ui.checkBox_useCharaColor.toggled.connect(self.on_use_character_color_changed)
        
        # 连接必要的信号槽
        self.ui.comboBox_style.currentIndexChanged.connect(self.on_style_changed)
        self.ui.buttonBox.clicked.connect(self.on_button_clicked)
        
        # 初始化组件编辑区域
        self.init_component_editors()
        # 记录初始组件数量
        self.original_component_count = len(self.component_editors)
        
        # 连接组件添加按钮
        self.ui.toolButton.clicked.connect(self.show_add_component_menu)
        self.ui.pushButton_2.clicked.connect(self.reset_components)
        
        # 连接预览区域按钮
        self.ui.pushButton_previewTextArea.clicked.connect(lambda: self.preview_area("text"))
        self.ui.pushButton_previewImgArea.clicked.connect(lambda: self.preview_area("image"))
        
        # 设置初始大小
        self.resize(650, 750)

    def preview_area(self, area_type):
        """预览区域按钮点击事件"""
        if not self.gui:
            return
        
        try:
            if area_type == "text":
                x = int(self.ui.lineEdit_textX.text() or 760)
                y = int(self.ui.lineEdit_textY.text() or 355)
                width = int(self.ui.lineEdit_textW.text() or 1579)
                height = int(self.ui.lineEdit_textH.text() or 445)
            elif area_type == "image":
                x = int(self.ui.lineEdit_imgX.text() or 0)
                y = int(self.ui.lineEdit_imgY.text() or 0)
                width = int(self.ui.lineEdit_imgW.text() or 300)
                height = int(self.ui.lineEdit_imgH.text() or 200)
            else:
                return
            
            self.gui.highlight_preview_rect(x, y, width, height, area_type)
        except Exception as e:
            print(f"预览区域失败: {e}")
            
    def on_use_character_color_changed(self, checked):
        """使用角色颜色复选框状态改变"""
        self.ui.lineEdit_bracketColor.setEnabled(not checked)
        if checked:
            self.update_bracket_color_from_character()
        self.update_bracket_color_preview()

    def update_bracket_color_from_character(self):
        """根据当前角色的文本颜色更新强调色"""
        character_name = CONFIGS._get_current_character_from_layers()
        if character_name in CONFIGS.character_list and CONFIGS.mahoshojo[character_name]["text"]:
            first_config = CONFIGS.mahoshojo[character_name]["text"][0]
            font_color = first_config.get("font_color", (255, 255, 255))
            color_hex = f"#{font_color[0]:02x}{font_color[1]:02x}{font_color[2]:02x}"
            self.ui.lineEdit_bracketColor.setText(color_hex)

    def init_align_combos(self):
        """初始化对齐方式下拉框"""
        align_options = list(ALIGN_MAPPING.keys())
        self.ui.comboBox_align.clear()
        self.ui.comboBox_align.addItems(align_options)
        
        self.ui.comboBox_imgAlign.clear()
        self.ui.comboBox_imgAlign.addItems(align_options)
        
        for editor in self.component_editors:
            if hasattr(editor.component_widget, 'combo_align'):
                editor.component_widget.combo_align.clear()
                editor.component_widget.combo_align.addItems(align_options)
        
    def init_component_editors(self):
        """初始化组件编辑器"""
        # 清空现有编辑器
        for editor in self.component_editors:
            editor.deleteLater()
        self.component_editors.clear()
        
        # 获取当前样式的组件
        current_style_name = self.ui.comboBox_style.currentText()
        if current_style_name in CONFIGS.style_configs:
            current_components = CONFIGS.style_configs[current_style_name].get("image_components", [])
        else:
            current_components = []
        
        # 按图层排序（从小到大）
        current_components.sort(key=lambda x: x.get("layer", 0))
        
        # 添加组件编辑器 - 反转顺序，图层号大的在顶部（先添加）
        for i, component in enumerate(reversed(current_components)):
            editor = ComponentEditor(self.ui.scrollAreaWidgetContents, self, component, i)
            self.ui.verticalLayout_6.insertWidget(self.ui.verticalLayout_6.count() - 1, editor)
            self.component_editors.append(editor)
        
    def show_add_component_menu(self):
        """显示添加组件菜单"""
        menu = QMenu(self)
        
        for comp_type, comp_name in COMPONENT_TYPES.items():
            action = menu.addAction(comp_name)
            action.triggered.connect(lambda checked, ct=comp_type: self.add_component(ct))
        
        pos = self.ui.toolButton.mapToGlobal(self.ui.toolButton.rect().bottomLeft())
        menu.exec(pos)

    def add_component(self, component_type):
        """添加新组件"""
        # 计算新的图层值（应该是最高的图层号+1）
        max_layer = 0
        for editor in self.component_editors:
            config = editor.get_current_config()
            layer = config.get("layer", 0)
            max_layer = max(max_layer, layer)
        
        # 创建默认配置 - 新组件应该在顶部
        component_config = {
            "type": component_type,
            "layer": max_layer + 1,  # 新组件在顶部，图层号最大
            "enabled": True,
        }
        
        # 创建编辑器
        editor = ComponentEditor(self.ui.scrollAreaWidgetContents, self, component_config, 0)
        
        # 插入到组件编辑器列表开头（这样在UI更新时会显示在最上面）
        self.component_editors.insert(0, editor)
        
        # 更新所有编辑器的索引
        for i, ed in enumerate(self.component_editors):
            ed.index = i
        
        # 重新构建UI顺序（这会按照self.component_editors的顺序重新排列）
        self.update_component_order()

        self._components_changed = True
        
    def remove_component(self, index):
        """删除组件"""
        if 0 <= index < len(self.component_editors):
            editor = self.component_editors.pop(index)
            editor.deleteLater()
            
            # 更新剩余编辑器的索引
            for i, ed in enumerate(self.component_editors):
                ed.index = i
                
            self.update_component_order()
            
            # 标记组件数量已变化
            self._components_changed = True
    
    def move_component(self, index, direction):
        """移动组件位置"""
        length = len(self.component_editors)
        new_index = index + direction
        if 0 <= new_index < length:
            
            self.component_editors[index], self.component_editors[new_index] = self.component_editors[new_index], self.component_editors[index]
            
            # 重新计算并更新所有组件的图层号
            for i, editor in enumerate(self.component_editors):
                # 更新编辑器索引
                editor.index = i
                
                layer = length - 1 - i
                editor.component_config["layer"] = layer
                
                # 更新组件标题
                comp_type_name = COMPONENT_TYPES.get(editor.component_type, editor.component_type)
                editor.setTitle(f"{comp_type_name}组件 (图层: {layer})")
            
            # 更新UI顺序
            self.update_component_order()

            # 标记组件已重新排序
            self._components_reordered = True
    
    def update_component_order(self):
        """更新组件在UI中的顺序"""
        layout = self.ui.verticalLayout_6
        
        # 移除所有组件（除了最后的spacer）
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item and item.widget() and item.widget() != self.ui.verticalSpacer:
                layout.removeItem(item)
        
        # 重新添加所有组件
        for editor in self.component_editors:
            layout.insertWidget(layout.count() - 1, editor)
        
        # 添加最后的spacer
        if layout.indexOf(self.ui.verticalSpacer) == -1:
            layout.addItem(self.ui.verticalSpacer)
    
    def reset_components(self):
        """重置组件"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有组件到默认配置吗？\n这将覆盖当前所有组件设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            current_style_name = self.ui.comboBox_style.currentText()
            default_components = CONFIGS.style.default_config.get(current_style_name, {}).get("image_components", [])
            CONFIGS.style_configs[current_style_name]["image_components"] = default_components
            if default_components:
                self.init_component_editors()
                clear_cache()
                
                if self.gui:
                    self.gui.update_status(f"已重置样式 '{current_style_name}' 的组件到默认配置")
            else:
                QMessageBox.warning(self, "警告", f"默认配置中没有找到样式 '{current_style_name}' 的组件设置")
    
    def load_current_style(self):
        """加载当前样式到UI"""
        # 获取可用样式
        available_styles = list(CONFIGS.style_configs.keys())
        self.ui.comboBox_style.clear()
        self.ui.comboBox_style.addItems(available_styles)
        
        # 设置当前样式
        if self.initial_style:
            current_style = self.initial_style
        else:
            current_style = CONFIGS.current_style
            
        index = self.ui.comboBox_style.findText(current_style)
        if index >= 0:
            self.ui.comboBox_style.setCurrentIndex(index)
        elif available_styles:
            self.ui.comboBox_style.setCurrentIndex(0)
            current_style = available_styles[0]
        
        # 加载样式数据
        self.load_style_data()
        
    def load_style_data(self):
        """加载样式数据到UI"""
        style = CONFIGS.style
        
        # 图片比例
        aspect_ratio = getattr(style, "aspect_ratio", "3:1")
        if aspect_ratio == "3:1":
            self.ui.radioButton_1.setChecked(True)
        elif aspect_ratio == "5:4":
            self.ui.radioButton_2.setChecked(True)
        elif aspect_ratio == "16:9":
            self.ui.radioButton_3.setChecked(True)
        
        # 文本设置
        self.ui.lineEdit_textX.setText(str(getattr(style, "textbox_x", 760)))
        self.ui.lineEdit_textY.setText(str(getattr(style, "textbox_y", 355)))
        self.ui.lineEdit_textW.setText(str(getattr(style, "textbox_width", 1579)))
        self.ui.lineEdit_textH.setText(str(getattr(style, "textbox_height", 445)))
        
        # 文本对齐方式
        text_align_str = getattr(style, "text_align", "top-left")
        if text_align_str in REVERSE_ALIGN_MAPPING:
            self.ui.comboBox_align.setCurrentText(REVERSE_ALIGN_MAPPING[text_align_str])
        else:
            self.ui.comboBox_align.setCurrentText("左上")
        
        # 字体
        font_family = getattr(style, "font_family", "font3")
        index = self.ui.comboBox_textFont.findText(font_family)
        if index >= 0:
            self.ui.comboBox_textFont.setCurrentIndex(index)
        
        self.ui.lineEdit_fontSize.setText(str(getattr(style, "font_size", 90)))
        self.ui.lineEdit_textColor.setText(getattr(style, "text_color", "#FFFFFF"))
        self.ui.lineEdit_shadowColor.setText(getattr(style, "shadow_color", "#000000"))
        self.ui.lineEdit_shadowX.setText(str(getattr(style, "shadow_offset_x", 4)))
        self.ui.lineEdit_shadowY.setText(str(getattr(style, "shadow_offset_y", 4)))
        
        # 强调色
        use_character_color = getattr(style, "use_character_color", False)
        self.ui.checkBox_useCharaColor.setChecked(use_character_color)
        self.ui.lineEdit_bracketColor.setText(getattr(style, "bracket_color", "#EF4F54"))
        self.ui.lineEdit_bracketColor.setEnabled(not use_character_color)
        
        # 粘贴图像设置
        paste_settings = getattr(style, "paste_image_settings", {})
        enabled = paste_settings.get("enabled", "off")
        if enabled == "always":
            self.ui.radioButton_alway.setChecked(True)
        elif enabled == "mixed":
            self.ui.radioButton_mixed.setChecked(True)
        else:
            self.ui.radioButton_off.setChecked(True)
        
        self.ui.lineEdit_imgX.setText(str(paste_settings.get("x", 0)))
        self.ui.lineEdit_imgY.setText(str(paste_settings.get("y", 0)))
        self.ui.lineEdit_imgW.setText(str(paste_settings.get("width", 300)))
        self.ui.lineEdit_imgH.setText(str(paste_settings.get("height", 200)))
        
        # 粘贴图像对齐方式
        align_str = paste_settings.get("align", "middle-center")
        if align_str in REVERSE_ALIGN_MAPPING:
            self.ui.comboBox_imgAlign.setCurrentText(REVERSE_ALIGN_MAPPING[align_str])
        else:
            self.ui.comboBox_imgAlign.setCurrentText("居中")
        
        # 粘贴图像填充方式
        fill_mode = paste_settings.get("fill_mode", "fit")
        fill_mode_map = {"fit": "适应边界", "width": "适应宽度", "height": "适应高度"}
        if fill_mode in fill_mode_map:
            self.ui.comboBox_imgFillMode.setCurrentText(fill_mode_map[fill_mode])
        else:
            self.ui.comboBox_imgFillMode.setCurrentText("适应边界")
        
        # 更新颜色预览
        self.update_text_color_preview()
        self.update_shadow_color_preview()
        self.update_bracket_color_preview()
    
    def collect_style_data(self):
        """收集样式数据 - 常规设置全部保存"""
        style_data = {}
        
        # 图片比例 - 全部保存
        if self.ui.radioButton_1.isChecked():
            style_data["aspect_ratio"] = "3:1"
        elif self.ui.radioButton_2.isChecked():
            style_data["aspect_ratio"] = "5:4"
        elif self.ui.radioButton_3.isChecked():
            style_data["aspect_ratio"] = "16:9"
        
        # 文本设置 - 全部保存
        style_data["textbox_x"] = int(self.ui.lineEdit_textX.text() or 760)
        style_data["textbox_y"] = int(self.ui.lineEdit_textY.text() or 355)
        style_data["textbox_width"] = int(self.ui.lineEdit_textW.text() or 1579)
        style_data["textbox_height"] = int(self.ui.lineEdit_textH.text() or 445)
        
        # 文本对齐方式
        align_text = self.ui.comboBox_align.currentText()
        if align_text in ALIGN_MAPPING:
            style_data["text_align"] = ALIGN_MAPPING[align_text]
        else:
            style_data["text_align"] = "top-left"
        
        # 字体设置 - 全部保存
        style_data["font_family"] = self.ui.comboBox_textFont.currentText()
        style_data["font_size"] = int(self.ui.lineEdit_fontSize.text() or 90)
        style_data["text_color"] = self.ui.lineEdit_textColor.text()
        style_data["shadow_color"] = self.ui.lineEdit_shadowColor.text()
        style_data["shadow_offset_x"] = int(self.ui.lineEdit_shadowX.text() or 4)
        style_data["shadow_offset_y"] = int(self.ui.lineEdit_shadowY.text() or 4)
        
        # 强调色 - 全部保存
        style_data["use_character_color"] = self.ui.checkBox_useCharaColor.isChecked()
        if not style_data["use_character_color"]:
            style_data["bracket_color"] = self.ui.lineEdit_bracketColor.text()
        
        # 粘贴图像设置 - 全部保存
        paste_settings = {}
        if self.ui.radioButton_alway.isChecked():
            paste_settings["enabled"] = "always"
        elif self.ui.radioButton_mixed.isChecked():
            paste_settings["enabled"] = "mixed"
        else:
            paste_settings["enabled"] = "off"
        
        paste_settings["x"] = int(self.ui.lineEdit_imgX.text() or 0)
        paste_settings["y"] = int(self.ui.lineEdit_imgY.text() or 0)
        paste_settings["width"] = int(self.ui.lineEdit_imgW.text() or 300)
        paste_settings["height"] = int(self.ui.lineEdit_imgH.text() or 200)
        
        # 粘贴图像对齐方式
        align_name = self.ui.comboBox_imgAlign.currentText()
        if align_name in ALIGN_MAPPING:
            paste_settings["align"] = ALIGN_MAPPING[align_name]
        else:
            paste_settings["align"] = "middle-center"
        
        # 粘贴图像填充方式
        fill_text = self.ui.comboBox_imgFillMode.currentText()
        fill_mode_map = {"适应边界": "fit", "适应宽度": "width", "适应高度": "height"}
        paste_settings["fill_mode"] = fill_mode_map.get(fill_text, "fit")
        
        style_data["paste_image_settings"] = paste_settings
        
        # 收集组件数据（组件配置会移除默认值）
        image_components = self.collect_components()
        if image_components:
            style_data["image_components"] = image_components
        
        return style_data

    def collect_components(self):
        """收集组件数据"""
        image_components = []
        for editor in reversed(self.component_editors):
            component_config = editor.get_current_config()
            if component_config:
                image_components.append(component_config)
        
        # 按图层排序
        image_components.sort(key=lambda x: x.get("layer", 0))
        return image_components
    
    def validate_style_data(self, style_data):
        """验证样式数据"""
        errors = []
        
        import re
        color_pattern = r'^#([A-Fa-f0-9]{6})$'
        
        # 验证颜色格式
        text_color = style_data.get("text_color", "")
        if text_color and not re.match(color_pattern, text_color):
            errors.append("文本颜色格式无效")
        
        shadow_color = style_data.get("shadow_color", "")
        if shadow_color and not re.match(color_pattern, shadow_color):
            errors.append("阴影颜色格式无效")
        
        bracket_color = style_data.get("bracket_color", "")
        if bracket_color and not re.match(color_pattern, bracket_color):
            errors.append("强调颜色格式无效")
        
        # 验证字体大小
        font_size = style_data.get("font_size", 90)
        if not 8 <= font_size <= 250:
            errors.append("字体大小必须在8到250之间")
        
        # 检查背景组件数量
        image_components = style_data.get("image_components", [])
        background_components = [comp for comp in image_components 
                               if comp.get("type") == "background" and comp.get("enabled", True)]
        
        if len(background_components) == 0:
            errors.append("必须至少有一个启用的背景组件")
        elif len(background_components) > 1:
            errors.append("只能有一个启用的背景组件")
        
        return errors
    
    def update_text_color_preview(self):
        """更新文本颜色预览"""
        color = self.ui.lineEdit_textColor.text()
        import re
        pattern = r'^#([A-Fa-f0-9]{6})$'
        if re.match(pattern, color):
            self.ui.label_textColorPreview.setStyleSheet(f"background-color: {color}; border: 1px solid #000;")
        else:
            self.ui.label_textColorPreview.setStyleSheet("background-color: #FF0000; border: 1px solid #000;")
    
    def update_shadow_color_preview(self):
        """更新阴影颜色预览"""
        color = self.ui.lineEdit_shadowColor.text()
        import re
        pattern = r'^#([A-Fa-f0-9]{6})$'
        if re.match(pattern, color):
            self.ui.label_shadowColorPreview.setStyleSheet(f"background-color: {color}; border: 1px solid #000;")
        else:
            self.ui.label_shadowColorPreview.setStyleSheet("background-color: #FF0000; border: 1px solid #000;")
    
    def update_bracket_color_preview(self):
        """更新强调颜色预览"""
        color = self.ui.lineEdit_bracketColor.text()
        import re
        pattern = r'^#([A-Fa-f0-9]{6})$'
        if re.match(pattern, color):
            self.ui.label_bracketColorPreview.setStyleSheet(f"background-color: {color}; border: 1px solid #000;")
        else:
            self.ui.label_bracketColorPreview.setStyleSheet("background-color: #FF0000; border: 1px solid #000;")
    
    @Slot()
    def on_style_changed(self):
        """样式改变"""
        style_name = self.ui.comboBox_style.currentText()
        
        print(f"切换到样式: {style_name}")
        
        CONFIGS.apply_style(style_name)
        self.load_style_data()
        self.init_component_editors()
        
        # 发送样式改变信号到主窗口
        if self.gui:
            self.style_changed.emit(style_name)
            self.gui.update_preview()
            self.gui.update_status(f"已切换到样式: {style_name}")
    
    @Slot(object)
    def on_button_clicked(self, button):
        """按钮点击事件"""
        role = self.ui.buttonBox.standardButton(button)

        if role == self.ui.buttonBox.StandardButton.Save:
            if self.save_current_style():
                self.accept()
        elif role == self.ui.buttonBox.StandardButton.Apply:
            self.save_current_style()
        elif role == self.ui.buttonBox.StandardButton.Cancel:
            self.reject()
    
    def save_current_style(self):
        """保存当前样式"""
        style_name = self.ui.comboBox_style.currentText()
        style_data = self.collect_style_data()

        # 验证数据
        errors = self.validate_style_data(style_data)
        if errors:
            QMessageBox.critical(self, "错误", "\n".join(errors))
            return False
        
        # 检查是否需要重新初始化主窗口的标签页
        needs_reinit = False
        
        # 检查组件数量是否变化
        current_count = len(self.collect_components())
        if current_count != self.original_component_count:
            needs_reinit = True
            print(f"组件数量变化: {self.original_component_count} -> {current_count}")
            self.original_component_count = current_count
        
        # 检查是否有角色或背景组件被添加/删除
        if not needs_reinit:
            current_components = self.collect_components()
            original_style = CONFIGS.style_configs.get(style_name, {})
            original_components = original_style.get("image_components", [])
            
            # 检查角色组件
            current_chars = [c for c in current_components if c.get("type") == "character"]
            original_chars = [c for c in original_components if c.get("type") == "character"]
            if len(current_chars) != len(original_chars):
                needs_reinit = True
            
            # 检查背景组件
            current_bgs = [c for c in current_components if c.get("type") == "background"]
            original_bgs = [c for c in original_components if c.get("type") == "background"]
            if len(current_bgs) != len(original_bgs):
                needs_reinit = True
        
        # 更新样式配置，直接依赖 update_style 的返回值
        success = CONFIGS.update_style(style_name, style_data)
        
        if success:
            if self.gui:
                clear_cache()
                self.style_changed.emit(style_name)
                
                # 如果需要重新初始化，更新预览
                if needs_reinit:
                    self.gui.update_status(f"样式已保存: {style_name} (组件已更新)")
                else:
                    self.gui.update_status(f"样式已保存: {style_name}")
                    self.gui.update_preview()
        return True
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果样式有改变但未保存，提示用户
        style_name = self.ui.comboBox_style.currentText()
        style_data = self.collect_style_data()
        original_data = CONFIGS.style_configs.get(style_name, {})
        
        # 简单比较
        if style_data != original_data:
            reply = QMessageBox.question(
                self, "确认关闭",
                "样式已修改但未保存，确定要关闭吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # 通知主窗口恢复控件
        if self.gui:
            try:
                QMetaObject.invokeMethod(self.gui, "_closed_style_window", 
                                        Qt.ConnectionType.QueuedConnection)
            except Exception as e:
                print(f"恢复主窗口控件时出错: {e}")
        
        # 接受关闭事件
        event.accept()