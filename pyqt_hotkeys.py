# pyqt_hotkeys.py
from PySide6.QtCore import QObject, Signal, QThread
from pynput import keyboard
from config import CONFIGS


class HotkeyListener(QThread):
    """热键监听线程"""
    hotkey_triggered = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._listener = None
        self._hotkey_handlers = {}
        self._running = True
        
    def set_hotkeys(self, hotkey_configs, quick_chars):
        """设置热键映射"""
        self._hotkey_handlers.clear()
        
        for action, hotkey_str in hotkey_configs.items():
            self._hotkey_handlers[hotkey_str] = action
    
    def stop_listening(self):
        """停止监听"""
        self._running = False
        if self._listener:
            self._listener.stop()
    
    def run(self):
        """线程运行函数"""
        # 创建热键映射字典
        hotkey_map = {}
        for hotkey_str, action in self._hotkey_handlers.items():
            hotkey_map[hotkey_str] = lambda a=action: self.hotkey_triggered.emit(a)
        
        # 启动全局热键监听器
        try:
            with keyboard.GlobalHotKeys(hotkey_map) as listener:
                self._listener = listener
                listener.join()
        except Exception as e:
            print(f"热键监听器错误: {e}")


class HotkeyManager(QObject):
    """热键管理器"""
    
    def __init__(self, gui, core):
        super().__init__()
        self.gui = gui
        self.core = core
        self.listener = HotkeyListener()
        self.listener.hotkey_triggered.connect(self._handle_hotkey)
        self._active = True
        
        # 初始化热键
        self.setup_hotkeys()
    
    def setup_hotkeys(self):
        """设置热键"""
        # 重新加载配置
        hotkey_configs = CONFIGS.keymap
        quick_chars = CONFIGS.gui_settings.get("quick_characters", {})
        
        # 设置监听器的热键
        self.listener.set_hotkeys(hotkey_configs, quick_chars)
        
        # 启动监听线程
        if not self.listener.isRunning():
            self.listener.start()
        
        print(f"热键监听器已启动，平台: {CONFIGS.platform}")
    
    def _handle_hotkey(self, action):
        """处理热键触发"""
        if not self._active and action != "toggle_listener":
            return
        
        # 执行相应的动作
        if action == "start_generate":
            self.gui.generate_image()
        elif action == "next_character":
            self._switch_character(1)
        elif action == "prev_character":
            self._switch_character(-1)
        elif action == "next_emotion":
            self._switch_emotion(1)
        elif action == "prev_emotion":
            self._switch_emotion(-1)
        elif action == "next_background":
            self._switch_background(1)
        elif action == "prev_background":
            self._switch_background(-1)
        elif action.startswith("character_") and action in CONFIGS.gui_settings.get("quick_characters", {}):
            char_id = CONFIGS.gui_settings["quick_characters"][action]
            self._switch_to_character_by_id(char_id)
        elif action == "toggle_listener":
            self._toggle_hotkey_listener()
        
        print(f"触发热键: {action}")
    
    def _toggle_hotkey_listener(self):
        """切换热键监听状态"""
        self._active = not self._active
        status = "启用" if self._active else "禁用"
        self.gui.update_status(f"热键监听已{status}")
        print(f"热键监听状态已切换为: {status}")

    def _find_first_switchable_character_tab(self):
        """找到第一个可切换的角色标签页（非固定角色）"""
        for tab in self.gui.character_tabs:
            if not tab.is_fixed_character():
                return tab

        # 如果没有找到非固定角色标签页，返回第一个角色标签页
        if self.gui.character_tabs:
            return self.gui.character_tabs[0]
        return None
    
    def _switch_character(self, direction):
        """切换角色 - 修改对应标签页的下拉框"""
        tab = self._find_first_switchable_character_tab()
        if not tab:
            return
        
        # 计算新角色索引
        current_index =tab.ui.combo_character_select.currentIndex()
        max_index = tab.ui.combo_character_select.count()
        new_index = (current_index + direction) % max_index
        
        tab.ui.combo_character_select.setCurrentIndex(new_index)
        
        # 状态更新由UI变化自动触发
        new_char_id = CONFIGS.character_list[new_index]
        self.gui.update_status(f"已切换到角色: {CONFIGS.get_character(new_char_id, full_name=True)}")
    
    def _switch_to_character_by_id(self, char_id):
        """通过角色ID切换到指定角色"""
        if not char_id or char_id not in CONFIGS.character_list:
            return
        
        tab = self._find_first_switchable_character_tab()
        if tab:
            display_text = f"{CONFIGS.get_character(char_id, full_name=True)} ({char_id})"
            index = tab.ui.combo_character_select.findText(display_text)
            tab.ui.combo_character_select.setCurrentIndex(index)
            self.gui.update_status(f"已切换到角色: {CONFIGS.get_character(char_id, full_name=True)}")
    
    def _switch_emotion(self, direction):
        """切换表情 - 修改对应标签页的下拉框"""
        tab = self._find_first_switchable_character_tab()
        if not tab:
            return
        
        # 计算新表情索引
        current_emotion_index = tab.ui.combo_emotion_select.currentIndex()
        max_index = tab.ui.combo_emotion_select.count()
        new_index = (current_emotion_index + direction) % max_index

        tab.ui.checkbox_random_emotion.setChecked(False)

        tab.ui.combo_emotion_select.setCurrentIndex(new_index)
        self.gui.update_status(f"表情已切换到: 表情 {new_index+1}")
    
    def _switch_background(self, direction):
        """切换背景 - 直接修改下拉框索引"""
        if not self.gui.background_tab:
            return
        
        # 确保使用固定背景（取消随机）
        if self.gui.background_tab.checkBox_randomBg.isChecked():
            self.gui.background_tab.checkBox_randomBg.setChecked(False)
        
        # 检查下拉框是否启用且有内容（排除"无"选项）
        if not self.gui.background_tab.comboBox_bgSelect.isEnabled() or self.gui.background_tab.comboBox_bgSelect.count() <= 1:
            return
        
        # 计算新索引，跳过第一个"无"选项
        current_index = self.gui.background_tab.comboBox_bgSelect.currentIndex()
        max_index = self.gui.background_tab.comboBox_bgSelect.count()        
        new_index = (current_index + direction) % max_index
        new_index = new_index if new_index != 0 else 1

        self.gui.background_tab.comboBox_bgSelect.setCurrentIndex(new_index)
        
        # 获取背景文件名
        bg_text = self.gui.background_tab.comboBox_bgSelect.currentText()
        self.gui.update_status(f"背景已切换到: {bg_text}")
    
    
    def stop(self):
        """停止热键监听"""
        if self.listener.isRunning():
            self.listener.stop_listening()
            self.listener.quit()
            self.listener.wait()
            print("热键监听器已停止")