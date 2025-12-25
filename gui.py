"""魔裁文本框 GUI 版本"""

import tkinter as tk
from tkinter import ttk
import threading

from core import ManosabaCore
from gui_settings import SettingsWindow
from gui_style import StyleWindow
from gui_about import AboutWindow
from gui_hotkeys import HotkeyManager
from gui_components import PreviewManager, StatusManager
from config import CONFIGS

class ManosabaGUI:
    """魔裁文本框 GUI"""

    def __init__(self):
        self.core = ManosabaCore()
        # 设置GUI回调
        self.core.set_gui_callback(self.on_sentiment_analyzer_status_changed)
        # 设置状态更新回调
        self.core.set_status_callback(self.update_status)

        self.root = tk.Tk()
        self.root.title("魔裁文本框生成器")
        self.root.geometry("700x650")

        # 添加图标
        from path_utils import set_window_icon
        set_window_icon(self.root)
            
        # 初始化管理器
        self.hotkey_manager = HotkeyManager(self)
        self.preview_manager = PreviewManager(self)
        self.status_manager = StatusManager(self)
        self.about_window = None  # 关于窗口实例
        self.style_window = None  # 样式窗口实例

        # 图片生成状态
        self.is_generating = False

        self.setup_gui()
        self.root.bind("<Configure>", self.on_window_resize)

        self.hotkey_manager.setup_hotkeys()

        # 根据初始状态设置按钮可用性
        self.update_sentiment_button_state()

        # 根据随机表情状态设置情感筛选下拉框状态
        if self.emotion_random_var.get():
            self.sentiment_filter_combo.config(state="disabled")
        else:
            self.sentiment_filter_combo.config(state="readonly")
        
        # 启动预加载回调处理器
        self._start_preload_callback_processor()

        self.update_preview()
        self.update_sentiment_filter_combo()
    
    def _start_preload_callback_processor(self):
        """启动预加载回调处理器"""
        # 启动预加载管理器的回调处理器
        self.core.preload_manager._start_main_thread_callback_processor()
        
        # 定期处理预加载回调（每100ms检查一次）
        def process_callbacks():
            try:
                self.core.preload_manager.process_main_thread_callbacks()
            except Exception as e:
                print(f"处理预加载回调失败: {str(e)}")
            
            # 继续调度下一次处理
            self.root.after(100, process_callbacks)
        
        # 延迟启动，确保GUI完全初始化
        self.root.after(200, process_callbacks)

    def setup_gui(self):
        """设置 GUI 界面"""
        # 创建菜单栏
        self.setup_menu()

        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 角色选择
        ttk.Label(main_frame, text="选择角色:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.character_var = tk.StringVar()
        character_combo = ttk.Combobox(
            main_frame, textvariable=self.character_var, state="readonly", width=30
        )
        character_combo["values"] = [
            f"{CONFIGS.get_character(char_id, full_name=True)} ({char_id})"
            for char_id in CONFIGS.character_list
        ]
        character_combo.set(
            f"{CONFIGS.get_character(full_name=True)} ({CONFIGS.get_character()})"
        )
        character_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        character_combo.bind("<<ComboboxSelected>>", self.on_character_changed)

        # 表情选择框架
        emotion_frame = ttk.LabelFrame(main_frame, text="表情选择", padding="5")
        emotion_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 表情随机选择
        self.emotion_random_var = tk.BooleanVar(value=True)
        emotion_random_cb = ttk.Checkbutton(
            emotion_frame,
            text="随机表情",
            variable=self.emotion_random_var,
            command=self.on_emotion_random_changed,
        )
        emotion_random_cb.grid(row=0, column=0, sticky=tk.W, padx=5)

        # 情感筛选下拉框（新增）
        ttk.Label(emotion_frame, text="表情筛选:").grid(
            row=0, column=1, sticky=tk.W, padx=5
        )
        self.sentiment_filter_var = tk.StringVar()
        self.sentiment_filter_combo = ttk.Combobox(
            emotion_frame, textvariable=self.sentiment_filter_var, state="readonly", width=15
        )
        self.sentiment_filter_combo.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        self.sentiment_filter_combo.bind("<<ComboboxSelected>>", self.on_sentiment_filter_changed)
        
        # 表情下拉框
        ttk.Label(emotion_frame, text="指定表情:").grid(
            row=0, column=3, sticky=tk.W, padx=5
        )
        self.emotion_var = tk.StringVar()
        self.emotion_combo = ttk.Combobox(
            emotion_frame, textvariable=self.emotion_var, state="readonly", width=15
        )
        emotion_count = CONFIGS.current_character["emotion_count"]
        self.emotion_combo["values"] = [
            f"表情 {i}" for i in range(1, emotion_count + 1)
        ]
        self.emotion_combo.set("表情 1")
        self.emotion_combo.grid(row=0, column=4, sticky=(tk.W, tk.E), padx=5)
        self.emotion_combo.bind("<<ComboboxSelected>>", self.on_emotion_changed)
        self.emotion_combo.config(state="disabled")

        # 配置列权重
        emotion_frame.columnconfigure(2, weight=1)
        emotion_frame.columnconfigure(4, weight=1)

        # 背景选择框架
        background_frame = ttk.LabelFrame(main_frame, text="背景选择", padding="5")
        background_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )

        # 背景随机选择
        self.background_random_var = tk.BooleanVar(value=True)
        background_random_cb = ttk.Checkbutton(
            background_frame,
            text="随机背景",
            variable=self.background_random_var,
            command=self.on_background_random_changed,
        )
        background_random_cb.grid(row=0, column=0, sticky=tk.W, padx=5)

        # 背景下拉框
        ttk.Label(background_frame, text="指定背景:").grid(
            row=0, column=1, sticky=tk.W, padx=5
        )
        self.background_var = tk.StringVar()
        self.background_combo = ttk.Combobox(
            background_frame,
            textvariable=self.background_var,
            state="readonly",
            width=15,
        )
        background_count = CONFIGS.background_count
        self.background_combo["values"] = [
            f"背景 {i}" for i in range(1, background_count + 1)
        ]
        self.background_combo.set("背景 1")
        self.background_combo.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        self.background_combo.bind("<<ComboboxSelected>>", self.on_background_changed)
        self.background_combo.config(state="disabled")

        background_frame.columnconfigure(2, weight=1)

        # 设置框架
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding="5")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.auto_paste_var = tk.BooleanVar(value=CONFIGS.config.AUTO_PASTE_IMAGE)
        ttk.Checkbutton(
            settings_frame,
            text="自动粘贴",
            variable=self.auto_paste_var,
            command=self.on_auto_paste_changed,
        ).grid(row=0, column=0, sticky=tk.W, padx=5)

        self.auto_send_var = tk.BooleanVar(value=CONFIGS.config.AUTO_SEND_IMAGE)
        ttk.Checkbutton(
            settings_frame,
            text="自动发送",
            variable=self.auto_send_var,
            command=self.on_auto_send_changed,
        ).grid(row=0, column=1, sticky=tk.W, padx=5)

        # 只在 display 为 True 时显示情感匹配按钮
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        if sentiment_settings.get("display", False):
            self.sentiment_matching_var = tk.BooleanVar(value=sentiment_settings.get("enabled", False))
            self.sentiment_checkbutton = ttk.Checkbutton(
                settings_frame,
                text="情感匹配",
                variable=self.sentiment_matching_var,
                command=self.on_sentiment_matching_changed,
            )
            self.sentiment_checkbutton.grid(row=0, column=2, sticky=tk.W, padx=5)
            
        # 根据初始状态设置按钮可用性
        self.update_sentiment_button_state()

        # 预览框架
        preview_frame = ttk.LabelFrame(main_frame, text="图片预览", padding="5")
        preview_frame.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )

        # 使用预览管理器设置预览界面
        self.preview_manager.setup_preview_frame(preview_frame)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        # 状态栏
        self.status_manager.setup_status_bar(main_frame, 6)

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # self.update_preview()
        self.update_sentiment_filter_combo()

    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        menubar.add_command(label="设置", command=self.open_settings)
        menubar.add_command(label="样式", command=self.open_style)
        menubar.add_command(label="关于", command=self.open_about)

    def open_style(self):
        """打开样式编辑窗口"""
        # 打开样式窗口
        self.style_window = StyleWindow(self.root, self.core, self)

    def open_about(self):
        """打开关于窗口"""
        if not self.about_window:
            self.about_window = AboutWindow(self.root)
        self.about_window.open()

    def open_settings(self):
        """打开设置窗口"""
        # 停止热键监听
        self.hotkey_manager.stop_hotkey_listener()
        
        # 打开设置窗口
        settings_window = SettingsWindow(self.root, self.core, self)
        
        # 设置窗口关闭时的回调
        self.root.wait_window(settings_window.window)
        
        # 设置窗口关闭后重新启动热键监听
        self.hotkey_manager.setup_hotkeys()

    def on_window_resize(self, event):
        """处理窗口大小变化事件 - 调整大小并刷新内容"""
        if event.widget == self.root:
            self.preview_manager.handle_window_resize(event)

    def update_preview(self):
        """更新预览"""
        self.preview_manager.update_preview()

    def update_sentiment_filter_combo(self):
        """更新情感筛选下拉框的选项"""
        character_name = CONFIGS.get_character()
        character_meta = CONFIGS.mahoshojo.get(character_name, {})
        
        # 获取所有可用的情感列表
        available_sentiments = ["全部表情"]
        
        for sentiment in CONFIGS.emotion_list:
            # 检查该情感是否有对应的表情索引
            emotion_indices = character_meta.get(sentiment, [])
            if emotion_indices:  # 只有有可用表情的情感才添加
                available_sentiments.append(sentiment)
        
        # 更新下拉框选项
        self.sentiment_filter_combo["values"] = available_sentiments
        
        # 根据随机表情状态设置下拉框状态
        if self.emotion_random_var.get():
            self.sentiment_filter_combo.config(state="disabled")
        else:
            self.sentiment_filter_combo.config(state="readonly")
        
        # 设置默认值
        self.sentiment_filter_combo.set("全部表情")

    def on_sentiment_filter_changed(self, event=None):
        """情感筛选改变事件"""
        # 如果随机表情启用，则不执行筛选
        if self.emotion_random_var.get():
            return
        
        selected_sentiment = self.sentiment_filter_var.get()
        character_name = CONFIGS.get_character()
        character_meta = CONFIGS.mahoshojo.get(character_name, {})
        
        if selected_sentiment == "全部表情":
            # 显示所有表情
            emotion_count = CONFIGS.current_character["emotion_count"]
            self.emotion_combo["values"] = [
                f"表情 {i}" for i in range(1, emotion_count + 1)
            ]
        else:
            # 获取该情感对应的表情索引列表
            emotion_indices = character_meta.get(selected_sentiment, [])
            if emotion_indices:
                # 更新表情下拉框为可用表情
                self.emotion_combo["values"] = [
                    f"表情 {i}" for i in emotion_indices
                ]
            else:
                # 如果没有可用表情，清空下拉框
                self.emotion_combo["values"] = []
        
        # 如果有选项，设置第一个为默认
        if self.emotion_combo["values"]:
            self.emotion_combo.set(self.emotion_combo["values"][0])
            if not self.emotion_random_var.get():  # 只有在非随机模式下才更新选中
                try:
                    emotion_index = int(self.emotion_combo.get().split()[-1])
                    CONFIGS.selected_emotion = emotion_index
                except (ValueError, IndexError):
                    CONFIGS.selected_emotion = None
        else:
            self.emotion_combo.set("")
            CONFIGS.selected_emotion = None
        
        # 更新预览
        self.update_preview()

    def on_character_changed(self, event=None):
        """角色改变事件"""
        selected_text = self.character_var.get()
        char_id = selected_text.split("(")[-1].rstrip(")")

        # 更新核心角色
        char_idx = CONFIGS.character_list.index(char_id) + 1
        self.core.switch_character(char_idx)

        # 更新情感筛选下拉框
        self.update_sentiment_filter_combo()
        
        # 更新表情选项（先使用全部表情）
        self.sentiment_filter_combo.set("全部表情")
        
        # 根据随机表情状态决定是否执行筛选
        if not self.emotion_random_var.get():
            self.on_sentiment_filter_changed()  # 这会自动更新表情下拉框

        # 重置表情选择为第一个表情
        if self.emotion_combo["values"]:
            self.emotion_combo.set(self.emotion_combo["values"][0])
            if self.emotion_random_var.get():
                CONFIGS.selected_emotion = None
            else:
                try:
                    CONFIGS.selected_emotion = int(self.emotion_combo.get().split()[-1])
                except (ValueError, IndexError):
                    CONFIGS.selected_emotion = None
        else:
            self.emotion_combo.set("")
            CONFIGS.selected_emotion = None

        # 标记需要更新预览内容
        self.update_preview()
        self.update_status(f"已切换到角色: {CONFIGS.get_character(full_name=True)}")

    def update_emotion_options(self):
        """更新表情选项"""
        emotion_count = CONFIGS.current_character["emotion_count"]
        self.emotion_combo["values"] = [
            f"表情 {i}" for i in range(1, emotion_count + 1)
        ]
        self.emotion_combo.set("表情 1")

    def on_emotion_random_changed(self):
        """表情随机选择改变"""
        if self.emotion_random_var.get():
            # 启用随机表情时，禁用表情下拉框和情感筛选下拉框
            self.emotion_combo.config(state="disabled")
            self.sentiment_filter_combo.config(state="disabled")
            CONFIGS.selected_emotion = None
        else:
            # 禁用随机表情时，启用表情下拉框和情感筛选下拉框
            self.emotion_combo.config(state="readonly")
            self.sentiment_filter_combo.config(state="readonly")
            
            # 更新表情选择
            emotion_value = self.emotion_combo.get()
            if emotion_value:
                try:
                    emotion_index = int(emotion_value.split()[-1])
                    CONFIGS.selected_emotion = emotion_index
                except (ValueError, IndexError):
                    CONFIGS.selected_emotion = None
            else:
                CONFIGS.selected_emotion = None

        self.update_preview()

    def on_emotion_changed(self, event=None):
        """表情改变事件"""
        # 取消情感匹配勾选
        if CONFIGS.gui_settings["sentiment_matching"].get("display", False) and self.sentiment_matching_var.get():
            self.sentiment_matching_var.set(False)
            self.on_sentiment_matching_changed()
            self.update_status("已取消情感匹配（手动选择表情）")

        if not self.emotion_random_var.get():
            emotion_value = self.emotion_var.get()
            if emotion_value:
                try:
                    emotion_index = int(emotion_value.split()[-1])
                    CONFIGS.selected_emotion = emotion_index
                    self.update_preview()
                except (ValueError, IndexError):
                    CONFIGS.selected_emotion = None
                    self.update_status("表情选择无效")

    def on_background_random_changed(self):
        """背景随机选择改变"""
        if self.background_random_var.get():
            self.background_combo.config(state="disabled")
            CONFIGS.selected_background = None
        else:
            self.background_combo.config(state="readonly")
            background_value = self.background_combo.get()
            if background_value:
                background_index = int(background_value.split()[-1])
                CONFIGS.selected_background = background_index

        self.update_preview()

    def on_background_changed(self, event=None):
        """背景改变事件"""
        if not self.background_random_var.get():
            background_value = self.background_var.get()
            if background_value:
                background_index = int(background_value.split()[-1])
                CONFIGS.selected_background = background_index
                self.update_preview()

    def on_auto_paste_changed(self):
        """自动粘贴设置改变"""
        CONFIGS.config.AUTO_PASTE_IMAGE = self.auto_paste_var.get()

    def on_auto_send_changed(self):
        """自动发送设置改变"""
        CONFIGS.config.AUTO_SEND_IMAGE = self.auto_send_var.get()

    def on_sentiment_analyzer_status_changed(self, initialized: bool, enabled: bool, initializing: bool = False):
        """情感分析器状态变化回调"""
        def update_ui():
            if initializing:
                # 正在初始化，禁用复选框
                self.sentiment_checkbutton.config(state="disabled")
                self.sentiment_matching_var.set(True)  # 初始化期间保持选中状态
                self.update_status("正在初始化情感分析器...")
            else:
                # 初始化完成，启用复选框
                self.sentiment_checkbutton.config(state="normal")
                self.sentiment_matching_var.set(enabled)
                if enabled:
                    self.update_status("情感匹配功能已启用")
                else:
                    self.update_status("情感匹配功能已禁用")
                    if self.emotion_random_var.get():
                        CONFIGS.selected_emotion = None
                    else:
                        CONFIGS.selected_emotion = int(self.emotion_combo.get().split()[-1])
        
        # 在UI线程中执行更新
        self.root.after(0, update_ui)

    def update_sentiment_button_state(self):
        """更新情感匹配按钮状态"""
        # 根据当前状态设置复选框状态
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        if not sentiment_settings.get("display", False):
            return

        current_enabled = sentiment_settings.get("enabled", False)
        
        if self.core.sentiment_analyzer_status['initializing']:
            # 正在初始化，禁用复选框
            self.sentiment_checkbutton.config(state="disabled")
            self.sentiment_matching_var.set(True)
        elif self.core.sentiment_analyzer_status['initialized']:
            # 初始化成功，启用复选框
            self.sentiment_checkbutton.config(state="normal")
            self.sentiment_matching_var.set(current_enabled)
        else:
            # 未初始化，启用复选框但状态为未选中
            self.sentiment_checkbutton.config(state="normal")
            self.sentiment_matching_var.set(False)

    def on_sentiment_matching_clicked(self):
        """情感匹配按钮点击事件"""
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        current_enabled = sentiment_settings.get("enabled", False)
        
        if not current_enabled:
            # 如果当前未启用，尝试启用
            if not self.core.sentiment_analyzer_status['initialized']:
                # 如果未初始化，则开始初始化
                self.update_status("正在初始化情感分析器...")
        self.core.toggle_sentiment_matching()
    
    def on_sentiment_matching_changed(self):
        """情感匹配设置改变"""
        # 调用core的切换方法
        self.core.toggle_sentiment_matching()

    def generate_image(self):
        """生成图片"""
        if self.is_generating:
            return
        
        # 设置生成状态
        self.is_generating = True
        self.status_manager.update_status("正在生成图片...")

        def generate_in_thread():
            try:
                result = self.core.generate_image()
                self.root.after(0, lambda: self.on_generation_complete(result))
            except Exception as e:
                error_msg = f"生成失败: {str(e)}"
                print(error_msg)
                self.root.after(0, lambda: self.on_generation_complete(error_msg))
            finally:
                self.is_generating = False
        thread = threading.Thread(target=generate_in_thread, daemon=True, name="GenerateImg")
        thread.start()

    def on_generation_complete(self, result):
        """生成完成后的回调函数"""
        self.status_manager.update_status(result)
        self.update_preview()

    def update_status(self, message: str):
        """更新状态栏"""
        if hasattr(self,"status_manager"):
            self.status_manager.update_status(message)  

    def run(self):
        """运行 GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ManosabaGUI()
    app.run()