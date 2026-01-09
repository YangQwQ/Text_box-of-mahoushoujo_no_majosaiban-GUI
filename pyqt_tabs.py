# -*- coding: utf-8 -*-
"""标签页管理模块"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from ui.components import Ui_CharaCfg
from config import CONFIGS
from image_processor import clear_cache

class BackgroundTabWidget(QWidget):
    """背景标签页组件 - 使用UI设计器中的布局"""
    
    config_changed = Signal()
    
    def __init__(self, parent=None, component_config=None, layer_index=0, ui_controls=None):
        super().__init__(parent)
        
        # 存储组件配置的引用
        self.layer_index = layer_index
        self._component_config = component_config or {}  # 存储传入的配置
        self._ignore_signals = False

        # 使用UI设计器中的控件
        self.checkBox_randomBg = ui_controls.get('checkBox_randomBg')
        self.comboBox_bgSelect = ui_controls.get('comboBox_bgSelect')
        self.lineEdit_bgColor = ui_controls.get('lineEdit_bgColor')
        self.widget_bgColorPreview = ui_controls.get('widget_bgColorPreview')
        
        self._connect_signals()
        
        # 加载背景图片列表并初始化UI
        self._init_from_config()
    
    def get_component_config(self):
        """获取当前图层的组件配置"""
        if not CONFIGS.preview_style or 'image_components' not in CONFIGS.preview_style:
            return self._component_config  # 返回传入的配置
        
        for component in CONFIGS.preview_style['image_components']:
            if component.get("layer") == self.layer_index:
                return component
        return self._component_config  # 返回传入的配置
    
    def _load_background_files(self, overlay = ""):
        """加载背景图片文件列表 - 使用 CONFIGS.background_list"""
        self.comboBox_bgSelect.clear()

        # 总是添加"无"选项
        self.comboBox_bgSelect.addItem("无", "")
        
        # 从 CONFIGS.background_list 添加背景文件
        for bg_file in CONFIGS.background_list:
            self.comboBox_bgSelect.addItem(bg_file, bg_file)        

    
    def _init_from_config(self):
        """从配置初始化UI"""
        try:
            self._ignore_signals = True

            component_config = self._component_config
            overlay = component_config.get("overlay", "")
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
            
            self._load_background_files(overlay)
            
            # 然后设置控件内容
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
                    # 图片 - 确保下拉框中有这个选项
                    index = self.comboBox_bgSelect.findData(overlay)
                    if index >= 0:
                        self.comboBox_bgSelect.setCurrentIndex(index)
                    else:
                        # 如果不在下拉框中，添加它并选择
                        self.comboBox_bgSelect.addItem(overlay, overlay)
                        self.comboBox_bgSelect.setCurrentIndex(self.comboBox_bgSelect.count() - 1)
                    
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
                component_config["use_fixed_background"] = False
        finally:
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

    def on_color_changed(self, text):
        """颜色输入改变"""
        if self._ignore_signals:
            return
        
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

class CharacterTabWidget(QWidget):
    """角色标签页组件，直接使用UI模板"""

    config_changed = Signal()
    
    def __init__(self, parent=None, component_config=None, layer_index=1):
        super().__init__(parent)
        
        # 存储组件配置的引用
        self.layer_index = layer_index
        self.current_character_id = None
        self._component_config = component_config
        self._ignore_signals = False
        self._pos_changing = False

        # 使用UI模板
        self.ui = Ui_CharaCfg()
        self.ui.setupUi(self)

        self._init_emotion_filter_combo()
        self._init_from_config()
        self._connect_signals()
    
    def _psd_info(self):
        return CONFIGS.get_psd_info(self.current_character_id)
    
    def _setup_psd_ui(self, info):
        try:
            self._ignore_signals = True

            poses = list(info["poses"].keys())
            has_pose = bool(poses)
            has_cloth = any(bool(v["clothes"]) for v in info["poses"].values())
            has_action = any(any(v2) for v in info["poses"].values() for v2 in v["clothes"].values())

            self.ui.label_emotion_filter.hide()
            self.ui.combo_emotion_filter.hide()
            self.ui.label_poise_select.setVisible(has_pose)
            self.ui.combo_poise_select.setVisible(has_pose)
            self.ui.label_clothes_select.setVisible(has_cloth)
            self.ui.combo_clothes_select.setVisible(has_cloth)
            self.ui.label_action_select.setVisible(has_action)
            self.ui.combo_action_select.setVisible(has_action)

            if has_pose:
                self.ui.combo_poise_select.clear()
                self.ui.combo_poise_select.addItems(poses)
            else:
                self.ui.combo_poise_select.currentIndexChanged.disconnect()
        finally:
            self._ignore_signals = False

    def _setup_normal_ui(self):
        self.ui.label_poise_select.hide()
        self.ui.combo_poise_select.hide()
        self.ui.label_clothes_select.hide()
        self.ui.combo_clothes_select.hide()
        self.ui.label_action_select.hide()
        self.ui.combo_action_select.hide()
    
    def _on_psd_pose_changed(self, _):
        if self._ignore_signals and not _:
            return

        info = self._psd_info()
        if not info:
            return
        pose = self.ui.combo_poise_select.currentText()
        if not pose:
            return
        
        try:
            self._pos_changing = True

            clothes = list(info["poses"][pose]["clothes"].keys())
            actions = {a for lst in info["poses"][pose]["clothes"].values() for a in lst}

            self.ui.combo_clothes_select.clear()
            if clothes:
                self.ui.combo_clothes_select.addItems(clothes)

            self.ui.combo_action_select.clear()
            if actions:
                self.ui.combo_action_select.addItems(sorted(actions))

            self._init_emotion_combo()
            self.ui.combo_emotion_select.setCurrentIndex(0)
        finally:
            self._pos_changing = False
            self._update_psd_component()

    def _update_psd_component(self):
        """PSD 模式下，把当前 UI 值实时写回 preview_style"""
        if not self._psd_info() or self._pos_changing:
            return
        
        emo_idx = self.ui.combo_emotion_select.currentText()
        updates = {
            "pose":      self.ui.combo_poise_select.currentText(),
            "clothing":  self.ui.combo_clothes_select.currentText(),
            "action":    self.ui.combo_action_select.currentText(),
            "emotion_index": emo_idx if emo_idx != "无可用表情" else "",
            "overlay":   "__PSD__"
        }
        CONFIGS.update_preview_component(self.layer_index, updates)
        
        if not self._pos_changing and not self._ignore_signals:
            self.config_changed.emit()
        
    def get_component_config(self):
        """获取当前图层的组件配置"""
        # 优先使用传入的配置
        if self._component_config:
            return self._component_config
        
        # 如果没有传入配置，从预览样式中获取
        if not CONFIGS.preview_style or 'image_components' not in CONFIGS.preview_style:
            return None
        
        for component in CONFIGS.preview_style['image_components']:
            if component.get("layer") == self.layer_index:
                self._component_config = component  # 缓存配置
                return component
        
        return None
    
    def _init_emotion_filter_combo(self):
        """初始化表情筛选下拉框"""
        # 获取情感列表
        emotion_filters = ["全部"] + CONFIGS.emotion_list
        self.ui.combo_emotion_filter.clear()
        self.ui.combo_emotion_filter.addItems(emotion_filters)
    
    def _init_from_config(self):
        """从配置初始化UI"""
        component_config = self.get_component_config()
        if not component_config:
            return
        
        # 设置标志，避免信号触发更新
        self._ignore_signals = True
        
        try:
            self._init_character_combo()
            # 角色
            if "character_name" in component_config:
                char_id = component_config["character_name"]
            else:
                char_id = CONFIGS.character_list[1] if len(CONFIGS.character_list) > 1 else CONFIGS.character_list[0]
            self.current_character_id = char_id
            full_text = f"{CONFIGS.get_character(char_id, full_name=True)} ({char_id})"
            idx = self.ui.combo_character_select.findText(full_text)
            if idx >= 0:
                self.ui.combo_character_select.setCurrentIndex(idx)
            
            psd = self._psd_info()
            if psd:
                self._setup_psd_ui(psd)
                self._on_psd_pose_changed(0)
            else:
                self._setup_normal_ui()

            # 表情部分
            self._init_emotion_combo()
            use_fixed = component_config.get("use_fixed_character", False)
            emotion_idx = component_config.get("emotion_index")
            if not use_fixed or emotion_idx is None:
                self.ui.checkbox_random_emotion.setChecked(True)
                self.ui.combo_emotion_select.setEnabled(False)
            else:
                self.ui.checkbox_random_emotion.setChecked(False)
                self.ui.combo_emotion_select.setEnabled(True)
                filter_name = self.ui.combo_emotion_filter.currentText()
                filtered = CONFIGS.get_filtered_emotions(self.current_character_id, filter_name)
                if emotion_idx in filtered:
                    self.ui.combo_emotion_select.setCurrentIndex(filtered.index(emotion_idx))
        finally:
            # 恢复信号处理
            self._ignore_signals = False
    
    def _init_character_combo(self):
        """初始化角色选择下拉框"""
        character_names = []
        for char_id in CONFIGS.character_list:
            full_name = CONFIGS.get_character(char_id, full_name=True)
            character_names.append(f"{full_name} ({char_id})")
        
        self.ui.combo_character_select.clear()
        self.ui.combo_character_select.addItems(character_names)
    
    def _init_emotion_combo(self, filter_name="全部"):
        """初始化表情下拉框，可按照筛选条件过滤"""
        try:
            self._ignore_signals = True

            if self._psd_info():
                pose = self.ui.combo_poise_select.currentText()
                exprs = self._psd_info()["poses"].get(pose, {}).get("expressions", [])
                self.ui.combo_emotion_select.clear()
                self.ui.combo_emotion_select.addItems(exprs if exprs else ["无可用表情"])
                self.ui.combo_emotion_select.setEnabled(
                    bool(exprs) and not self.ui.checkbox_random_emotion.isChecked()
                )
                return

            # 原普通角色逻辑保留
            char = self.current_character_id or CONFIGS.get_character()
            filtered = CONFIGS.get_filtered_emotions(char, filter_name)
            emotions = [f"表情 {i}" for i in filtered]
            self.ui.combo_emotion_select.clear()
            self.ui.combo_emotion_select.addItems(emotions if emotions else ["无可用表情"])
            self.ui.combo_emotion_select.setEnabled(
                bool(emotions) and not self.ui.checkbox_random_emotion.isChecked()
            )
        finally:
            self._ignore_signals = False
    
    def _connect_signals(self):
        """连接信号槽"""
        self.ui.combo_character_select.currentIndexChanged.connect(self.on_character_changed)
        self.ui.checkbox_random_emotion.toggled.connect(self.on_emotion_random_changed)
    
        self.ui.combo_emotion_select.currentIndexChanged.connect(self._update_psd_component)
        self.ui.combo_clothes_select.currentIndexChanged.connect(self._update_psd_component)
        self.ui.combo_action_select.currentIndexChanged.connect(self._update_psd_component)

        self.ui.combo_poise_select.currentIndexChanged.connect(self._on_psd_pose_changed)
        self.ui.combo_emotion_select.currentIndexChanged.connect(self.on_emotion_changed)
        self.ui.combo_emotion_filter.currentIndexChanged.connect(self.on_emotion_filter_changed)
        
    def on_character_changed(self, index):
        if index < 0 or self._ignore_signals:
            return

        clear_cache()

        updates = {"overlay":   ""}
        CONFIGS.update_preview_component(self.layer_index, updates)

        self._ignore_signals = True
        try:
            selected_text = self.ui.combo_character_select.currentText()
            if "(" in selected_text and ")" in selected_text:
                char_id = selected_text.split("(")[-1].rstrip(")")
                self.current_character_id = char_id
                CONFIGS.update_preview_component(self.layer_index,
                                                 {"character_name": char_id})
                psd = self._psd_info()
                if psd:
                    self._setup_psd_ui(psd)
                    self._on_psd_pose_changed(1)
                else:
                    self._setup_normal_ui()
                    self._init_emotion_combo()
                    self.config_changed.emit()
        finally:
            self._ignore_signals = False
            
    def on_emotion_random_changed(self, checked):
        """表情随机选择改变"""

        # 设置表情选择框的启用状态
        self.ui.combo_emotion_select.setEnabled(not checked)
        
        updates = {}
        
        if checked:
            # 使用随机表情，移除emotion_index
            updates["emotion_index"] = None
        else:
            # 使用固定表情，设置当前选择的表情
            current_index = self.ui.combo_emotion_select.currentIndex()
            if current_index >= 0:
                filter_name = self.ui.combo_emotion_filter.currentText()
                filtered_emotions = CONFIGS.get_filtered_emotions(self.current_character_id, filter_name)
                if current_index < len(filtered_emotions):
                    updates["emotion_index"] = filtered_emotions[current_index]
        
        # 更新预览样式
        CONFIGS.update_preview_component(self.layer_index, updates)
        if self._ignore_signals:
            return
        # 发出配置改变信号
        self.config_changed.emit()

    def on_emotion_changed(self, index):
        """表情改变事件"""
        if index < 0 or self._ignore_signals or self.ui.checkbox_random_emotion.isChecked():
            return
            
        # 获取实际的表情索引
        filter_name = self.ui.combo_emotion_filter.currentText()
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
        
        filter_name = self.ui.combo_emotion_filter.currentText()
        self._init_emotion_combo(filter_name)
        
        # 更新配置中的emotion_filter
        updates = {
            "emotion_filter": filter_name
        }
        
        # 如果当前使用固定表情，需要重新计算表情索引
        if not self.ui.checkbox_random_emotion.isChecked():
            current_index = self.ui.combo_emotion_select.currentIndex()
            if current_index >= 0:
                filtered_emotions = CONFIGS.get_filtered_emotions(self.current_character_id, filter_name)
                if current_index < len(filtered_emotions):
                    updates["emotion_index"] = filtered_emotions[current_index]
        
        # 更新预览样式
        CONFIGS.update_preview_component(self.layer_index, updates)
        
        # 发出配置改变信号
        self.config_changed.emit()