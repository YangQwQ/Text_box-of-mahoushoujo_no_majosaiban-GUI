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

        # 使用UI模板
        self.ui = Ui_CharaCfg()
        self.ui.setupUi(self)

        self._init_from_config()
        self._connect_signals()
    
    def _psd_info(self):
        return CONFIGS.get_psd_info(self.current_character_id)
        
    def _setup_psd_ui(self):
        """设置PSD角色UI"""
        config = self._component_config

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
        
        config = self._component_config
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
            vaild_items = bool(items)
            if vaild_items:
                combo.addItems(items)
            label.setVisible(vaild_items)
            combo.setVisible(vaild_items)

            combo.blockSignals(False)
        
        # 恢复选中值
        if clothes:
            clothing = config.get("clothing", clothes[0])
            self.ui.combo_clothes_select.setCurrentText(clothing)
        
        if actions:
            action = config.get("action", actions[0])
            self.ui.combo_action_select.setCurrentText(action)
    
    def get_available_emotions(self):
        """
        获取当前UI中显示的所有可用表情
        返回格式: ["表情 1", "表情 2", ...] 或 ["微笑", "开心", ...]
        """
        emotions = []
        
        # 获取当前下拉框中的所有项目（不包括"无可用表情"）
        for i in range(self.ui.combo_emotion_select.count()):
            text = self.ui.combo_emotion_select.itemText(i)
            if text != "无可用表情":
                emotions.append(text)
        
        return emotions
    
    def get_available_filters(self):
        """
        获取当前UI中显示的所有可用筛选器
        返回格式: ["全部", "正面", "负面",...]
        """
        filters = []
        for i in range(self.ui.combo_emotion_filter.count()):
            text = self.ui.combo_emotion_filter.itemText(i)
            if text != "全部":
                filters.append(text)
        return filters

    def get_filtered_emotions(self, filter_name):
        psd_info = CONFIGS.get_psd_info(self.current_character_id)
        if psd_info:
            pose = self.ui.combo_poise_select.currentText()
            clothing = self.ui.combo_clothes_select.currentText()
            emo_list = {}
            if pose and pose in psd_info["poses"]:
                filters, emo_list = get_emotion_filter_emotion_options(
                    self.current_character_id, pose, clothing
                )
            filter_name = filter_name if (filter_name in filters) or filter_name in emo_list.get("全部") else "全部"
        else:
            emo_list = CONFIGS.mahoshojo.get(self.current_character_id, {}).get("emo", {})
            
        return emo_list.get(filter_name, [])

    def _update_emotion_filter_and_combo(self):
        """
        统一更新表情筛选器和表情下拉框
        支持PSD角色和普通角色
        """
        if not self.current_character_id:
            return
        
        try:
            self._ignore_signals = True
            
            # 获取角色配置
            character_config = CONFIGS.mahoshojo.get(self.current_character_id, {})
            psd_info = CONFIGS.get_psd_info(self.current_character_id)
            
            # 保存当前选中的值
            saved_filter = self.ui.combo_emotion_filter.currentText()  or  "全部"
            
            # 清空控件
            self.ui.combo_emotion_filter.clear()
            self.ui.combo_emotion_select.clear()
            
            emotions = []
            filters = ["全部"]
            show_filter = False
            
            if psd_info:
                # PSD角色逻辑
                pose = self.ui.combo_poise_select.currentText()
                clothing = self.ui.combo_clothes_select.currentText()
                
                if pose and pose in psd_info["poses"]:
                    filters, emo_list = get_emotion_filter_emotion_options(
                        self.current_character_id, pose, clothing
                    )
                    # 更新筛选器UI（只在有多个筛选选项时显示）
                    self.ui.combo_emotion_filter.blockSignals(True)
                    
                    # 设置可见性
                    show_filter = bool(filters and len(filters)>1)
                    saved_filter = saved_filter if saved_filter in filters else "全部"
                    if show_filter:
                        self.ui.combo_emotion_filter.addItems(filters)
                        self.ui.combo_emotion_filter.setCurrentText(saved_filter)
                    
                    self.ui.combo_emotion_filter.blockSignals(False)
                    
                    # 根据筛选器获取表情列表
                    if emo_list:
                        emotions = emo_list[saved_filter]
            else:
                # 普通角色逻辑
                emotion_count = character_config.get("emotion_count", 0)
                
                if emotion_count > 0:
                    # 构建筛选器（从角色配置的emo键动态获取）
                    if "emo" in character_config:
                        for emotion_name, emotion_indices in character_config["emo"].items():
                            if emotion_indices:  # 如果有对应表情
                                filters.append(emotion_name)
                    
                    # 所有可用表情索引
                    all_indices = list(range(1, emotion_count + 1))
                    
                    # 根据当前筛选器获取表情列表
                    current_filter = saved_filter if saved_filter in filters else "全部"
                    if current_filter == "全部":
                        emotion_indices = all_indices
                    else:
                        emotion_indices = character_config["emo"].get(current_filter, [])
                    
                    emotions = [f"表情 {i}" for i in emotion_indices]
                    
                    # 显示筛选器
                    show_filter = len(filters) > 1
                    if show_filter:
                        self.ui.combo_emotion_filter.addItems(filters)
                        self.ui.combo_emotion_filter.setCurrentText(current_filter)

            # 显示筛选器
            self.ui.label_emotion_filter.setVisible(show_filter)
            self.ui.combo_emotion_filter.setVisible(show_filter)
                    
            # 更新表情下拉框
            self.ui.combo_emotion_select.blockSignals(True)
            if emotions:
                self.ui.combo_emotion_select.addItems(emotions)
                self.ui.combo_emotion_select.setCurrentIndex(0)
            else:
                self.ui.combo_emotion_select.addItem("无可用表情")
            
            self.ui.combo_emotion_select.blockSignals(False)
            
            # 根据随机复选框设置是否启用
            has_emotions = bool(emotions) and (len(emotions) == 0 or emotions[0] != "无可用表情")
            self.ui.combo_emotion_select.setEnabled(has_emotions and not self.ui.checkbox_random_emotion.isChecked())
            
        finally:
            self._ignore_signals = False
    
    def _init_from_config(self):
        """从配置初始化UI"""
        try:
            self._ignore_signals = True
            
            config = self._component_config
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
                    
    def _init_character_combo(self):
        """初始化角色选择下拉框"""
        character_names = []
        for char_id in CONFIGS.character_list:
            full_name = CONFIGS.get_character(char_id, full_name=True)
            character_names.append(f"{full_name} ({char_id})")
        
        self.ui.combo_character_select.clear()
        self.ui.combo_character_select.addItems(character_names)
    
    def _connect_signals(self):
        """连接信号"""
        # 角色部分
        self.ui.combo_character_select.currentIndexChanged.connect(self._on_character_changed)
        self.ui.combo_poise_select.currentIndexChanged.connect(lambda: self._on_psd_option_changed("pose"))
        self.ui.combo_clothes_select.currentIndexChanged.connect(lambda: self._on_psd_option_changed("clothing"))
        self.ui.combo_action_select.currentIndexChanged.connect(lambda: self._on_psd_option_changed("action"))
        
        # 表情部分
        self.ui.combo_emotion_filter.currentIndexChanged.connect(self._on_emotion_filter_changed)
        self.ui.combo_emotion_select.currentIndexChanged.connect(self._on_emotion_selected)
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
                "overlay": "__PSD__"
            })
        else:
            values.update({
                "emotion_index": self.ui.combo_emotion_select.currentIndex() + 1,
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

            # 更新角色名 （更新括号颜色需要这个）        
            for component in CONFIGS.style_configs[CONFIGS.current_style]['image_components']:
                if component.get("layer") == self.layer_index:
                    component["character_name"] = char_id
            
            self._ignore_signals = True
            self._reload_ui()
            
            # 只发送一次信号，触发预览更新
            print("emit 4")
            self.config_changed.emit()