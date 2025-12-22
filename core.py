"""魔裁文本框核心逻辑"""
from config import CONFIGS
from clipboard_utils import ClipboardManager
from sentiment_analyzer import SentimentAnalyzer

from load_utils import clear_cache, load_background_safe, load_character_safe, get_preload_manager, load_image_cached, get_component_cache_manager
from path_utils import get_resource_path, get_available_fonts
from draw_utils import draw_content_auto, load_font_cached

import os
import time
import random
import psutil
import threading
from pynput.keyboard import Key, Controller
from sys import platform
from PIL import Image, ImageDraw
from typing import Dict, Any, Tuple

if platform.startswith("win"):
    try:
        import win32gui
        import win32process
    except ImportError:
        print("[red]请先安装 Windows 运行库: pip install pywin32[/red]")
        raise

class ManosabaCore:
    """魔裁文本框核心类"""

    def __init__(self):
        # 初始化配置
        self.kbd_controller = Controller()
        self.clipboard_manager = ClipboardManager()
        
        #预览图当前的索引
        self._preview_emotion = -1
        self._preview_background = -1
        self._current_base_image = None  # 当前预览的基础图片（用于快速生成）
        
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
        
        # 初始化预加载管理器
        self.preload_manager = get_preload_manager()
        self.preload_manager.set_update_callback(self.update_status)
        
        # 获取组件缓存管理器
        self.component_cache_manager = get_component_cache_manager()
        
        # 程序启动时开始预加载图片
        self.update_status("正在预加载图片到缓存...")
        
        # 获取预加载设置
        preloading_settings = CONFIGS.gui_settings.get("preloading", {})
        preload_character = preloading_settings.get("preload_character", True)
        preload_background = preloading_settings.get("preload_background", True)
        
        # 根据设置决定是否预加载
        if preload_character:
            # 只预加载当前角色的图片
            current_character = CONFIGS.get_character()
            self.preload_manager.submit_preload_task('character', character_name=current_character)
            self.update_status(f"开始预加载角色: {current_character}")
        else:
            self.update_status("角色图片预加载已禁用")
        
        if preload_background:
            # 预加载背景图片
            self.preload_manager.submit_preload_task('background')
            self.update_status("开始预加载背景图片")
        else:
            self.update_status("背景图片预加载已禁用")
    
        # 程序启动时检查是否需要初始化
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        if sentiment_settings.get("enabled", False):
            self.update_status("检测到启用情感匹配，正在初始化...")
            self._initialize_sentiment_analyzer_async()
        else:
            self.update_status("情感匹配功能未启用")
            self._notify_gui_status_change(False, False)

    def _calculate_canvas_size(self):
        """根据样式配置计算画布大小"""
        ratio = CONFIGS.style.aspect_ratio

        # 固定宽度为2560，根据比例计算高度
        if ratio == "5:4":
            # 5:4 = 2560 : x, x = 2560 * 4 / 5 = 2048
            height = 2048
        elif ratio == "16:9":
            # 16:9 = 2560 : x, x = 2560 * 9 / 16 = 1440
            height = 1440
        else:  # "3:1" 或默认
            # 3:1 = 2560 : x, x = 2560 * 1 / 3 ≈ 853.33
            height = 854
        
        return 2560, height
    
    def _calculate_component_position(self, canvas_width: int, canvas_height: int, 
                                     component_width: int, component_height: int, 
                                     align: str, offset_x: int = 0, offset_y: int = 0) -> Tuple[int, int]:
        """
        统一的组件位置计算函数
        
        Args:
            canvas_width: 画布宽度
            canvas_height: 画布高度
            component_width: 组件宽度
            component_height: 组件高度
            align: 对齐方式 (top-left, top-center, top-right, middle-left, middle-center, middle-right, 
                  bottom-left, bottom-center, bottom-right)
            offset_x: X轴偏移
            offset_y: Y轴偏移
            
        Returns:
            (x, y) 组件左上角坐标
        """
        # 水平对齐计算
        if align.endswith("-left"):
            x = 0
        elif align.endswith("-center"):
            x = (canvas_width - component_width) // 2
        elif align.endswith("-right"):
            x = canvas_width - component_width
        else:
            x = 0  # 默认左对齐
        
        # 垂直对齐计算
        if align.startswith("top-"):
            y = 0
        elif align.startswith("middle-"):
            y = (canvas_height - component_height) // 2
        elif align.startswith("bottom-"):
            y = canvas_height - component_height
        else:
            y = 0  # 默认顶部对齐
        
        # 应用偏移
        x += offset_x
        y += offset_y
        
        return x, y
    
    def _generate_base_image_with_text(
        self, character_name: str, background_index: int, emotion_index: int
    ) -> Image.Image:
        """生成带角色文字的基础图片（使用样式配置）"""
        start_time = time.time()

        # 1. 加载预裁剪的背景图
        background = load_background_safe(f"c{background_index}").convert("RGBA")

        print(f"\n背景加载用时 {int((time.time()-start_time)*1000)}")
        start_time = time.time()

        # 2. 创建画布
        canvas = background

        print(f"背景处理用时 {int((time.time()-start_time)*1000)}")
        start_time=time.time()

        # 3. 获取排序后的组件列表
        sorted_components = CONFIGS.get_sorted_image_components()
        
        # 4. 按图层顺序绘制所有组件
        for component in sorted_components:
            if not component.get("enabled", True):
                continue
                
            component_type = component.get("type")
            
            if component_type == "character":
                # 绘制角色
                self._draw_character_component(canvas, component, character_name, emotion_index)
            elif component_type == "textbox":
                # 绘制文本框遮罩
                canvas = self._draw_textbox_component(canvas, component)
            elif component_type == "namebox":
                # 绘制名称框
                self._draw_namebox_component(canvas, component, character_name)
            elif component_type == "extra":
                # 绘制额外组件
                canvas = self._draw_extra_component(canvas, component)
        
            print(f"{component_type}用时 {int((time.time()-start_time)*1000)}")
            start_time=time.time()
        return canvas

    def _draw_character_component(self, canvas, component, character_name, emotion_index):
        """绘制角色组件"""
        # 检查是否启用
        if not component.get("enabled", True):
            return
            
        # 加载预处理的角色图片
        overlay = load_character_safe(character_name, emotion_index)
        
        # 计算粘贴位置（左下角对齐）
        paste_x = 0 + component.get("offset_x", 0) + CONFIGS.current_character.get("offset", (0, 0))[0] + CONFIGS.current_character.get(f"offsetX", {}).get(f"{emotion_index}", 0)
        paste_y = canvas.height - overlay.height + component.get("offset_y", 0) + CONFIGS.current_character.get("offset", (0, 0))[1] + CONFIGS.current_character.get(f"offsetY", {}).get(f"{emotion_index}", 0)
        
        canvas.paste(overlay, (paste_x, paste_y), overlay)

    def _draw_textbox_component(self, canvas, component):
        """绘制文本框组件（使用缓存）"""
        overlay_file = component.get("overlay", "")
        if not overlay_file:
            return canvas
        
        # 尝试从缓存获取
        scale = component.get("scale", 1.0)
        overlay_layer = self.component_cache_manager.get_overlay_cache(overlay_file, scale)
        
        if overlay_layer is None:
            overlay_path = get_resource_path(os.path.join("assets", "shader", overlay_file))
            if not os.path.exists(overlay_path):
                return canvas
            
            textbox = load_image_cached(overlay_path)
            
            # 应用缩放
            if scale != 1.0:
                original_width, original_height = textbox.size
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                textbox = textbox.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 创建透明图层进行alpha混合
            overlay_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            
            # 计算粘贴位置
            align = component.get("align", "bottom-center")
            offset_x = component.get("offset_x", 0)
            offset_y = component.get("offset_y", 0)
            canvas_width, canvas_height = canvas.size
            
            # 使用统一位置计算函数
            paste_x, paste_y = self._calculate_component_position(
                canvas_width, canvas_height,
                textbox.width, textbox.height,
                align,
                offset_x,
                offset_y
            )
            
            overlay_layer.paste(textbox, (paste_x, paste_y), textbox)

            # 缓存处理后的图片
            self.component_cache_manager.set_overlay_cache(overlay_file, scale, overlay_layer)
        
        # 使用alpha_composite进行正确的alpha混合
        canvas = Image.alpha_composite(canvas, overlay_layer)
        
        return canvas

    def _draw_namebox_component(self, canvas, component, character_name):
        """绘制名称框组件（使用缓存）"""
        overlay_file = component.get("overlay", "")
        if not overlay_file:
            return
        
        # 尝试从缓存获取
        scale = component.get("scale", 1.3)
        namebox_with_text = self.component_cache_manager.get_namebox_with_text_cache(character_name, overlay_file, scale)
        
        if namebox_with_text is None:
            # 创建带文字的namebox
            namebox_with_text = self._create_namebox_with_text(character_name, component)
            if namebox_with_text:
                # 应用缩放
                if scale != 1.0:
                    original_width, original_height = namebox_with_text.size
                    new_width = int(original_width * scale)
                    new_height = int(original_height * scale)
                    namebox_with_text = namebox_with_text.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 缓存处理后的图片
                self.component_cache_manager.set_namebox_with_text_cache(character_name, overlay_file, scale, namebox_with_text)
            else:
                return
        
        if namebox_with_text:
            # 使用统一位置计算函数
            align = component.get("align", "bottom-left")
            canvas_width, canvas_height = canvas.size
            offset_x = component.get("offset_x", 0)
            offset_y = component.get("offset_y", 0)
            
            namebox_x, namebox_y = self._calculate_component_position(
                canvas_width, canvas_height,
                namebox_with_text.width, namebox_with_text.height,
                align,
                offset_x,
                offset_y
            )
            
            canvas.paste(namebox_with_text, (namebox_x, namebox_y), namebox_with_text)

    def _draw_extra_component(self, canvas, component):
        """绘制额外组件（使用缓存）"""
        overlay_file = component.get("overlay", "")
        if not overlay_file:
            return canvas
        
        # 尝试从缓存获取
        scale = component.get("scale", 1.0)
        overlay_layer = self.component_cache_manager.get_overlay_cache(overlay_file, scale)
        
        if overlay_layer is None:
            overlay_path = get_resource_path(os.path.join("assets", "shader", overlay_file))
            if not os.path.exists(overlay_path):
                return canvas
            
            extra_img = load_image_cached(overlay_path)
            
            # 应用缩放
            if scale != 1.0:
                original_width, original_height = extra_img.size
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                extra_img = extra_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
            # 创建透明图层进行alpha混合
            overlay_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            
            # 使用统一位置计算函数
            align = component.get("align", "top-left")
            offset_x = component.get("offset_x", 0)
            offset_y = component.get("offset_y", 0)
            canvas_width, canvas_height = canvas.size
            
            paste_x, paste_y = self._calculate_component_position(
                canvas_width, canvas_height,
                extra_img.width, extra_img.height,
                align,
                offset_x,
                offset_y
            )
            
            overlay_layer.paste(extra_img, (paste_x, paste_y), extra_img)

            # 缓存处理后的图片
            self.component_cache_manager.set_overlay_cache(overlay_file, scale, overlay_layer)
        
        canvas = Image.alpha_composite(canvas, overlay_layer)
        
        return canvas
    
    def _create_namebox_with_text(self, character_name: str, component: dict) -> Image.Image:
        """在namebase上合成角色名字文字，使用组件配置"""
        overlay_file = component.get("overlay", "")
        if not overlay_file:
            return None
            
        namebox_path = get_resource_path(os.path.join("assets", "shader", overlay_file))
        if not os.path.exists(namebox_path):
            return None
                
        namebox = load_image_cached(namebox_path)
        
        # 如果角色没有文字配置，直接返回namebox
        if character_name not in CONFIGS.text_configs_dict:
            return namebox
        
        # 创建绘制对象
        draw = ImageDraw.Draw(namebox)
        
        # 获取角色的文字配置
        text_configs = CONFIGS.text_configs_dict[character_name]
        
        # 计算基线位置（基于最大字号的文字）
        max_font_size = max((config.get("font_size", 92) for config in text_configs if config.get("text")), default=92)
        
        # 根据最大字号计算基线位置
        baseline_y = int(namebox.height * 0.65)

        # 按配置中的顺序绘制每个文字
        current_x = int(270 - max_font_size / 2)
        
        for config in text_configs:
            text = config["text"]
            if not text:  # 跳过空文本
                continue
                
            font_color = tuple(config["font_color"])
            font_size = config["font_size"]
            
            # 获取字体
            font_name = CONFIGS.current_character.get("font", "font3")
            font = load_font_cached(font_name, font_size)
            
            # 计算文字宽度（使用textlength方法）
            text_width = int(draw.textlength(text, font=font))
            
            # 计算阴影位置和主文字位置
            shadow_x = current_x + 2
            shadow_y = baseline_y + 2
            
            main_x = current_x
            main_y = baseline_y
            
            # 绘制阴影文字
            draw.text(
                (shadow_x, shadow_y), 
                text, 
                fill=(0, 0, 0), 
                font=font,
                anchor="ls"
            )

            # 绘制主文字
            draw.text(
                (main_x, main_y), 
                text, 
                fill=font_color, 
                font=font,
                anchor="ls"
            )
            
            # 更新下一个文字的起始位置
            current_x = main_x + text_width
        
        return namebox

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
            if not self.sentiment_analyzer_status['initialized']:
                # 如果未初始化，则开始初始化
                self.update_status("正在初始化情感分析器...")
                if "sentiment_matching" not in CONFIGS.gui_settings:
                    CONFIGS.gui_settings["sentiment_matching"] = {}
                CONFIGS.gui_settings["sentiment_matching"]["enabled"] = True
                CONFIGS.save_gui_settings()
                self._initialize_sentiment_analyzer_async()
            else:
                # 如果已初始化，直接启用
                self.update_status("已启用情感匹配功能")
                CONFIGS.gui_settings["sentiment_matching"]["enabled"] = True
                CONFIGS.save_gui_settings()
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
        if not text.strip():
            return None
        
        if not self.sentiment_analyzer_status['initialized']:
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
        self.preload_manager.clear_caches("character")  # 清理角色缓存
        if 0 < index <= len(CONFIGS.character_list):
            CONFIGS.current_character_index = index
            CONFIGS.mahoshojo = CONFIGS.load_config("chara_meta")
            CONFIGS.character_list = list(CONFIGS.mahoshojo.keys())
            character_name = CONFIGS.get_character()
            # 加载当前角色的配置到current_character变量
            if character_name in CONFIGS.mahoshojo:
                CONFIGS.current_character = CONFIGS.mahoshojo[character_name]
            else:
                CONFIGS.current_character = {}
            
            # 根据预加载设置决定是否预加载新角色的图片
            preloading_settings = CONFIGS.gui_settings.get("preloading", {})
            preload_character = preloading_settings.get("preload_character", True)
            
            if preload_character:
                self.update_status(f"正在切换到角色: {character_name}")
                self.preload_manager.submit_preload_task('character', character_name=character_name)
            else:
                self.update_status(f"切换到角色: {character_name} (预加载已禁用)")
            
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

        # 生成预览图片
        try:
            self._current_base_image = self._generate_base_image_with_text(
                character_name, background_index, emotion_index
            )
        except:
            self._current_base_image = Image.new("RGB", (400, 300), color="gray")

        # 用于 GUI 预览
        preview_image = self._current_base_image.copy()

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

        if platform.startswith("win"):
            self.kbd_controller.press(Key.ctrl)
            self.kbd_controller.press('a')
            self.kbd_controller.release('a')
            self.kbd_controller.press('x')
            self.kbd_controller.release('x')
            self.kbd_controller.release(Key.ctrl)
        else:
            self.kbd_controller.press(Key.cmd)
            self.kbd_controller.press("a")
            self.kbd_controller.release("a")
            self.kbd_controller.press("x")
            self.kbd_controller.release("x")
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
            image_region = (
                paste_settings.get("x", 0),
                paste_settings.get("y", 0),
                paste_settings.get("x", 0) + paste_settings.get("width", 300),
                paste_settings.get("y", 0) + paste_settings.get("height", 200)
            )
            
            print(f"[{int((time.time()-start_time)*1000)}] 开始合成图片")
            
            bmp_bytes = draw_content_auto(
                image_source = self._current_base_image,
                text = text,
                content_image = image,
                text_rect=text_region,
                image_rect=image_region,
                fill_mode = paste_settings.get("fill_mode", "fit"),
                image_align = paste_settings.get("align", "center"),
                image_valign = paste_settings.get("valign", "middle"),
                image_paste_mode=enabled
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


class ComponentCacheManager:
    """组件缓存管理器（修复版）"""
    
    def __init__(self):
        self._overlay_cache = {}  # 文本框和额外组件缓存
        self._namebox_cache = {}  # 名称框缓存
    
    def get_overlay_cache(self, overlay_file: str, scale: float):
        """获取缓存的文本框/额外组件图片"""
        cache_key = f"{overlay_file}_{scale}"
        return self._overlay_cache.get(cache_key)
    
    def set_overlay_cache(self, overlay_file: str, scale: float, image):
        """设置文本框/额外组件缓存"""
        cache_key = f"{overlay_file}_{scale}"
        self._overlay_cache[cache_key] = image
    
    def get_namebox_with_text_cache(self, character_name: str, overlay_file: str, scale: float):
        """获取缓存的名称框图片"""
        cache_key = f"{character_name}_{overlay_file}_{scale}"
        return self._namebox_cache.get(cache_key)
    
    def set_namebox_with_text_cache(self, character_name: str, overlay_file: str, scale: float, image):
        """设置名称框缓存"""
        cache_key = f"{character_name}_{overlay_file}_{scale}"
        self._namebox_cache[cache_key] = image
    
    def clear_cache(self, cache_type: str = "all"):
        """清理特定类型的缓存"""
        print("清理缓存")
        if cache_type in ("overlay", "all"):
            self._overlay_cache.clear()
        if cache_type in ("namebox", "all"):
            self._namebox_cache.clear()