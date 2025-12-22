"""设置窗口模块"""

import tkinter as tk
from tkinter import ttk
import threading
from config import CONFIGS


class SettingsWindow:
    """设置窗口"""

    def __init__(self, parent, core, gui):
        self.parent = parent
        self.core = core
        self.gui = gui
        
        # 标记配置是否已修改
        self.settings_changed = False

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("450x550")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        # 添加图标
        from path_utils import set_window_icon
        set_window_icon(self.window)

        # 添加窗口关闭事件处理
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._setup_ui()

        # 确保界面状态正确
        self._setup_model_parameters()

    def _setup_ui(self):
        """设置UI界面"""
        # 创建Notebook用于标签页
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 常规设置标签页
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="常规设置")

        # 进程白名单标签页
        whitelist_frame = ttk.Frame(notebook, padding="10")
        notebook.add(whitelist_frame, text="进程白名单")

        # 快捷键设置标签页
        hotkey_frame = ttk.Frame(notebook, padding="10")
        notebook.add(hotkey_frame, text="快捷键设置")

        self._setup_general_tab(general_frame)
        self._setup_whitelist_tab(whitelist_frame)
        self._setup_hotkey_tab(hotkey_frame)

        # 按钮框架
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="保存", command=self._on_save).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="取消", command=self.window.destroy).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(button_frame, text="应用", command=self._on_apply).pack(
            side=tk.RIGHT, padx=5
        )
    
    def _setup_general_tab(self, parent):
        """设置常规设置标签页 - 添加滚动功能并修复滚动范围问题"""
        # 创建滚动容器
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        
        # 创建可滚动框架
        scrollable_frame = ttk.Frame(canvas)
        
        # 将 scrollable_frame 放入 canvas 中，使用 anchor="nw" 确保从左上角开始
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # 配置 scrollregion 和宽度
        def configure_scroll_region(event):
            # 只在 scrollable_frame 高度大于 canvas 时才设置 scrollregion
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def configure_frame_width(event):
            # 设置 scrollable_frame 宽度为 canvas 宽度减去滚动条宽度
            canvas_width = canvas.winfo_width()
            if canvas_width > scrollbar.winfo_width():
                # 减去滚动条宽度和一些边距
                frame_width = canvas_width - scrollbar.winfo_width() - 10
                canvas.itemconfig(canvas_frame, width=frame_width)
        
        # 绑定事件
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_frame_width)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局滚动组件
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加内部边距，防止内容紧贴边缘
        content_frame = ttk.Frame(scrollable_frame, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 预加载设置
        preloading_frame = ttk.LabelFrame(content_frame, text="预加载设置", padding="10")
        preloading_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 预加载角色图片
        preloading_settings = CONFIGS.gui_settings.get("preloading", {})
        
        self.preload_character_var = tk.BooleanVar(
            value=preloading_settings.get("preload_character", True)
        )
        preload_character_cb = ttk.Checkbutton(
            preloading_frame,
            text="预加载角色图片",
            variable=self.preload_character_var,
            command=lambda: setattr(self, 'settings_changed', True)
        )
        preload_character_cb.grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 20))
        
        # 预加载背景图片
        self.preload_background_var = tk.BooleanVar(
            value=preloading_settings.get("preload_background", True)
        )
        preload_background_cb = ttk.Checkbutton(
            preloading_frame,
            text="预加载背景图片",
            variable=self.preload_background_var,
            command=lambda: setattr(self, 'settings_changed', True)
        )
        preload_background_cb.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 预加载说明
        ttk.Label(preloading_frame, 
                text="注：预加载可以提高图片生成速度，但会增加内存使用", 
                font=("", 8), foreground="gray").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=2
        )
        
        # 配置列权重
        preloading_frame.columnconfigure(0, weight=1)
        preloading_frame.columnconfigure(1, weight=1)
        
        # 获取情感匹配设置
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        if sentiment_settings.get("display", False):
            # 情感匹配设置
            sentiment_frame = ttk.LabelFrame(content_frame, text="情感匹配设置", padding="10")
            sentiment_frame.pack(fill=tk.X, pady=5, padx=5)
        
            # AI模型选择
            ttk.Label(sentiment_frame, text="AI模型:").grid(
                row=1, column=0, sticky=tk.W, pady=5
            )
            
            # 动态获取模型列表
            model_names = list(CONFIGS.ai_models.keys())
            self.ai_model_var = tk.StringVar(
                value=sentiment_settings.get("ai_model", model_names[0] if model_names else "ollama")
            )
            ai_model_combo = ttk.Combobox(
                sentiment_frame,
                textvariable=self.ai_model_var,
                values=model_names,
                state="readonly"
            )
            ai_model_combo.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
            ai_model_combo.bind("<<ComboboxSelected>>", lambda e: [self._setup_model_parameters(), setattr(self, 'settings_changed', True)])
        
            # 连接测试按钮
            self.test_btn = ttk.Button(
                sentiment_frame,
                text="测试连接",
                command=self._test_ai_connection
            )
            self.test_btn.grid(row=1, column=2, sticky=tk.E, pady=5, padx=5)
        
            # 模型参数框架 - 显示所有参数
            self.params_frame = ttk.Frame(sentiment_frame)
            self.params_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=5)
            
            # 初始化参数显示
            self._setup_model_parameters()
        
            # 情感匹配说明
            ttk.Label(sentiment_frame, 
                    text="注：在主界面点击情感匹配以进行连接，点击测试连接按钮也行", 
                    font=("", 8), foreground="gray").grid(
                row=0, column=0, columnspan=3, sticky=tk.W, pady=2
            )
        
            # 配置列权重
            sentiment_frame.columnconfigure(1, weight=1)
            sentiment_frame.columnconfigure(2, weight=0)  # 按钮列不扩展
        
        # 图像压缩设置
        compression_frame = ttk.LabelFrame(content_frame, text="图像压缩设置", padding="10")
        compression_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # 像素减少压缩
        self.pixel_reduction_var = tk.BooleanVar(
            value=CONFIGS.gui_settings.get("image_compression", {}).get("pixel_reduction_enabled", False)
        )
        pixel_reduction_cb = ttk.Checkbutton(
            compression_frame,
            text="启用像素削减压缩",
            variable=self.pixel_reduction_var,
            command=lambda: setattr(self, 'settings_changed', True)
        )
        pixel_reduction_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 像素减少比例滑条
        ttk.Label(compression_frame, text="像素削减比例:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        
        pixel_frame = ttk.Frame(compression_frame)
        pixel_frame.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=5)
        
        self.pixel_reduction_ratio_var = tk.IntVar(
            value=CONFIGS.gui_settings.get("image_compression", {}).get("pixel_reduction_ratio", 50)
        )
        pixel_scale = ttk.Scale(
            pixel_frame,
            from_=10,
            to=90,
            variable=self.pixel_reduction_ratio_var,
            orient=tk.HORIZONTAL
        )
        pixel_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        pixel_scale.bind("<ButtonRelease-1>", lambda e: setattr(self, 'settings_changed', True))
        
        self.pixel_value_label = ttk.Label(pixel_frame, text=f"{self.pixel_reduction_ratio_var.get()}%")
        self.pixel_value_label.pack(side=tk.LEFT, padx=5)
        
        # 绑定变量变化更新标签
        self.pixel_reduction_ratio_var.trace_add("write", self._update_pixel_label)
        
        # 压缩说明
        ttk.Label(compression_frame, 
                text="注：压缩质量影响PNG输出质量，像素减少通过降低BMP图像分辨率来减小文件大小", 
                font=("", 8), foreground="gray").grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=2
        )
        
        # 配置列权重，使内容可以水平扩展
        if sentiment_settings.get("display", False):
            compression_frame.columnconfigure(1, weight=1)

    def _setup_hotkey_tab(self, parent):
        """设置快捷键标签页"""
        # 创建滚动框架
        canvas = tk.Canvas(parent, highlightthickness=0, background='#f0f0f0')
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # 创建窗口并设置合适的宽度
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # 更新函数确保框架宽度正确
        def update_scrollable_frame_width(event=None):
            # 获取canvas当前宽度并减去滚动条宽度
            canvas_width = canvas.winfo_width()
            if canvas_width > 10:  # 确保有有效宽度
                canvas.itemconfig(canvas_frame, width=canvas_width - 10)
        
        canvas.bind("<Configure>", update_scrollable_frame_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始更新一次宽度
        parent.after(100, update_scrollable_frame_width)
        
        # 加载快捷键
        hotkeys = CONFIGS.keymap
        
        # 生成快捷键放在第一个
        generate_frame = ttk.LabelFrame(scrollable_frame, text="生成控制", padding="10")
        generate_frame.pack(fill=tk.X, pady=5)

        self._create_hotkey_editable_row(
            generate_frame,
            "生成图片",
            "start_generate",
            hotkeys.get("start_generate", "ctrl+e"),
            0,
        )

        # 角色切换快捷键
        char_frame = ttk.LabelFrame(scrollable_frame, text="角色切换", padding="10")
        char_frame.pack(fill=tk.X, pady=5)

        self._create_hotkey_editable_row(
            char_frame,
            "向前切换角色",
            "prev_character",
            hotkeys.get("prev_character", "ctrl+j"),
            0,
        )
        self._create_hotkey_editable_row(
            char_frame,
            "向后切换角色",
            "next_character",
            hotkeys.get("next_character", "ctrl+l"),
            1,
        )

        # 表情切换快捷键 - 新增
        emotion_frame = ttk.LabelFrame(scrollable_frame, text="表情切换", padding="10")
        emotion_frame.pack(fill=tk.X, pady=5)

        self._create_hotkey_editable_row(
            emotion_frame,
            "向前切换表情",
            "prev_emotion",
            hotkeys.get("prev_emotion", "ctrl+u"),
            0,
        )
        self._create_hotkey_editable_row(
            emotion_frame,
            "向后切换表情",
            "next_emotion",
            hotkeys.get("next_emotion", "ctrl+o"),
            1,
        )

        # 背景切换快捷键
        bg_frame = ttk.LabelFrame(scrollable_frame, text="背景切换", padding="10")
        bg_frame.pack(fill=tk.X, pady=5)

        self._create_hotkey_editable_row(
            bg_frame,
            "向前切换背景",
            "prev_background",
            hotkeys.get("prev_background", "ctrl+i"),
            0,
        )
        self._create_hotkey_editable_row(
            bg_frame,
            "向后切换背景",
            "next_background",
            hotkeys.get("next_background", "ctrl+k"),
            1,
        )

        # 控制快捷键
        control_frame = ttk.LabelFrame(scrollable_frame, text="控制", padding="10")
        control_frame.pack(fill=tk.X, pady=5)

        self._create_hotkey_editable_row(
            control_frame,
            "继续/停止监听",
            "toggle_listener",
            hotkeys.get("toggle_listener", "alt+ctrl+p"),
            0,
        )

        # 角色快速选择快捷键
        quick_char_frame = ttk.LabelFrame(
            scrollable_frame, text="角色快速选择", padding="10"
        )
        quick_char_frame.pack(fill=tk.X, pady=5)

        # 获取所有角色选项
        character_options = [""]  # 空选项
        for char_id in CONFIGS.character_list:
            full_name = CONFIGS.get_character(char_id, full_name=True)
            character_options.append(f"{full_name} ({char_id})")

        quick_chars = CONFIGS.gui_settings.get("quick_characters", {})

        for i in range(1, 7):
            # 获取当前设置的角色
            current_char = quick_chars.get(f"character_{i}", "")
            if current_char and current_char in CONFIGS.character_list:
                current_display = f"{CONFIGS.get_character(current_char, full_name=True)} ({current_char})"
            else:
                current_display = ""

            self._create_character_hotkey_row(
                quick_char_frame,
                f"快捷键 {i}",
                f"character_{i}",
                current_display,
                character_options,
                i - 1,
            )

    def _create_hotkey_editable_row(self, parent, label, key, hotkey_value, row):
        """创建可编辑的快捷键显示行"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0, 10))

        # 创建包含Entry和Button的Frame，实现右对齐
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # 快捷键显示（只读）
        hotkey_var = tk.StringVar(value=hotkey_value)
        setattr(self, f"{key}_hotkey_var", hotkey_var)

        entry = ttk.Entry(control_frame, textvariable=hotkey_var, state="readonly")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 添加配置按钮 - 保持右对齐
        config_btn = ttk.Button(
            control_frame, 
            text="配置", 
            width=6,
            command=lambda k=key: self._start_key_config(k)
        )
        config_btn.pack(side=tk.RIGHT)
        
        # 配置列权重，使Entry可以扩展填充
        parent.columnconfigure(1, weight=1)

    def _create_character_hotkey_row(
        self, parent, label, key, current_char, character_options, row
    ):
        """创建角色快捷键设置行"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2, padx=(0, 10))

        # 创建包含Combobox的Frame
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # 角色选择下拉框 - 修改为填充可用空间
        char_var = tk.StringVar(value=current_char)
        setattr(self, f"{key}_char_var", char_var)

        char_combo = ttk.Combobox(
            control_frame,
            textvariable=char_var,
            values=character_options,
            state="readonly",
        )
        char_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        char_combo.bind("<<ComboboxSelected>>", lambda e: setattr(self, 'settings_changed', True))

        # 配置列权重，使Combobox可以扩展填充
        parent.columnconfigure(1, weight=1)
        
    def _setup_whitelist_tab(self, parent):
        """设置进程白名单标签页"""
        # 创建滚动文本框
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        # 添加说明
        ttk.Label(frame, text="每行一个进程名，不包含.exe后缀").pack(anchor=tk.W, pady=5)

        # 文本框
        self.whitelist_text = tk.Text(frame, wrap=tk.WORD, width=50, height=20)
        self.whitelist_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # 从配置文件重新加载白名单内容
        # current_whitelist = CONFIGS.load_config("process_whitelist")
        self.whitelist_text.insert('1.0', '\n'.join(CONFIGS.process_whitelist))
        self.whitelist_text.edit_modified(False)  # 重置修改标志

    def _setup_model_parameters(self, event=None):
        """设置模型参数显示"""
        if not CONFIGS.gui_settings["sentiment_matching"].get("display", False):
            return

        # 清除现有参数控件
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        selected_model = self.ai_model_var.get()
        if selected_model not in CONFIGS.ai_models:
            return
            
        model_config = CONFIGS.ai_models[selected_model]
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        model_settings = sentiment_settings.get("model_configs", {}).get(selected_model, {})
        
        # 创建参数输入控件
        row = 0
        
        # API URL
        ttk.Label(self.params_frame, text="API地址:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.api_url_var = tk.StringVar(
            value=model_settings.get("base_url", model_config.get("base_url", ""))
        )
        api_url_entry = ttk.Entry(
            self.params_frame,
            textvariable=self.api_url_var,
            width=40
        )
        api_url_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=5)
        api_url_entry.bind("<KeyRelease>", lambda e: setattr(self, 'settings_changed', True))
        row += 1
        
        # API Key
        ttk.Label(self.params_frame, text="API密钥:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.api_key_var = tk.StringVar(
            value=model_settings.get("api_key", model_config.get("api_key", ""))
        )
        api_key_entry = ttk.Entry(
            self.params_frame,
            textvariable=self.api_key_var,
            width=40,
            show="*"
        )
        api_key_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=5)
        api_key_entry.bind("<KeyRelease>", lambda e: setattr(self, 'settings_changed', True))
        row += 1
        
        # 模型名称
        ttk.Label(self.params_frame, text="模型名称:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.model_name_var = tk.StringVar(
            value=model_settings.get("model", model_config.get("model", ""))
        )
        model_name_entry = ttk.Entry(
            self.params_frame,
            textvariable=self.model_name_var,
            width=40
        )
        model_name_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=5)
        model_name_entry.bind("<KeyRelease>", lambda e: setattr(self, 'settings_changed', True))
        row += 1
        
        # 模型描述
        description = model_config.get("description", "")
        if description:
            ttk.Label(self.params_frame, text="描述:", font=("", 8)).grid(
                row=row, column=0, sticky=tk.W, pady=2
            )
            ttk.Label(self.params_frame, text=description, font=("", 8), foreground="gray").grid(
                row=row, column=1, columnspan=2, sticky=tk.W, pady=2, padx=5
            )
        
        self.params_frame.columnconfigure(1, weight=1)

    def _start_key_config(self, key):
        """开始配置快捷键"""
        # 获取对应的变量
        hotkey_var = getattr(self, f"{key}_hotkey_var")
        ori_key = hotkey_var.get()

        # 设置初始文本
        hotkey_var.set("请按下按键组合...")
        
        # 启动监听线程
        self._current_config_key = key
        self._config_thread_stop = False
        self._config_thread = threading.Thread(
            target=self._key_config_listener,
            args=(key, ori_key),
            daemon=True,
            name="HotkeyCfgListener"
        )
        self._config_thread.start()
        
    def _key_config_listener(self, key, ori_key):
        """按键配置监听线程 - 使用 pynput"""
        from pynput import keyboard as pynput_kb
        
        hotkey_var = getattr(self, f"{key}_hotkey_var")
        
        # 存储按键组合
        key_combo = []
        listener = None
        should_stop = False
        
        def on_press(key_obj):
            nonlocal should_stop
            try:
                should_stop = False
                
                # 处理特殊键
                if hasattr(key_obj, 'name'):
                    # 修饰键处理
                    if key_obj.name in ['ctrl_l', 'ctrl_r', 'ctrl']:
                        key_str = '<ctrl>'
                    elif key_obj.name in ['alt_l', 'alt_r', 'alt']:
                        key_str = '<alt>'
                    elif key_obj.name in ['shift_l', 'shift_r', 'shift']:
                        key_str = '<shift>'
                    elif key_obj.name in ['cmd_l', 'cmd_r', 'cmd', 'win', 'windows']:
                        key_str = '<cmd>' if CONFIGS.platform == 'darwin' else '<win>'
                    elif key_obj.name.startswith('f') and key_obj.name[1:].isdigit():
                        key_str = f'<{key_obj.name}>'
                    elif key_obj.name in ['space', 'enter', 'esc', 'tab', 'backspace', 'delete', 'insert',
                                        'pageup', 'pagedown', 'home', 'end', 'left', 'right', 'up', 'down']:
                        key_str = f'<{key_obj.name}>'
                    else:
                        # 对于字母键，直接使用名称
                        if key_obj.name.isalpha() and len(key_obj.name) == 1:
                            key_str = key_obj.name.lower()
                        else:
                            key_str = key_obj.name
                else:
                    # 处理普通字符键 - 修复Ctrl+数字的问题
                    if hasattr(key_obj, 'char') and key_obj.char:
                        char_val = key_obj.char
                        if isinstance(char_val, str) and len(char_val) == 1:
                            code = ord(char_val)
                            # Ctrl+A 到 Ctrl+Z 对应 1-26
                            if 1 <= code <= 26:
                                # 转换为对应字母
                                key_str = chr(code - 1 + ord('a'))
                            # 修复：Ctrl+0 到 Ctrl+9 对应 0-9 (ASCII 0-9对应Ctrl+@到Ctrl+])
                            elif code == 0:  # Ctrl+@ 或 Ctrl+`
                                key_str = '0'
                            elif code < 32:  # 其他控制字符
                                # 检查是否是数字控制字符 (Ctrl+1 到 Ctrl+9 对应 ASCII 1-9)
                                if 1 <= code <= 9:
                                    key_str = str(code)
                                elif code == 27:  # Ctrl+[
                                    key_str = '['
                                elif code == 28:  # Ctrl+\
                                    key_str = '\\'
                                elif code == 29:  # Ctrl+]
                                    key_str = ']'
                                elif code == 30:  # Ctrl+^
                                    key_str = '^'
                                elif code == 31:  # Ctrl+_
                                    key_str = '_'
                                else:
                                    key_str = None
                            # 修复：Ctrl+数字键的直接映射
                            elif 48 <= code <= 57:  # 数字 0-9
                                # 检查是否按下了Ctrl键（通过key_combo中是否已有<ctrl>）
                                if '<ctrl>' in key_combo:
                                    # 直接使用数字字符
                                    key_str = char_val
                                else:
                                    key_str = char_val.lower() if char_val.isalpha() else char_val
                            elif code >= 32:  # 可打印字符
                                key_str = char_val.lower() if char_val.isalpha() else char_val
                            else:
                                key_str = None
                        else:
                            key_str = char_val
                    else:
                        # 没有字符属性，尝试获取其他表示
                        try:
                            # 尝试获取虚拟键码
                            if hasattr(key_obj, 'vk'):
                                vk = key_obj.vk
                                # 检查是否是数字键 (VK_0 到 VK_9)
                                if 48 <= vk <= 57:  # VK_0 到 VK_9
                                    # 检查是否按下了Ctrl键
                                    if '<ctrl>' in key_combo:
                                        key_str = str(vk - 48)  # 转换为数字字符
                                    else:
                                        key_str = str(vk - 48)
                                elif 65 <= vk <= 90:  # VK_A 到 VK_Z
                                    key_str = chr(vk).lower()
                                else:
                                    key_str = str(key_obj)
                            else:
                                key_str = str(key_obj)
                        except:
                            key_str = str(key_obj)
                
                # 去重并添加到组合
                if key_str and key_str not in key_combo:
                    key_combo.append(key_str)
                    
                    # 更新显示
                    def update_display():
                        # 确保修饰键在前面
                        modifiers = [k for k in key_combo if k.startswith('<')]
                        regular_keys = [k for k in key_combo if not k.startswith('<')]
                        final_combo = modifiers + regular_keys
                        display_str = '+'.join(final_combo)
                        hotkey_var.set(display_str)
                    
                    self.window.after(0, update_display)
                    
            except Exception as e:
                print(f"按键处理错误: {e}")
        
        def on_release(key_obj):
            nonlocal should_stop
            # 标记需要停止，但不立即停止
            should_stop = True
            return True  # 继续监听
        
        # 设置初始文本
        def set_initial_text():
            hotkey_var.set("请输入按键...")
        self.window.after(0, set_initial_text)
        
        # 启动监听器
        listener = pynput_kb.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        
        import time
        start_time = time.time()
        
        while listener.running and (time.time() - start_time) < 5:  # 最多等待5秒
            time.sleep(0.05)
            
            if should_stop:
                print("结束监听")
                break
        
        # 如果监听器还在运行，停止它
        if listener and listener.running:
            listener.stop()
        
        # 如果没有按键被按下，恢复原来的值
        if not key_combo:
            def restore_original():
                hotkey_var.set(ori_key)
            self.window.after(0, restore_original)

    def _test_ai_connection(self):
        """测试AI连接 - 这会触发模型初始化"""
        selected_model = self.ai_model_var.get()
        if selected_model not in CONFIGS.ai_models:
            return
            
        # 获取当前配置
        config = {
            "base_url": self.api_url_var.get(),
            "api_key": self.api_key_var.get(),
            "model": self.model_name_var.get()
        }
        
        # 禁用按钮
        self.test_btn.config(state="disabled")
        self.test_btn.config(text="测试中...")
        
        def test_in_thread():
            success = self.core.test_ai_connection(selected_model, config)
            self.window.after(0, lambda: self._on_connection_test_complete(success))
        
        threading.Thread(target=test_in_thread, daemon=True,name="TestAiConn").start()

    def _on_connection_test_complete(self, success: bool):
        """连接测试完成回调"""
        self.test_btn.config(state="normal")
        if success:
            self.test_btn.config(text="连接成功")
            # 测试成功时，更新当前配置
            if "model_configs" not in CONFIGS.gui_settings["sentiment_matching"]:
                CONFIGS.gui_settings["sentiment_matching"]["model_configs"] = {}

            # 2秒后恢复文本
            self.window.after(2000, lambda: self.test_btn.config(text="测试连接"))
        else:
            self.test_btn.config(text="连接失败")
            # 连接失败时，禁用情感匹配
            # 2秒后恢复文本
            self.window.after(2000, lambda: self.test_btn.config(text="测试连接"))

    def _update_pixel_label(self, *args):
        """更新像素减少比例标签"""
        self.pixel_value_label.config(text=f"{self.pixel_reduction_ratio_var.get()}%")
        self.settings_changed = True

    def _collect_settings(self):
        """收集所有设置到字典"""
        settings = {
            "preloading": {
                "preload_character": self.preload_character_var.get(),
                "preload_background": self.preload_background_var.get()
            },
            "image_compression": {
                "pixel_reduction_enabled": self.pixel_reduction_var.get(),
                "pixel_reduction_ratio": self.pixel_reduction_ratio_var.get()
            },
            "quick_characters": self._collect_quick_characters(),
        }

        # 如果显示情感匹配设置
        if CONFIGS.gui_settings["sentiment_matching"].get("display", False):
            selected_model = self.ai_model_var.get()
            settings["sentiment_matching"] = {
                "display": True,
                "enabled": CONFIGS.gui_settings["sentiment_matching"].get("enabled", False),
                "ai_model": selected_model,
                "model_configs": {
                    selected_model: {
                        "base_url": self.api_url_var.get(),
                        "api_key": self.api_key_var.get(),
                        "model": self.model_name_var.get()
                    }
                }
            }
        else:
            settings["sentiment_matching"] = CONFIGS.gui_settings.get("sentiment_matching", {})
        
        return settings

    def _collect_quick_characters(self):
        """收集快速角色设置"""
        quick_characters = {}
        for i in range(1, 7):
            char_var = getattr(self, f"character_{i}_char_var")
            char_display = char_var.get()
            if char_display and "(" in char_display and ")" in char_display:
                char_id = char_display.split("(")[-1].rstrip(")")
                quick_characters[f"character_{i}"] = char_id
            else:
                quick_characters[f"character_{i}"] = ""
        return quick_characters

    def _collect_hotkeys(self):
        """收集热键设置"""
        new_hotkeys = {}
        
        # 收集普通快捷键
        for key in ['start_generate', 'next_character', 'prev_character', 'next_emotion', 'prev_emotion', 
                    'next_background', 'prev_background', 'toggle_listener']:
            var_name = f"{key}_hotkey_var"
            if hasattr(self, var_name):
                hotkey_var = getattr(self, var_name)
                hotkey_value = hotkey_var.get()
                # 如果用户输入了"请输入按键"，跳过保存
                if hotkey_value != "请输入按键" and hotkey_value != "请按下按键组合...":
                    new_hotkeys[key] = hotkey_value
        
        return new_hotkeys

    def _collect_whitelist(self):
        """收集进程白名单设置"""
        text_content = self.whitelist_text.get('1.0', tk.END).strip()
        processes = [p.strip() for p in text_content.split('\n') if p.strip()]
        return processes

    def _on_save(self):
        """保存设置并关闭窗口"""
        self._on_apply()
        self.window.destroy()

    def _on_apply(self):
        """应用设置但不关闭窗口"""
        # 检查并保存常规设置
        if self.settings_changed:
            self.settings_changed = False
            new_settings = self._collect_settings()
            
            # 获取最新的预加载设置
            old_PS = CONFIGS.gui_settings.get("preloading", {}).copy()
            new_PS = new_settings.get("preloading", {})

            # 检查预加载设置是否从关闭变为开启（更精确的比较）
            old_preload_char = old_PS.get("preload_character", True)
            new_preload_char = new_PS.get("preload_character", True)
            
            old_preload_bg = old_PS.get("preload_background", True)
            new_preload_bg = new_PS.get("preload_background", True)
                        
            # 更新CONFIGS
            CONFIGS.gui_settings.update(new_settings)
            
            # 保存到文件
            if CONFIGS.save_gui_settings():
                print("配置更新")
                # 如果角色预加载从关闭变为开启
                if (old_preload_char != new_preload_char and new_preload_char):
                    # 触发预加载当前角色
                    current_character = CONFIGS.get_character()
                    self.gui.core.preload_manager.submit_preload_task('character', character_name=current_character)
                
                # 如果背景预加载从关闭变为开启
                if (old_preload_bg != new_preload_bg and new_preload_bg):
                    self.gui.core.preload_manager.submit_preload_task('background')
                
            # 应用设置时检查是否需要重新初始化AI模型
            self.core._reinitialize_sentiment_analyzer_if_needed()
            
        if CONFIGS.save_process_whitelist(self._collect_whitelist()):
            print("白名单更新")
            CONFIGS.process_whitelist=CONFIGS.load_config("process_whitelist")
        if CONFIGS.save_keymap(self._collect_hotkeys()):
            print("热键更新")
            CONFIGS.keymap = CONFIGS.load_config("keymap")

    def _on_close(self):
        """处理窗口关闭事件"""
        # 停止按键配置监听线程（如果正在运行）
        if hasattr(self, '_config_thread') and self._config_thread and self._config_thread.is_alive():
            self._config_thread_stop = True
        
        # 销毁窗口
        self.window.destroy()