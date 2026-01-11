# -*- coding: utf-8 -*-
"""标签页管理模块"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from ui.components import Ui_CharaCfg
from config import CONFIGS
from utils.psd_utils import get_pose_options, get_emotion_filter_emotion_options, get_clothing_action_options

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

    def get_overlay_value(self):
        """获取当前背景值"""
        bg_file = ""
        if self.comboBox_bgSelect.currentIndex() > 0:
            bg_file = self.comboBox_bgSelect.currentData()
        elif self.lineEdit_bgColor and self.lineEdit_bgColor.text():
            bg_file = self.lineEdit_bgColor.text()
        return bg_file
    
    def is_fixed_background(self):
        """是否使用固定背景"""
        return not self.checkBox_randomBg.isChecked()
    
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
        self.lineEdit_bgColor.setEnabled(not checked)
        
        if not checked:
            if self.comboBox_bgSelect.currentIndex() == 0 and self.lineEdit_bgColor and self.lineEdit_bgColor.text():
                # 输入了颜色
                color = self.lineEdit_bgColor.text()
                if color.startswith("#") and len(color) == 7:
                    # 更新颜色预览
                    self._update_color_preview(color)
        
        self.config_changed.emit()
    
    def on_bg_selected(self, index):
        """背景选择改变"""
        # 只有在不使用随机背景时才更新配置
        if not self.checkBox_randomBg.isChecked():
            if index > 0:  # 选择了图片
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
                        self._update_color_preview(color)

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
                    
                    # 清除背景图片选择
                    self.comboBox_bgSelect.setCurrentIndex(0)
                    
                    self.config_changed.emit()

                elif not text.startswith("#"):
                    # 颜色无效，清空预览
                    if self.widget_bgColorPreview:
                        self.widget_bgColorPreview.setStyleSheet("")
            else:
                self.config_changed.emit()
                if self.widget_bgColorPreview:
                    self.widget_bgColorPreview.setStyleSheet("")

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

        self._psd_emotion_options = {}
        self._psd_current_filters = []

        # 使用UI模板
        self.ui = Ui_CharaCfg()
        self.ui.setupUi(self)

        self._init_from_config()
        self._connect_signals()
    
    def _psd_info(self):
        return CONFIGS.get_psd_info(self.current_character_id)
        
    def _setup_psd_ui(self):
        """设置PSD角色UI"""
        config = self._get_component_config()
        
        # 姿态
        poses = get_pose_options(self.current_character_id)
        self.ui.combo_poise_select.clear()
        self.ui.combo_poise_select.addItems(poses)
        
        current_pose = config.get("pose", poses[0])
        self.ui.combo_poise_select.setCurrentText(current_pose)
        
        # 服装和动作
        self._update_clothing_action()
        
        # 修复：调用新的合并方法
        self._update_emotion_filter_and_combo()
        
        # 显示/隐藏控件
        self.ui.label_poise_select.setVisible(True)
        self.ui.combo_poise_select.setVisible(True)
        
    def _setup_normal_ui(self):
        """设置普通角色UI"""
        self.ui.label_poise_select.hide()
        self.ui.combo_poise_select.hide()
        self.ui.label_clothes_select.hide()
        self.ui.combo_clothes_select.hide()
        self.ui.label_action_select.hide()
        self.ui.combo_action_select.hide()
        
        self._update_emotion_filter_and_combo()

    def _update_clothing_action(self):
        """更新服装和动作列表"""
        if not self.current_character_id:
            return
        
        config = self._get_component_config()
        pose = self.ui.combo_poise_select.currentText()
        
        # 获取服装和动作
        clothes, actions = get_clothing_action_options(self.current_character_id, pose)
        
        # 更新UI
        for combo, items, label in [
            (self.ui.combo_clothes_select, clothes, self.ui.label_clothes_select),
            (self.ui.combo_action_select, actions, self.ui.label_action_select)
        ]:
            combo.blockSignals(True)
            combo.clear()
            if items:
                combo.addItems(items)
                label.setVisible(True)
                combo.setVisible(True)
            else:
                label.setVisible(False)
                combo.setVisible(False)
            combo.blockSignals(False)
        
        # 恢复选中值
        if clothes:
            clothing = config.get("clothing", clothes[0])
            self.ui.combo_clothes_select.setCurrentText(clothing)
        
        if actions:
            action = config.get("action", actions[0])
            self.ui.combo_action_select.setCurrentText(action)

    def _update_emotion_filter_and_combo(self):
        """
        统一更新表情筛选器和表情下拉框
        支持PSD角色和普通角色
        """
        if not self.current_character_id:
            return
        
        try:
            self._ignore_signals = True
            psd_info = CONFIGS.get_psd_info(self.current_character_id)
            
            # 保存当前选中的表情，用于后续恢复
            saved_emotion = self.ui.combo_emotion_select.currentText()
            self.ui.combo_emotion_select.clear()
            filter_name = self.ui.combo_emotion_filter.currentText() or  "全部"
            self.ui.combo_emotion_filter.clear()
            
            # 初始化变量
            filters = []
            emotions = []
            
            if psd_info:
                # PSD角色逻辑
                pose = self.ui.combo_poise_select.currentText()
                clothing = self.ui.combo_clothes_select.currentText()
                
                # 获取筛选器选项（如果姿态有表情）
                if pose and pose in psd_info["poses"]:
                    filters, self._psd_emotion_options = get_emotion_filter_emotion_options(
                        self.current_character_id, pose, clothing
                    )
                    
                    # 更新筛选器UI（只在有多个筛选选项时显示）
                    self.ui.combo_emotion_filter.blockSignals(True)
                    
                    avail_filter = bool(filters and len(filters)>1)

                    self.ui.label_emotion_filter.setVisible(avail_filter)
                    self.ui.combo_emotion_filter.setVisible(avail_filter)
                    
                    if avail_filter:
                        self.ui.combo_emotion_filter.addItems(filters)
                                                
                        # 恢复之前选中的筛选器
                        filter_name = filter_name if filter_name in filters else filters[0]
                        self.ui.combo_emotion_filter.setCurrentText(filter_name)
                    
                    self.ui.combo_emotion_filter.blockSignals(False)
                    
                    # 根据筛选器获取表情列表
                    if self._psd_emotion_options and filter_name in self._psd_emotion_options:
                        emotions = self._psd_emotion_options[filter_name]
                    else:
                        emotions = psd_info["poses"].get(pose, {}).get("expressions", [])
                else:
                    # 姿态无效，隐藏筛选器
                    self.ui.label_emotion_filter.setVisible(False)
                    self.ui.combo_emotion_filter.setVisible(False)
                    emotions = []
            
            else:
                # 普通角色逻辑
                emotion_count = CONFIGS.mahoshojo.get(self.current_character_id, {}).get("emotion_count", 0)
                
                self.ui.combo_emotion_filter.blockSignals(True)
                
                avail_emos = bool(emotion_count)
                self.ui.label_emotion_filter.setVisible(avail_emos)
                self.ui.combo_emotion_filter.setVisible(avail_emos)

                if avail_emos:
                    emo_list = []
                    emo_list.append("全部")
                    for emo in CONFIGS.emotion_list:
                        if CONFIGS.mahoshojo.get(self.current_character_id, {}).get(emo, 0):
                            emo_list.append(emo)
                    self.ui.combo_emotion_filter.addItems(emo_list)
                    
                    # 恢复之前选中的筛选器
                    filter_name = filter_name if filter_name in emo_list else emo_list[0]
                    self.ui.combo_emotion_filter.setCurrentText(filter_name)
                
                self.ui.combo_emotion_filter.blockSignals(False)
                
                # 获取筛选后的表情列表
                if avail_emos:
                    filtered_emotions = CONFIGS.get_filtered_emotions(self.current_character_id, filter_name)
                    emotions = [f"表情 {i}" for i in filtered_emotions]
            
            # 更新表情下拉框
            self.ui.combo_emotion_select.blockSignals(True)
            
            if emotions:
                self.ui.combo_emotion_select.addItems(emotions)
                
                # 尝试恢复之前选中的表情
                if saved_emotion and saved_emotion in emotions:
                    index = self.ui.combo_emotion_select.findText(saved_emotion)
                    if index >= 0:
                        self.ui.combo_emotion_select.setCurrentIndex(index)
                else:
                    self.ui.combo_emotion_select.setCurrentIndex(0)
            else:
                self.ui.combo_emotion_select.addItem("无可用表情")
            
            self.ui.combo_emotion_select.blockSignals(False)
            
            # 根据随机复选框设置是否启用
            has_emotions = bool(emotions) and (len(emotions) == 0 or emotions[0] != "无可用表情")
            self.ui.combo_emotion_select.setEnabled(has_emotions and not self.ui.checkbox_random_emotion.isChecked())
            
        finally:
            self._ignore_signals = False
        
    def _get_component_config(self):
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
    
    def _init_from_config(self):
        """从配置初始化UI"""
        try:
            self._ignore_signals = True
            
            config = self._get_component_config()
            if not config:
                return
            
            # 初始化角色列表
            self._init_character_combo()
            
            # 设置当前角色
            char_id = config.get("character_name", CONFIGS.character_list[1] if len(CONFIGS.character_list) > 1 else CONFIGS.character_list[0])
            self._set_character(char_id)
            
            # 设置随机/固定
            use_fixed = config.get("use_fixed_character", False)
            self.ui.checkbox_random_emotion.setChecked(not use_fixed)
            
            # 加载UI
            self._reload_ui()
            
        finally:
            self._ignore_signals = False

    def _set_character(self, char_id):
        """设置角色选择"""
        self.current_character_id = char_id
        full_text = f"{CONFIGS.get_character(char_id, full_name=True)} ({char_id})"
        idx = self.ui.combo_character_select.findText(full_text)
        if idx >= 0:
            self.ui.combo_character_select.setCurrentIndex(idx)

    def _reload_ui(self):
        """根据角色类型加载UI"""
        psd_info = CONFIGS.get_psd_info(self.current_character_id)
        if psd_info:
            self._setup_psd_ui()
        else:
            self._setup_normal_ui()

    def _update_psd_subcontrols_from_pose(self, pose, saved_clothing=None, saved_action=None):
        """根据姿态更新PSD子控件（服装、动作、表情）"""
        info = self._psd_info()
        if not info or pose not in info["poses"]:
            # 隐藏所有
            self.ui.label_clothes_select.setVisible(False)
            self.ui.combo_clothes_select.setVisible(False)
            self.ui.label_action_select.setVisible(False)
            self.ui.combo_action_select.setVisible(False)
            return
        
        pose_data = info["poses"][pose]
        
        if pose_data.get("clothes_source") == "pose":
            clothes = list(pose_data.get("clothes", {}).keys())
        elif pose_data.get("clothes_source") == "global" and info.get("global_clothes"):
            clothes = list(info["global_clothes"].keys())
        else:
            clothes = []
        
        has_clothes = len(clothes) > 0
        
        self.ui.combo_clothes_select.clear()
        self.ui.label_clothes_select.setVisible(has_clothes)
        self.ui.combo_clothes_select.setVisible(has_clothes)
        
        if has_clothes:
            self.ui.combo_clothes_select.addItems(clothes)
            # 优先使用保存的值
            if saved_clothing and saved_clothing in clothes:
                idx = self.ui.combo_clothes_select.findText(saved_clothing)
                if idx >= 0:
                    self.ui.combo_clothes_select.setCurrentIndex(idx)
        
        # ========== 更新动作 ==========
        # 根据actions_source从正确位置获取动作列表
        actions = set()
        
        if pose_data.get("actions_source") == "pose":
            # 结构B：动作直接在姿态下
            for clothing_list in pose_data.get("clothes", {}).values():
                actions.update(clothing_list)
        elif pose_data.get("actions_source") == "global" and info.get("global_actions"):
            # 结构A：使用全局动作
            actions.update(info["global_actions"])
        
        actions = sorted(list(actions))
        has_actions = len(actions) > 0
        
        self.ui.combo_action_select.clear()
        self.ui.label_action_select.setVisible(has_actions)
        self.ui.combo_action_select.setVisible(has_actions)
        
        if has_actions:
            self.ui.combo_action_select.addItems(actions)
            # 优先使用保存的值
            if saved_action and saved_action in actions:
                idx = self.ui.combo_action_select.findText(saved_action)
                if idx >= 0:
                    self.ui.combo_action_select.setCurrentIndex(idx)
        
        # ========== 更新表情 ==========
        self._update_emotion_filter_and_combo()
                    
    def _init_character_combo(self):
        """初始化角色选择下拉框"""
        character_names = []
        for char_id in CONFIGS.character_list:
            full_name = CONFIGS.get_character(char_id, full_name=True)
            character_names.append(f"{full_name} ({char_id})")
        
        self.ui.combo_character_select.clear()
        self.ui.combo_character_select.addItems(character_names)
    
    def _connect_signals(self):
        """连接信号 - 使用统一处理函数"""
        # 角色切换（保持独立处理）
        self.ui.combo_character_select.currentIndexChanged.connect(self._on_character_changed)
        
        # PSD选项统一处理（姿态、服装、动作）
        self.ui.combo_poise_select.currentIndexChanged.connect(lambda: self._on_psd_option_changed("pose"))
        self.ui.combo_clothes_select.currentIndexChanged.connect(lambda: self._on_psd_option_changed("clothing"))
        self.ui.combo_action_select.currentIndexChanged.connect(lambda: self._on_psd_option_changed("action"))
        
        # 表情筛选使用独立函数
        self.ui.combo_emotion_filter.currentIndexChanged.connect(self._on_emotion_filter_changed)
        
        # 表情选择（单独处理）
        self.ui.combo_emotion_select.currentIndexChanged.connect(self._on_emotion_selected)
        
        # 随机选择复选框
        self.ui.checkbox_random_emotion.toggled.connect(self._on_random_emotion_toggled)
    
    def _on_random_emotion_toggled(self, checked):
        """随机表情复选框状态改变"""
        if self._ignore_signals:
            return
        
        # 刷新表情列表以更新可用状态
        self._update_emotion_filter_and_combo()
        
        self.config_changed.emit()

    def _on_psd_option_changed(self, changed_option=""):
        """
        PSD选项统一处理函数（姿态/服装/动作变化）
        根据依赖关系自动刷新子控件并保留用户选择
        """
        if self._ignore_signals:
            return
        
        # 保存当前选中的值（用于后续恢复）
        saved_values = {
            "pose": self.ui.combo_poise_select.currentText(),
            "clothing": self.ui.combo_clothes_select.currentText(),
            "action": self.ui.combo_action_select.currentText(),
        }
        
        # 根据变化类型决定刷新哪些子控件
        if changed_option == "pose":
            self._update_clothing_action_from_pose()
            self._update_emotion_filter_and_combo()
        elif changed_option == "clothing":
            self._update_action_from_clothing()
            self._update_emotion_filter_and_combo() 
        
        # 恢复之前的选择（如果在新列表中还存在）
        self._restore_selection_if_available(self.ui.combo_poise_select, saved_values["pose"])
        self._restore_selection_if_available(self.ui.combo_clothes_select, saved_values["clothing"])
        self._restore_selection_if_available(self.ui.combo_action_select, saved_values["action"])
        
        # 更新PSD组件配置
        print("emit 1")
        self.config_changed.emit()

    def _update_clothing_action_from_pose(self):
        """当姿态改变时，重新加载服装和动作列表"""
        if not self.current_character_id or not self._psd_info():
            return
        
        pose = self.ui.combo_poise_select.currentText()
        psd_info = self._psd_info()
        
        if not pose or pose not in psd_info["poses"]:
            # 隐藏所有控件
            self.ui.label_clothes_select.setVisible(False)
            self.ui.combo_clothes_select.setVisible(False)
            self.ui.label_action_select.setVisible(False)
            self.ui.combo_action_select.setVisible(False)
            return
        
        pose_data = psd_info["poses"][pose]
        
        # ========== 更新服装 ==========
        # 根据clothes_source从正确位置获取服装列表
        if pose_data.get("clothes_source") == "pose":
            # 结构B：服装在姿态内
            clothes = list(pose_data.get("clothes", {}).keys())
        elif pose_data.get("clothes_source") == "global" and psd_info.get("global_clothes"):
            # 结构A：使用全局服装
            clothes = list(psd_info["global_clothes"].keys())
        else:
            clothes = []
        
        has_clothes = len(clothes) > 0
        
        self.ui.combo_clothes_select.blockSignals(True)
        self.ui.combo_clothes_select.clear()
        self.ui.label_clothes_select.setVisible(has_clothes)
        self.ui.combo_clothes_select.setVisible(has_clothes)
        
        if has_clothes:
            self.ui.combo_clothes_select.addItems(clothes)
        self.ui.combo_clothes_select.blockSignals(False)
        
        # ========== 更新动作（先根据姿态获取） ==========
        self._update_action_from_clothing()

    def _update_action_from_clothing(self):
        """根据当前服装更新动作列表（如果服装没变化，则根据姿态获取所有动作）"""
        if not self.current_character_id or not self._psd_info():
            return
        
        pose = self.ui.combo_poise_select.currentText()
        clothing = self.ui.combo_clothes_select.currentText()
        psd_info = self._psd_info()
        
        if not pose or pose not in psd_info["poses"]:
            return
        
        pose_data = psd_info["poses"][pose]
        actions = set()
        
        # 根据actions_source从正确位置获取动作列表
        if pose_data.get("actions_source") == "pose":
            # 结构B：动作在姿态下
            if clothing and pose_data.get("clothes_source") == "pose":
                # 如果有当前服装，获取该服装下的动作
                actions.update(pose_data.get("clothes", {}).get(clothing, []))
            else:
                # 没有具体服装，获取姿态下所有服装的动作
                for clothing_list in pose_data.get("clothes", {}).values():
                    actions.update(clothing_list)
        elif pose_data.get("actions_source") == "global" and psd_info.get("global_actions"):
            # 结构A：使用全局动作
            actions.update(psd_info["global_actions"])
        
        actions = sorted(list(actions))
        has_actions = len(actions) > 0
        
        self.ui.combo_action_select.blockSignals(True)
        self.ui.combo_action_select.clear()
        self.ui.label_action_select.setVisible(has_actions)
        self.ui.combo_action_select.setVisible(has_actions)
        
        if has_actions:
            self.ui.combo_action_select.addItems(actions)
        self.ui.combo_action_select.blockSignals(False)

    def _restore_selection_if_available(self, combo_box, previous_value):
        """
        恢复之前的选择（如果在新列表中还存在）
        操作期间屏蔽信号，避免循环触发
        """
        if not previous_value:
            return

        # 查找之前值在新列表中的索引
        index = combo_box.findText(previous_value)
        
        blocked = combo_box.blockSignals(True)
        try:
            if index >= 0:
                # 如果存在，恢复选择
                combo_box.setCurrentIndex(index)
            else:
                # 如果不存在，自动选择第一项
                combo_box.setCurrentIndex(0)
        finally:
            combo_box.blockSignals(blocked)

    def _on_emotion_selected(self):
        """表情选择改变（仅更新配置和预览）"""
        if self._ignore_signals:
            return
        
        print("emit 2")
        self.config_changed.emit()

    def _on_emotion_filter_changed(self):
        """表情筛选改变时只更新表情列表"""
        if self._ignore_signals:
            return
        
        # 调用统一的更新函数
        self._update_emotion_filter_and_combo()

        print("emit 3")
        self.config_changed.emit()

    def is_fixed_character(self):
        """判断是否为固定角色"""
        return not self.ui.checkbox_random_emotion.isChecked()

    def get_current_values(self):
        """关键方法：返回当前UI的值，供预览生成时调用"""
        values = {
            "character_name": self.current_character_id,
            "use_fixed_character": not self.ui.checkbox_random_emotion.isChecked(),
        }
        
        # 如果是PSD角色
        if CONFIGS.get_psd_info(self.current_character_id):
            values.update({
                "pose": self.ui.combo_poise_select.currentText(),
                "clothing": self.ui.combo_clothes_select.currentText(),
                "action": self.ui.combo_action_select.currentText(),
                "emotion_index": self.ui.combo_emotion_select.currentText(),
                "emotion_filter": self.ui.combo_emotion_filter.currentText(),
                "emotion_list": self._psd_emotion_options.get(self.ui.combo_emotion_filter.currentText(), []),
                "overlay": "__PSD__"
            })
        else:
            emotion_data = self.ui.combo_emotion_select.currentIndex() + 1
            values.update({
                "emotion_index": emotion_data if emotion_data else 1,
                "emotion_filter": self.ui.combo_emotion_filter.currentText(),
                "overlay": ""
            })
        
        return values
    
    def _on_character_changed(self, index):
        """角色选择改变 - 只更新角色配置"""
        if index < 0 or self._ignore_signals:
            return
        
        selected_text = self.ui.combo_character_select.currentText()
        if "(" in selected_text and ")" in selected_text:
            char_id = selected_text.split("(")[-1].rstrip(")")
            self.current_character_id = char_id
            
            # 更新配置文件中的角色名称
            CONFIGS.update_preview_component(self.layer_index, {"character_name": char_id})
            
            self._ignore_signals = True
            self._reload_ui()
            
            # 只发送一次信号，触发预览更新
            print("emit 4")
            self.config_changed.emit()