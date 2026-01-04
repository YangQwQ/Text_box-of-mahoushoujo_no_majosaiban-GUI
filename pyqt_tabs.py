# -*- coding: utf-8 -*-
"""标签页管理模块"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QLabel, QComboBox, QCheckBox, QLineEdit
from PySide6.QtCore import Signal, Qt
from ui_pyqt_components import Ui_CharacterComponent, Ui_BackgroundComponent
from config import CONFIGS
import os
from path_utils import get_resource_path
from image_processor import clear_cache

class BackgroundTabWidget(QWidget):
    """背景标签页组件 - 使用UI设计器中的布局"""
    
    config_changed = Signal()
    
    def __init__(self, parent=None, component_config=None, layer_index=0, ui_controls=None):
        super().__init__(parent)
        
        # 存储组件配置的引用
        self.layer_index = layer_index
        self._updating_ui = False  # 添加标志，防止递归触发
        self._ignore_signals = False  # 添加忽略信号标志
        
        # 使用UI设计器中的控件
        self.checkBox_randomBg = ui_controls.get('checkBox_randomBg')
        self.comboBox_bgSelect = ui_controls.get('comboBox_bgSelect')
        self.lineEdit_bgColor = ui_controls.get('lineEdit_bgColor')
        self.widget_bgColorPreview = ui_controls.get('widget_bgColorPreview')
        
        # 加载背景图片列表
        self._load_background_files()
        
        # 连接信号槽
        self._connect_signals()
        
        # 初始化UI从配置
        self._init_from_config()
    
    def get_component_config(self):
        """获取当前图层的组件配置"""
        if not CONFIGS.preview_style or 'image_components' not in CONFIGS.preview_style:
            return None
        
        for component in CONFIGS.preview_style['image_components']:
            if component.get("layer") == self.layer_index:
                return component
        return None
    
    def _load_background_files(self):
        """加载背景图片文件列表"""
        try:
            background_dir = get_resource_path(os.path.join("assets", "background"))
            if os.path.exists(background_dir):
                bg_files = [f for f in os.listdir(background_dir) if f.lower().startswith('c')]
                self.comboBox_bgSelect.addItem("无", "")
                for bg_file in sorted(bg_files):
                    self.comboBox_bgSelect.addItem(bg_file, bg_file)
        except Exception as e:
            print(f"获取背景文件失败: {e}")
    
    def _init_from_config(self):
        """从配置初始化UI"""
        component_config = self.get_component_config()
        if not component_config:
            return
        
        # 设置标志，避免信号触发更新
        self._ignore_signals = True
        
        try:
            # 设置是否使用固定背景
            use_fixed_bg = component_config.get("use_fixed_background", False)
            
            # 先设置所有控件的启用状态
            if not use_fixed_bg:
                self.checkBox_randomBg.setChecked(True)
                self.comboBox_bgSelect.setEnabled(False)
                if self.lineEdit_bgColor:
                    self.lineEdit_bgColor.setEnabled(False)
            else:
                self.checkBox_randomBg.setChecked(False)
                self.comboBox_bgSelect.setEnabled(True)
                if self.lineEdit_bgColor:
                    self.lineEdit_bgColor.setEnabled(True)
            
            # 然后设置控件内容
            overlay = component_config.get("overlay", "")
            if overlay:
                if overlay.startswith("#"):
                    # 颜色 - 选择"无"，并在颜色输入框显示颜色
                    index = self.comboBox_bgSelect.findData("")
                    if index >= 0:
                        self.comboBox_bgSelect.setCurrentIndex(index)  # 选择"无"
                    if self.lineEdit_bgColor:
                        self.lineEdit_bgColor.setText(overlay)
                        self._update_color_preview(overlay)
                else:
                    # 图片 - 选择对应的图片
                    index = self.comboBox_bgSelect.findData(overlay)
                    if index >= 0:
                        self.comboBox_bgSelect.setCurrentIndex(index)
                    # 如果选择了图片，清空颜色输入和预览
                    if self.lineEdit_bgColor:
                        self.lineEdit_bgColor.clear()
                        if self.widget_bgColorPreview:
                            self.widget_bgColorPreview.setStyleSheet("")
            else:
                # 没有指定overlay，选择"无"，清空颜色输入
                index = self.comboBox_bgSelect.findData("")
                if index >= 0:
                    self.comboBox_bgSelect.setCurrentIndex(index)
                if self.lineEdit_bgColor:
                    self.lineEdit_bgColor.clear()
                    if self.widget_bgColorPreview:
                        self.widget_bgColorPreview.setStyleSheet("")
        finally:
            # 恢复信号处理
            self._ignore_signals = False

    def _connect_signals(self):
        """连接信号槽"""
        self.checkBox_randomBg.toggled.connect(self.on_random_bg_changed)
        self.comboBox_bgSelect.currentIndexChanged.connect(self.on_bg_selected)
        if self.lineEdit_bgColor:
            self.lineEdit_bgColor.textChanged.connect(self.on_color_changed)
    
    def _update_color_preview(self, color):
        """更新颜色预览"""
        if color and color.startswith("#") and len(color) == 7:
            if self.widget_bgColorPreview:
                # QWidget作为预览
                self.widget_bgColorPreview.setStyleSheet(f"background-color: {color}; border: 1px solid gray;")
    
    def on_random_bg_changed(self, checked):
        """随机背景选择改变"""
        if self._ignore_signals:
            return
            
        # 只改变控件的启用状态，不清除内容
        self.comboBox_bgSelect.setEnabled(not checked)
        if self.lineEdit_bgColor:
            self.lineEdit_bgColor.setEnabled(not checked)
        
        # 更新配置
        updates = {
            "use_fixed_background": not checked
        }
        
        if checked:
            # 使用随机背景
            updates["overlay"] = ""  # 清空overlay表示使用随机
        else:
            # 使用固定背景，根据当前选择的选项设置overlay
            if self.comboBox_bgSelect.currentIndex() > 0:
                # 选择了图片
                bg_file = self.comboBox_bgSelect.currentData()
                updates["overlay"] = bg_file
            elif self.lineEdit_bgColor and self.lineEdit_bgColor.text():
                # 输入了颜色
                color = self.lineEdit_bgColor.text()
                if color.startswith("#") and len(color) == 7:
                    updates["overlay"] = color
                    # 更新颜色预览
                    self._update_color_preview(color)
                else:
                    # 无效颜色，清空overlay
                    updates["overlay"] = ""
            else:
                # 既没有选择图片也没有输入颜色，使用空字符串
                updates["overlay"] = ""
        
        # 更新预览样式
        CONFIGS.update_preview_component(self.layer_index, updates)
        self.config_changed.emit()
    
    def on_bg_selected(self, index):
        """背景选择改变"""
        if self._ignore_signals or self._updating_ui:
            return
            
        # 设置标志，防止递归
        self._updating_ui = True
        
        try:
            # 只有在不使用随机背景时才更新配置
            if not self.checkBox_randomBg.isChecked():
                updates = {}
                
                if index > 0:  # 选择了图片
                    bg_file = self.comboBox_bgSelect.currentData()
                    updates["overlay"] = bg_file
                    updates["use_fixed_background"] = True
                    
                    # 清除颜色输入和预览
                    if self.lineEdit_bgColor:
                        self.lineEdit_bgColor.clear()
                        if self.widget_bgColorPreview:
                            self.widget_bgColorPreview.setStyleSheet("")
                elif index == 0:  # 选择了"无"
                    # 如果颜色输入框有内容，使用颜色
                    if self.lineEdit_bgColor and self.lineEdit_bgColor.text():
                        color = self.lineEdit_bgColor.text()
                        if color.startswith("#") and len(color) == 7:
                            updates["overlay"] = color
                            updates["use_fixed_background"] = True
                            self._update_color_preview(color)
                    else:
                        # 没有选择图片也没有输入颜色，清空overlay
                        updates["overlay"] = ""
                        updates["use_fixed_background"] = True
                clear_cache()

                if updates:
                    CONFIGS.update_preview_component(self.layer_index, updates)
                    self.config_changed.emit()
        finally:
            self._updating_ui = False

    def on_color_changed(self, text):
        """颜色输入改变"""
        if self._ignore_signals or self._updating_ui:
            return
            
        self._updating_ui = True
        
        try:
            # 只有在不使用随机背景时才更新配置
            if not self.checkBox_randomBg.isChecked():
                if text:
                    if text.startswith("#") and len(text) == 7:
                        self._update_color_preview(text)
                        
                        updates = {
                            "overlay": text,
                            "use_fixed_background": True
                        }
                        
                        # 更新预览样式
                        CONFIGS.update_preview_component(self.layer_index, updates)
                        
                        # 清除背景图片选择
                        self.comboBox_bgSelect.setCurrentIndex(0)
                        
                        self.config_changed.emit()
                        
                        clear_cache()
                    elif not text.startswith("#"):
                        # 颜色无效，清空预览
                        if self.widget_bgColorPreview:
                            self.widget_bgColorPreview.setStyleSheet("")
                else:
                    # 颜色被清空，清空overlay和预览
                    updates = {
                        "overlay": "",
                        "use_fixed_background": True
                    }
                    CONFIGS.update_preview_component(self.layer_index, updates)
                    self.config_changed.emit()
                    if self.widget_bgColorPreview:
                        self.widget_bgColorPreview.setStyleSheet("")
                    clear_cache()
        finally:
            self._updating_ui = False

class CharacterTabWidget(QWidget):
    """角色标签页组件，直接使用UI模板"""

    config_changed = Signal()
    
    def __init__(self, parent=None, component_config=None, layer_index=1):
        super().__init__(parent)
        
        # 存储组件配置的引用
        self.layer_index = layer_index
        self.current_character_id = None
        self._ignore_signals = False  # 添加忽略信号标志
        self._updating_ui = False  # 添加UI更新标志
        
        # 使用UI模板
        self.ui = Ui_CharacterComponent()
        self.ui.setupUi(self)
        
        # 隐藏暂时不需要的控件
        self.ui.label_poiseSelect.hide()
        self.ui.label_posSelect.hide()
        self.ui.comboBox_poiseSelect.hide()
        self.ui.comboBox_posSelect.hide()

        # 初始化表情筛选下拉框
        self._init_emotion_filter_combo()
        
        # 初始化UI从配置
        self._init_from_config()
        
        # 连接信号槽
        self._connect_signals()
        
    def get_component_config(self):
        """获取当前图层的组件配置"""
        if not CONFIGS.preview_style or 'image_components' not in CONFIGS.preview_style:
            return None
        
        for component in CONFIGS.preview_style['image_components']:
            if component.get("layer") == self.layer_index:
                return component
        return None
    
    def _init_emotion_filter_combo(self):
        """初始化表情筛选下拉框"""
        # 获取情感列表
        emotion_filters = ["全部"] + CONFIGS.emotion_list
        self.ui.comboBox_emotionFilter.clear()
        self.ui.comboBox_emotionFilter.addItems(emotion_filters)
    
    def _init_from_config(self):
        """从配置初始化UI"""
        component_config = self.get_component_config()
        if not component_config:
            return
        
        # 设置标志，避免信号触发更新
        self._ignore_signals = True
        
        try:
            # 初始化角色下拉框
            self._init_character_combo()
            
            # 设置角色选择
            if "character_name" in component_config:
                char_id = component_config["character_name"]
                self.current_character_id = char_id
                current_text = f"{CONFIGS.get_character(char_id, full_name=True)} ({char_id})"
                index = self.ui.comboBox_charaSelect.findText(current_text)
                if index >= 0:
                    self.ui.comboBox_charaSelect.setCurrentIndex(index)
                else:
                    # 如果找不到，默认选择第一个
                    if self.ui.comboBox_charaSelect.count() > 0:
                        self.ui.comboBox_charaSelect.setCurrentIndex(0)
            else:
                # 如果没有设置角色，使用当前角色
                current_character = CONFIGS.current_character
                self.current_character_id = current_character
                current_text = f"{CONFIGS.get_character(current_character, full_name=True)} ({current_character})"
                index = self.ui.comboBox_charaSelect.findText(current_text)
                if index >= 0:
                    self.ui.comboBox_charaSelect.setCurrentIndex(index)
                elif self.ui.comboBox_charaSelect.count() > 0:
                    self.ui.comboBox_charaSelect.setCurrentIndex(0)
            
            # 初始化表情下拉框（默认显示全部）
            self._init_emotion_combo()
            
            # 设置是否使用固定表情
            use_fixed_character = component_config.get("use_fixed_character", False)
            emotion_index = component_config.get("emotion_index")
            
            # 设置随机表情状态
            if not use_fixed_character or emotion_index is None:
                self.ui.checkBox_randomEmotion.setChecked(True)
                self.ui.comboBox_emotionSelect.setEnabled(False)
            else:
                self.ui.checkBox_randomEmotion.setChecked(False)
                self.ui.comboBox_emotionSelect.setEnabled(True)
                # 设置选中的表情索引
                if emotion_index:
                    # 获取当前过滤条件下的表情列表
                    filter_name = self.ui.comboBox_emotionFilter.currentText()
                    filtered_emotions = CONFIGS.get_filtered_emotions(self.current_character_id, filter_name)
                    if emotion_index in filtered_emotions:
                        idx = filtered_emotions.index(emotion_index)
                        if 0 <= idx < self.ui.comboBox_emotionSelect.count():
                            self.ui.comboBox_emotionSelect.setCurrentIndex(idx)
        finally:
            # 恢复信号处理
            self._ignore_signals = False
    
    def _init_character_combo(self):
        """初始化角色选择下拉框"""
        character_names = []
        for char_id in CONFIGS.character_list:
            full_name = CONFIGS.get_character(char_id, full_name=True)
            character_names.append(f"{full_name} ({char_id})")
        
        self.ui.comboBox_charaSelect.clear()
        self.ui.comboBox_charaSelect.addItems(character_names)
    
    def _init_emotion_combo(self, filter_name="全部"):
        """初始化表情下拉框，可按照筛选条件过滤"""
        # 获取当前角色
        current_char = self.current_character_id
        if not current_char:
            current_char = CONFIGS.get_character()
        
        # 获取筛选后的表情索引
        filtered_emotions = CONFIGS.get_filtered_emotions(current_char, filter_name)
        
        # 创建表情列表
        emotions = [f"表情 {i}" for i in filtered_emotions]
        
        self.ui.comboBox_emotionSelect.clear()
        if emotions:
            self.ui.comboBox_emotionSelect.addItems(emotions)
        else:
            self.ui.comboBox_emotionSelect.addItem("无可用表情")
        
        # 根据是否勾选随机表情设置启用状态
        if self.ui.checkBox_randomEmotion.isChecked():
            self.ui.comboBox_emotionSelect.setEnabled(False)
        else:
            self.ui.comboBox_emotionSelect.setEnabled(bool(emotions))
    
    def _connect_signals(self):
        """连接信号槽"""
        self.ui.comboBox_charaSelect.currentIndexChanged.connect(self.on_character_changed)
        self.ui.checkBox_randomEmotion.toggled.connect(self.on_emotion_random_changed)
        self.ui.comboBox_emotionSelect.currentIndexChanged.connect(self.on_emotion_changed)
        self.ui.comboBox_emotionFilter.currentIndexChanged.connect(self.on_emotion_filter_changed)
    
    def _update_namebox_config(self, character_name):
        """更新namebox组件的文本配置"""
        # 找到namebox组件并更新
        if not CONFIGS.preview_style or 'image_components' not in CONFIGS.preview_style:
            return
            
        for component in CONFIGS.preview_style['image_components']:
            if component.get("type") == "namebox" and component.get("enabled", True):
                if character_name in CONFIGS.text_configs_dict:
                    component["textcfg"] = CONFIGS.text_configs_dict[character_name]
                    component["font_name"] = "font3"
                    print(f"已更新namebox配置为角色: {character_name}")
                break
    
    def on_character_changed(self, index):
        """角色改变事件"""
        if index < 0 or self._ignore_signals:
            return
        
        clear_cache()
        
        selected_text = self.ui.comboBox_charaSelect.currentText()
        if "(" in selected_text and ")" in selected_text:
            char_id = selected_text.split("(")[-1].rstrip(")")
            self.current_character_id = char_id
            
            # 更新预览样式中的组件配置
            CONFIGS.update_preview_component(self.layer_index, {
                "character_name": char_id,
            })
            
            # 更新当前角色变量（如果是第一个角色图层或非固定角色图层）
            if self.layer_index == 1 or not self.get_component_config().get("use_fixed_character", False):
                CONFIGS.current_character = char_id
            
            # 更新namebox配置
            self._update_namebox_config(char_id)
            
            # 更新表情下拉框
            self._init_emotion_combo()
            
            # 发出配置改变信号
            self.config_changed.emit()
    
    def on_emotion_random_changed(self, checked):
        """表情随机选择改变"""
        if self._ignore_signals:
            return
            
        # 设置表情选择框的启用状态
        self.ui.comboBox_emotionSelect.setEnabled(not checked)
        
        updates = {}
        
        if checked:
            # 使用随机表情，移除emotion_index
            updates["emotion_index"] = None
        else:
            # 使用固定表情，设置当前选择的表情
            current_index = self.ui.comboBox_emotionSelect.currentIndex()
            if current_index >= 0:
                filter_name = self.ui.comboBox_emotionFilter.currentText()
                filtered_emotions = CONFIGS.get_filtered_emotions(self.current_character_id, filter_name)
                if current_index < len(filtered_emotions):
                    updates["emotion_index"] = filtered_emotions[current_index]
        
        # 更新预览样式
        CONFIGS.update_preview_component(self.layer_index, updates)
        
        # 发出配置改变信号
        self.config_changed.emit()

    def on_emotion_changed(self, index):
        """表情改变事件"""
        if index < 0 or self._ignore_signals or self.ui.checkBox_randomEmotion.isChecked():
            return
            
        # 获取实际的表情索引
        filter_name = self.ui.comboBox_emotionFilter.currentText()
        filtered_emotions = CONFIGS.get_filtered_emotions(self.current_character_id, filter_name)
        if index < len(filtered_emotions):
            updates = {
                "emotion_index": filtered_emotions[index],
            }
            
            # 更新预览样式
            CONFIGS.update_preview_component(self.layer_index, updates)
            
            # 发出配置改变信号
            self.config_changed.emit()
    
    def on_emotion_filter_changed(self, index):
        """表情筛选改变事件"""
        if index < 0 or self._ignore_signals:
            return
        
        filter_name = self.ui.comboBox_emotionFilter.currentText()
        self._init_emotion_combo(filter_name)
        
        # 更新配置中的emotion_filter
        updates = {
            "emotion_filter": filter_name
        }
        
        # 如果当前使用固定表情，需要重新计算表情索引
        if not self.ui.checkBox_randomEmotion.isChecked():
            current_index = self.ui.comboBox_emotionSelect.currentIndex()
            if current_index >= 0:
                filtered_emotions = CONFIGS.get_filtered_emotions(self.current_character_id, filter_name)
                if current_index < len(filtered_emotions):
                    updates["emotion_index"] = filtered_emotions[current_index]
        
        # 更新预览样式
        CONFIGS.update_preview_component(self.layer_index, updates)
        
        # 发出配置改变信号
        self.config_changed.emit()