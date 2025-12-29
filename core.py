"""魔裁文本框核心逻辑"""
from config import CONFIGS
from clipboard_utils import ClipboardManager
from sentiment_analyzer import SentimentAnalyzer
from image_loader import get_enhanced_loader, generate_image_with_dll, set_dll_global_config, clear_cache, update_style_config, update_dll_gui_settings, draw_content_auto

import time
import copy
import random
import psutil
import threading
from pynput.keyboard import Key, Controller
from sys import platform
from PIL import Image
from typing import Dict, Any

if platform.startswith("win"):
    try:
        import win32gui
        import win32process
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32[/red]")
        raise

def _calculate_canvas_size():
    """根据样式配置计算画布大小"""
    ratio = CONFIGS.style.aspect_ratio

    # 固定宽度为2560，根据比例计算高度
    if ratio == "5:4":
        height = 2048
    elif ratio == "16:9":
        height = 1440
    else:  # "3:1" 或默认
        height = 854
    
    return (2560, height)

class ManosabaCore:
    """魔裁文本框核心类"""

    def __init__(self):
        # 初始化配置
        self.kbd_controller = Controller()
        self.clipboard_manager = ClipboardManager()
        
        #预览图当前的索引
        self._preview_emotion = -1
        self._preview_background = -1
        
        # 状态更新回调
        self.status_callback = None
        self.gui_callback = None

        # 初始化情感分析器 - 不在这里初始化，等待特定时机
        self.sentiment_analyzer = SentimentAnalyzer()
        self.sentiment_analyzer_status = {
            'initialized': False,
            'initializing': False,
            'current_config': {}
        }
        
        # 初始化DLL加载器
        self._dll_loader = get_enhanced_loader()
        self._assets_path = CONFIGS.config.ASSETS_PATH
        
        # 设置DLL全局配置
        set_dll_global_config(
            self._assets_path,
            min_image_ratio=0.2
        )
        
        # 更新DLL GUI设置
        update_dll_gui_settings(CONFIGS.gui_settings)
    
    def set_gui_callback(self, callback):
        """设置GUI回调函数，用于通知状态变化"""
        self.gui_callback = callback

    def _notify_gui_status_change(self, initialized: bool, enabled: bool = None, initializing: bool = False):
        """通知GUI状态变化"""
        if self.gui_callback:
            if enabled is None:
                # 如果没有指定enabled，则使用当前设置
                sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
                enabled = sentiment_settings.get("enabled", False) and initialized
            self.gui_callback(initialized, enabled, initializing)

    def _initialize_sentiment_analyzer_async(self):
        """异步初始化情感分析器"""
        def init_task():
            try:
                self.sentiment_analyzer_status['initializing'] = True
                self._notify_gui_status_change(False, False, True)
                
                sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
                if sentiment_settings.get("enabled", False):
                    client_type = sentiment_settings.get("ai_model", "ollama")
                    model_configs = sentiment_settings.get("model_configs", {})
                    config = model_configs.get(client_type, {})
                    
                    # 记录当前配置
                    self.sentiment_analyzer_status['current_config'] = {
                        'client_type': client_type,
                        'config': config.copy()
                    }
                    
                    success = self.sentiment_analyzer.initialize(client_type, config)
                    
                    if success:
                        self.update_status("情感分析器初始化完成，功能已启用")
                        self.sentiment_analyzer_status['initialized'] = True
                        # 通知GUI初始化成功
                        self._notify_gui_status_change(True, True, False)
                    else:
                        self.update_status("情感分析器初始化失败，功能已禁用")
                        self.sentiment_analyzer_status['initialized'] = False
                        # 通知GUI初始化失败，需要禁用情感匹配
                        self._notify_gui_status_change(False, False, False)
                        # 更新设置，禁用情感匹配
                        self._disable_sentiment_matching()
                else:
                    self.update_status("情感匹配功能未启用，跳过初始化")
                    self.sentiment_analyzer_status['initialized'] = False
                    self._notify_gui_status_change(False, False, False)
                    
            except Exception as e:
                self.update_status(f"情感分析器初始化失败: {e}，功能已禁用")
                self.sentiment_analyzer_status['initialized'] = False
                # 通知GUI初始化失败，需要禁用情感匹配
                self._notify_gui_status_change(False, False, False)
                # 更新设置，禁用情感匹配
                self._disable_sentiment_matching()
            finally:
                self.sentiment_analyzer_status['initializing'] = False
        
        # 在后台线程中初始化
        init_thread = threading.Thread(target=init_task, daemon=True)
        init_thread.start()    
    
    def toggle_sentiment_matching(self):
        """切换情感匹配状态"""
        # 如果正在初始化，不处理点击
        if self.sentiment_analyzer_status['initializing']:
            return
            
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        current_enabled = sentiment_settings.get("enabled", False)
        
        if not current_enabled:
            # 如果当前未启用，则启用并初始化
            CONFIGS.gui_settings["sentiment_matching"]["enabled"] = True
            CONFIGS.save_gui_settings()
            if not self.sentiment_analyzer_status['initialized']:
                # 如果未初始化，则开始初始化
                self.update_status("正在初始化情感分析器...")
                self._initialize_sentiment_analyzer_async()
            else:
                # 如果已初始化，直接启用
                self.update_status("已启用情感匹配功能")
                self._notify_gui_status_change(True, True, False)
        else:
            # 如果当前已启用，则禁用
            self.update_status("已禁用情感匹配功能")
            CONFIGS.gui_settings["sentiment_matching"]["enabled"] = False
            CONFIGS.save_gui_settings()
            self._notify_gui_status_change(self.sentiment_analyzer_status['initialized'], False, False)

    def _disable_sentiment_matching(self):
        """禁用情感匹配设置"""
        if "sentiment_matching" in CONFIGS.gui_settings:
            CONFIGS.gui_settings["sentiment_matching"]["enabled"] = False
        # 保存设置
        CONFIGS.save_gui_settings()
        self.update_status("情感匹配功能已禁用")

    def _reinitialize_sentiment_analyzer_if_needed(self):
        """检查配置是否有变化，如果有变化则重新初始化"""
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        if not sentiment_settings.get("enabled", False):
            # 如果功能被禁用，重置状态
            if self.sentiment_analyzer_status['initialized']:
                self.sentiment_analyzer_status['initialized'] = False
                self.update_status("情感匹配已禁用，重置分析器状态")
                self._notify_gui_status_change(False, False, False)
            return
        
        client_type = sentiment_settings.get("ai_model", "ollama")
        model_configs = sentiment_settings.get("model_configs", {})
        config = model_configs.get(client_type, {})
        
        new_config = {
            'client_type': client_type,
            'config': config.copy()
        }
        
        # 检查配置是否有变化
        if new_config != self.sentiment_analyzer_status['current_config']:
            self.update_status("AI配置已更改，重新初始化情感分析器")
            self.sentiment_analyzer_status['initialized'] = False
            self.sentiment_analyzer_status['current_config'] = new_config
            # 通知GUI开始重新初始化
            self._notify_gui_status_change(False, False, False)
            self._initialize_sentiment_analyzer_async()

    def test_ai_connection(self, client_type: str, config: Dict[str, Any]) -> bool:
        """测试AI连接 - 这会进行模型初始化"""
        try:
            # 使用临时分析器进行测试，不影响主分析器状态
            temp_analyzer = SentimentAnalyzer()
            success = temp_analyzer.initialize(client_type, config)
            if success:
                self.update_status(f"AI连接测试成功: {client_type}")
                # 如果测试成功，可以更新主分析器
                self.sentiment_analyzer.initialize(client_type, config)
                self.sentiment_analyzer_status['initialized'] = True
                # 通知GUI测试成功
                self._notify_gui_status_change(True, True)
            else:
                self.update_status(f"AI连接测试失败: {client_type}")
                self.sentiment_analyzer_status['initialized'] = False
                # 通知GUI测试失败
                self._notify_gui_status_change(False, False)
            return success
        except Exception as e:
            self.update_status(f"连接测试失败: {e}")
            self.sentiment_analyzer_status['initialized'] = False
            # 通知GUI测试失败
            self._notify_gui_status_change(False, False)
            return False

    def _get_emotion_by_sentiment(self, text: str) -> int:
        """根据文本情感获取对应的表情索引"""
        if not (text.strip() and self.sentiment_analyzer_status['initialized']):
            return None
        try:
            # 分析情感
            sentiment = self.sentiment_analyzer.analyze_sentiment(text)
            if not sentiment:
                return None
                
            current_character = CONFIGS.get_character()
            character_meta = CONFIGS.mahoshojo.get(current_character, {})
            
            # 查找对应情感的表情索引列表
            emotion_indices = character_meta.get(sentiment, [])
            if not emotion_indices:
                return None
                
            # 随机选择一个表情索引
            if emotion_indices:
                return random.choice(emotion_indices)
            else:
                return None
                
        except Exception as e:
            self.update_status(f"情感分析失败: {e}")
            return None

    def _update_emotion_by_sentiment(self, text: str) -> bool:
        """根据文本情感更新表情，返回是否成功更新"""
        # 检查情感分析器是否已初始化
        if not self.sentiment_analyzer_status['initialized']:
            self.update_status("情感分析器未初始化，跳过情感分析")
            return False
            
        emotion_index = self._get_emotion_by_sentiment(text)
        if emotion_index:
            CONFIGS.selected_emotion = emotion_index
            return True
        return False

    def switch_character(self, index: int) -> bool:
        """切换到指定索引的角色"""
        if 0 < index <= len(CONFIGS.character_list):
            CONFIGS.current_character_index = index
            CONFIGS.mahoshojo = CONFIGS.load_config("chara_meta")
            CONFIGS.character_list = list(CONFIGS.mahoshojo.keys())
            
            # 加载当前角色的配置到current_character变量  
            character_name = CONFIGS.get_character()
            CONFIGS.current_character = CONFIGS.mahoshojo.get(character_name, {})

            if CONFIGS.style.use_character_color:
                CONFIGS._update_bracket_color_from_character()
                update_style_config(CONFIGS.style)
            
            clear_cache()
            
            self.update_status(f"切换到角色: {character_name}")
            
            return True
        return False

    def _get_random_index(self, index_count: int, exclude_index: int = -1) -> int:
        """随机选择表情（避免连续相同）"""
        if exclude_index == -1:
            final_index = random.randint(1, index_count)
        else:
            # 避免连续相同表情
            available_indices = [i for i in range(1, index_count + 1) if i != exclude_index]
            final_index = (
                random.choice(available_indices)
                if available_indices
                else exclude_index
            )

        return final_index

    def _active_process_allowed(self) -> bool:
        """校验当前前台进程是否在白名单"""
        if not CONFIGS.process_whitelist:
            return True
        
        wl = {name.lower() for name in CONFIGS.process_whitelist}

        if platform.startswith("win"):
            try:
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    return False
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                name = psutil.Process(pid).name().lower()
                return name in wl
            except (psutil.Error, OSError):
                return False

        elif platform == "darwin":
            try:
                import subprocess

                result = subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to get name of first process whose frontmost is true',
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                name = result.stdout.strip().lower()
                return name in wl
            except subprocess.SubprocessError:
                return False

        else:
            # Linux 支持
            return True
    
    def set_status_callback(self, callback):
        """设置状态更新回调函数"""
        self.status_callback = callback

    def update_status(self, message: str):
        """更新状态（供外部调用）"""
        if self.status_callback:
            self.status_callback(message)

    def generate_preview(self) -> tuple:
        """生成预览图片和相关信息"""
        st = time.time()
        character_name = CONFIGS.get_character()
        emotion_count = CONFIGS.current_character["emotion_count"]

        # 确定表情和背景
        emotion_index = (
            self._get_random_index(emotion_count, exclude_index=self._preview_emotion)
            if CONFIGS.selected_emotion is None
            else CONFIGS.selected_emotion
        )
        background_index = (
            self._get_random_index(CONFIGS.background_count, exclude_index=self._preview_background)
            if CONFIGS.selected_background is None
            else CONFIGS.selected_background
        )

        # 保存预览使用的表情和背景
        self._preview_emotion = emotion_index
        self._preview_background = background_index

        # 生成预览图片（由C端缓存）
        try:
            # 使用缓存
            layer_cache = get_enhanced_loader().layer_cache
            if layer_cache:
                cp_components = layer_cache
                for component in cp_components:
                    if component.get("type") == "character":
                        if component.get("use_fixed_character", False):
                            character_name = component["character_name"]
                            emotion_index = component["emotion_index"]
                        else:
                            # 获取角色配置中的缩放
                            character_config = CONFIGS.mahoshojo.get(character_name, {})
                            offset = character_config.get("offset", (0, 0))

                            # 直接把角色缩放放进去
                            component["scale1"] = character_config.get("scale", 1.0)
                            
                            # 获取表情偏移（如果有）
                            emotion_offsets_X = character_config.get("offsetX", {})
                            emotion_offsets_Y = character_config.get("offsetY", {})
                            
                            component["offset_x1"] = emotion_offsets_X.get(str(emotion_index), 0) + offset[0]
                            component["offset_y1"] = emotion_offsets_Y.get(str(emotion_index), 0) + offset[1]
            else:
                # 准备组件数据
                components = CONFIGS.get_sorted_image_components()
                cp_components = copy.deepcopy(components)

                compress_layer = False
                # 构建组件列表，确保顺序正确
                for component in cp_components:
                    # 特殊处理
                    if component["type"] == "character":
                        if component.get("use_fixed_character", False):
                            character_name = component["character_name"]
                            emotion_index = component["emotion_index"]

                        # 获取角色配置中的缩放
                        character_config = CONFIGS.mahoshojo.get(character_name, {})
                        offset = character_config.get("offset", (0, 0))

                        component["scale1"] = character_config.get("scale", 1.0)
                        
                        # 获取表情偏移（如果有）
                        emotion_offsets_X = character_config.get("offsetX", {})
                        emotion_offsets_Y = character_config.get("offsetY", {})
                        
                        component["offset_x1"] = emotion_offsets_X.get(str(emotion_index), 0) + offset[0]
                        component["offset_y1"] = emotion_offsets_Y.get(str(emotion_index), 0) + offset[1]

                        if not component.get("use_fixed_character", False):
                            layer_cache.append(component)
                            compress_layer = False
                        else:
                            if not compress_layer:
                                layer_cache.append({"use_cache": True})
                                compress_layer = True

                    # 对于固定背景，需要特殊处理overlay
                    elif component["type"] == "background":
                        if not component.get("use_fixed_background", False):
                            layer_cache.append(component)
                            compress_layer = False
                        else:
                            if not compress_layer:
                                layer_cache.append({"use_cache": True})
                                compress_layer = True
                    elif component["type"] == "namebox":
                        component["textcfg"] = CONFIGS.text_configs_dict[character_name]
                        component["font_name"] = CONFIGS.current_character.get("font", "font3")
                        
                        if not compress_layer:
                                layer_cache.append({"use_cache": True})
                                compress_layer = True
                    else:
                        if not compress_layer:
                                layer_cache.append({"use_cache": True})
                                compress_layer = True
            
            # 使用DLL生成图像，C端会自动缓存
            preview_image = generate_image_with_dll(
                self._assets_path,
                _calculate_canvas_size(),
                cp_components,
                character_name,
                emotion_index,
                background_index
            )
            
            if preview_image:
                print(f"预览生成用时: {int((time.time()-st)*1000)}ms")
            else:
                print("预览图生成失败，使用默认图片")
                preview_image = Image.new("RGBA", _calculate_canvas_size(), (0, 0, 0, 0))
                
        except Exception as e:
            print(f"预览图生成出错: {e}")
            preview_image = Image.new("RGBA", _calculate_canvas_size(), color=(0, 0, 0, 0))

        # 构建预览信息 - 显示实际使用的索引值
        info = f"角色: {character_name}\n表情: {emotion_index:02d}\n背景: {background_index:02d}"
        return preview_image, info

    def generate_image(self) -> str:
        """生成并发送图片"""
        if not self._active_process_allowed():
            return "前台应用不在白名单内"

        base_msg=""

        # 开始计时
        start_time = time.time()
        print(f"[{int((time.time()-start_time)*1000)}] 开始生成图片")

        # 清空剪贴板
        self.clipboard_manager.clear_clipboard()

        time.sleep(0.005)

        # 获取剪切模式设置
        cut_settings = CONFIGS.gui_settings.get("cut_settings", {})
        cut_mode = cut_settings.get("cut_mode", "full")
        
        # 根据剪切模式执行不同的剪切操作
        if cut_mode == "直接剪切":
            # 手动剪切模式：不执行任何剪切操作，等待用户自行剪切
            self.kbd_controller.press(Key.ctrl)
            self.kbd_controller.press('x')
            self.kbd_controller.release('x')
            self.kbd_controller.release(Key.ctrl)
        else:
            # 执行剪切操作
            if cut_mode == "单行剪切":
                # 单行剪切模式：模拟 Shift+Home 选择当前行
                self.update_status("单行剪切模式：剪切当前行...")
                if platform.startswith("win"):
                    self.kbd_controller.press(Key.end)
                    self.kbd_controller.release(Key.end)
                    self.kbd_controller.press(Key.shift)
                    self.kbd_controller.press(Key.home)
                    self.kbd_controller.release(Key.home)
                    self.kbd_controller.release(Key.shift)
                    time.sleep(0.01)
                    self.kbd_controller.press(Key.ctrl)
                    self.kbd_controller.press('x')
                    self.kbd_controller.release('x')
                    self.kbd_controller.release(Key.ctrl)
                else:
                    self.kbd_controller.press(Key.shift)
                    self.kbd_controller.press(Key.home)
                    self.kbd_controller.release(Key.home)
                    self.kbd_controller.release(Key.shift)
                    time.sleep(0.01)
                    self.kbd_controller.press(Key.cmd)
                    self.kbd_controller.press('x')
                    self.kbd_controller.release('x')
                    self.kbd_controller.release(Key.cmd)
            else:
                # 全选剪切模式（默认）
                self.update_status("全选剪切模式：剪切全部内容...")
                if platform.startswith("win"):
                    self.kbd_controller.press(Key.ctrl)
                    self.kbd_controller.press('a')
                    self.kbd_controller.release('a')
                    self.kbd_controller.press('x')
                    self.kbd_controller.release('x')
                    self.kbd_controller.release(Key.ctrl)
                else:
                    self.kbd_controller.press(Key.cmd)
                    self.kbd_controller.press('a')
                    self.kbd_controller.release('a')
                    self.kbd_controller.press('x')
                    self.kbd_controller.release('x')
                    self.kbd_controller.release(Key.cmd)

        print(f"[{int((time.time()-start_time)*1000)}] 开始读取剪切板")
        deadline = time.time() + 2.5
        while time.time() < deadline:
            text, image = self.clipboard_manager.get_clipboard_all()
            if (text and text.strip()) or image is not None:
                print(f"[{int((time.time()-start_time)*1000)}] 剪切板内容获取完成")
                break
            time.sleep(0.005)
            
        print("读取到图片" if image is not None else "", "读取到文本" if text.strip() else "")
        
        # 情感匹配处理
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})

        if (sentiment_settings.get("enabled", False) and 
            self.sentiment_analyzer_status['initialized'] and
            text.strip()):
            
            self.update_status("正在分析文本情感...")
            emotion_updated = self._update_emotion_by_sentiment(text)
            
            if emotion_updated:
                self.update_status("情感分析完成，更新表情")
                print(f"[{int((time.time()-start_time)*1000)}] 情感分析完成")
                # 刷新预览以显示新的表情
                base_msg += f"情感: {self.sentiment_analyzer.selected_emotion}  "
                self.generate_preview()
                
            else:
                self.update_status("情感分析失败，使用默认表情")
                CONFIGS.selected_emotion = None
                print(f"[{int((time.time()-start_time)*1000)}] 情感分析失败")

        if text == "" and image is None:
            return "错误: 没有文本或图像"

        try:
            # 获取粘贴图像设置
            paste_settings = CONFIGS.style.paste_image_settings
            enabled = paste_settings.get("enabled", "off")
            
            # 初始化区域变量
            text_region = (
                CONFIGS.style.textbox_x,
                CONFIGS.style.textbox_y,
                CONFIGS.style.textbox_x + CONFIGS.style.textbox_width,
                CONFIGS.style.textbox_y + CONFIGS.style.textbox_height
            )
            
            # 根据粘贴模式决定图片区域
            image_region = None
            if enabled == "always":
                image_region = (
                    paste_settings.get("x", 0),
                    paste_settings.get("y", 0),
                    paste_settings.get("x", 0) + paste_settings.get("width", 300),
                    paste_settings.get("y", 0) + paste_settings.get("height", 200)
                )
            
            print(f"[{int((time.time()-start_time)*1000)}] 开始图像合成")
            
            bmp_bytes = draw_content_auto(
                text=text,
                content_image=image,
                # text_rect=text_region,
                # image_rect=image_region,
                # image_paste_mode=enabled
            )

            print(f"[{int((time.time()-start_time)*1000)}] 图片合成完成")

        except Exception as e:
            return f"生成图像失败: {e}"

        # 复制到剪贴板
        if not self.clipboard_manager.copy_image_to_clipboard(bmp_bytes):
            return "复制到剪贴板失败"
        
        print(f"[{int((time.time()-start_time)*1000)}] 图片复制到剪切板完成")

        # 等待剪贴板确认（最多等待2.5秒）
        wait = 0.01
        total = 0
        while total < 0.5:
            if self.clipboard_manager.has_image_in_clipboard():
                break
            time.sleep(wait)
            total += wait
            wait = min(wait * 1.5, 0.08)
        print(f"[{int((time.time()-start_time)*1000)}] 剪切板确认完成")

        # 自动粘贴和发送
        if CONFIGS.config.AUTO_PASTE_IMAGE:
            self.kbd_controller.press(Key.ctrl if platform != "darwin" else Key.cmd)
            self.kbd_controller.press("v")
            self.kbd_controller.release("v")
            self.kbd_controller.release(Key.ctrl if platform != "darwin" else Key.cmd)

            if not self._active_process_allowed():
                return "前台应用不在白名单内"
            if CONFIGS.config.AUTO_SEND_IMAGE:
                time.sleep(0.2)
                self.kbd_controller.press(Key.enter)
                self.kbd_controller.release(Key.enter)

                print(f"[{int((time.time()-start_time)*1000)}] 自动发送完成")
        
        # 构建状态消息
        base_msg += f"角色: {CONFIGS.get_character()}, 表情: {self._preview_emotion}, 背景: {self._preview_background}, 用时: {int((time.time() - start_time) * 1000)}ms"
        
        return base_msg