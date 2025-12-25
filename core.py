"""魔裁文本框核心逻辑"""
from config import CONFIGS
from clipboard_utils import ClipboardManager
from sentiment_analyzer import SentimentAnalyzer

from load_utils import load_character_safe, get_preload_manager, load_image_cached, get_unified_cache_manager, load_background_component_safe, calculate_component_position, apply_fill_mode, calculate_canvas_size
from path_utils import get_resource_path
from draw_utils import draw_content_auto, load_font_cached

import os
import time
import random
import psutil
import threading
from pynput.keyboard import Key, Controller
from sys import platform
from PIL import Image, ImageDraw
from typing import Dict, Any

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
        # 使用安全的方式设置回调
        self.preload_manager.set_update_callback(self._safe_update_status)
        
        # 获取组件缓存管理器
        self._cache_manager = get_unified_cache_manager()

        # 程序启动时开始预加载图片
        if CONFIGS.gui_settings.get("preloading", {}).get("preload_character", True):
            current_character = CONFIGS.get_character()
            self.preload_manager.submit_preload_task('character', character_name=current_character)
        
        if CONFIGS.gui_settings.get("preloading", {}).get("preload_background", True):
            self.preload_manager.submit_preload_task('background')
    
        # 程序启动时检查是否需要初始化
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        if sentiment_settings.get("enabled", False):
            self.update_status("检测到启用情感匹配，正在初始化...")
            self._initialize_sentiment_analyzer_async()
        else:
            self.update_status("情感匹配功能未启用")
            self._notify_gui_status_change(False, False)
    
    def _safe_update_status(self, message: str):
        """安全更新状态 - 通过回调机制"""
        if self.status_callback:
            try:
                self.update_status(message)
                pass
            except Exception as e:
                print(f"安全更新状态失败: {str(e)}")

    def _generate_base_image_with_text(
        self, character_name: str, background_index: int, emotion_index: int
    ) -> Image.Image:
        """生成带角色文字的基础图片"""
        start_time = time.time()
        
        # 获取画布大小
        self._canvas_size = calculate_canvas_size()

        # 1. 获取排序后的组件列表（按图层升序）
        sorted_components = CONFIGS.get_sorted_image_components()
        
        canvas = load_background_component_safe(None)
        # 2. 加载背景
        for component in sorted_components:
            if all([component.get("type") == "background", component.get("enabled", False)]):
                if not component.get("use_fixed_background", False):
                    component["overlay"] = f"c{background_index}"
                canvas = load_background_component_safe(component)
                break
        
        if canvas.width != 2560:
            canvas = canvas.resize(self._canvas_size)

        print(f"背景加载用时 {int((time.time()-start_time)*1000)}ms")
        
        # 3. 寻找缓存
        if self._cache_manager.cached_layers_sequence:
            for data in self._cache_manager.cached_layers_sequence:
                if data:
                    if data[1]:
                        canvas = Image.alpha_composite(canvas, data[1])
                    if data[0]:
                        overlay = self._draw_component(data[0], character_name, emotion_index)
                        if overlay:
                            canvas = Image.alpha_composite(canvas, overlay)
        else:
            should_cache = not self.is_style_window_open()
            if should_cache:
                cache_layer = Image.new("RGBA", (self._canvas_size), (0, 0, 0, 0))
                layer_counter = 0
            # 绘制其他组件并缓存
            for component in sorted_components:
                if not component.get("enabled", True):
                    continue
                
                # 绘制其他组件
                target = self._draw_component(component, character_name, emotion_index)

                # 顺带缓存图层
                if should_cache:
                    if component.get("type") in ["background", "character"] and not (component.get("use_fixed_background", False) or component.get("use_fixed_character", False)):
                        self._cache_manager.cached_layers_sequence.append((component, cache_layer))
                        if layer_counter > 0:
                            cache_layer = Image.new("RGBA", (self._canvas_size), (0, 0, 0, 0))
                        else:
                            layer_counter = 0
                    elif target:
                        cache_layer = Image.alpha_composite(cache_layer, target)
                        layer_counter += 1
                
                # 合成图层
                if target:
                    canvas = Image.alpha_composite(canvas, target)
            if should_cache and layer_counter > 0:
                self._cache_manager.cached_layers_sequence.append(({}, cache_layer))
            
        print(f"图片合成用时 {int((time.time()-start_time)*1000)}ms")
        return canvas

    def is_style_window_open(self):
        """检测样式编辑窗口是否开启"""
        if not hasattr(self, 'gui_callback') or not self.gui_callback:
            return False
        
        # 通过GUI回调获取GUI实例
        try:
            # 假设GUI实例可通过某种方式访问
            gui_instance = self.gui_callback.get('gui') if isinstance(self.gui_callback, dict) else getattr(self, '_gui_instance', None)
            if gui_instance and hasattr(gui_instance, 'style_window') and gui_instance.style_window:
                # 检查窗口是否仍然有效
                return self._is_window_valid(gui_instance.style_window.window)
            return False
        except:
            return False
        
    def _draw_component(self, component, character_name=None, emotion_index=None):
        """统一的组件绘制函数"""
        comp_type = component.get("type")
        
        if comp_type == "textbox":
            return self._draw_textbox_component(component)
        elif comp_type == "namebox":
            return self._draw_namebox_component(component, character_name)
        elif comp_type == "character":
            return self._draw_character_component(component, character_name, emotion_index)
        elif comp_type == "extra":
            return self._draw_extra_component(component)
        elif comp_type == "text":
            return self._draw_text_component(component)
        return None

    def _draw_textbox_component(self, component):
        """绘制文本框组件"""
        overlay_file = component.get("overlay", "")
        if not overlay_file:
            return None
        
        overlay_path = get_resource_path(os.path.join("assets", "shader", overlay_file))
        if not os.path.exists(overlay_path):
            return None
        
        textbox = load_image_cached(overlay_path)
        
        # 应用缩放
        scale = component.get("scale", 1.0)
        if scale != 1.0:
            original_width, original_height = textbox.size
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            textbox = textbox.resize((new_width, new_height), Image.Resampling.BILINEAR)
        
        # 计算粘贴位置
        align = component.get("align", "bottom-center")
        offset_x = component.get("offset_x", 0)
        offset_y = component.get("offset_y", 0)
        
        paste_x, paste_y = calculate_component_position(self._canvas_size[0], self._canvas_size[1],textbox.width, textbox.height,align,offset_x,offset_y)
        
        # 创建透明图层并粘贴文本框
        overlay_layer = Image.new("RGBA", self._canvas_size, (0, 0, 0, 0))
        overlay_layer.paste(textbox, (paste_x, paste_y), textbox)
        
        return overlay_layer

    def _draw_namebox_component(self, component, character_name):
        """绘制名称框组件 - 修复：统一使用alpha_composite进行alpha混合"""
        overlay_file = component.get("overlay", "")
        if not overlay_file:
            return None
        
        # 创建带文字的namebox
        namebox_with_text = self._create_namebox_with_text(character_name, component)
        if not namebox_with_text:
            return None
        
        # 应用缩放
        scale = component.get("scale", 1.2)
        if scale != 1.0:
            original_width, original_height = namebox_with_text.size
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            namebox_with_text = namebox_with_text.resize((new_width, new_height), Image.Resampling.BILINEAR)
        
        # 使用统一位置计算函数
        align = component.get("align", "bottom-left")
        canvas_width, canvas_height = self._canvas_size
        offset_x = component.get("offset_x", 0)
        offset_y = component.get("offset_y", 0)
        
        namebox_x, namebox_y = calculate_component_position(canvas_width, canvas_height,namebox_with_text.width, namebox_with_text.height,align,offset_x,offset_y)
        
        # 创建透明图层并粘贴名称框
        overlay_layer = Image.new("RGBA", self._canvas_size, (0, 0, 0, 0))
        overlay_layer.paste(namebox_with_text, (namebox_x, namebox_y), namebox_with_text)
        
        return overlay_layer

    def _draw_character_component(self, component, character_name=None, emotion_index=None):
        """绘制角色组件 - 保留直接paste（角色图片通常已经处理好了透明度）"""
        # 检查是否启用
        if not component.get("enabled", True):
            return None
        
        # 确定使用的角色和表情
        if component.get("use_fixed_character", False):
            # 使用固定角色
            fixed_character_name = component.get("character_name", "")
            fixed_emotion_index = component.get("emotion_index", 1)
            
            if not fixed_character_name:
                return None
            
            draw_character_name = fixed_character_name
            draw_emotion_index = fixed_emotion_index
            # 获取固定角色的配置
            character_config = CONFIGS.mahoshojo.get(fixed_character_name, {})
        else:
            # 使用主程序角色
            if character_name is None or emotion_index is None:
                return None
                
            draw_character_name = character_name
            draw_emotion_index = emotion_index
            character_config = CONFIGS.current_character
        
        # 加载预处理的角色图片（传入组件配置）
        overlay = load_character_safe(draw_character_name, draw_emotion_index, component)
        
        # 计算粘贴位置
        target_width, target_height = self._canvas_size
        overlay_width, overlay_height = overlay.size
        
        align = component.get("align", "bottom-left")
        offset_x = component.get("offset_x", 0)
        offset_y = component.get("offset_y", 0)
        
        # 使用统一位置计算函数获取基本位置
        paste_x, paste_y = calculate_component_position(target_width, target_height,overlay_width, overlay_height,align,offset_x,offset_y)
        
        # 1. 角色整体偏移
        char_offset = character_config.get("offset", (0, 0))
        
        # 2. 表情特定偏移
        emotion_str = str(draw_emotion_index)
        paste_x += character_config.get("offsetX", {}).get(emotion_str, 0) + char_offset[0]
        paste_y += character_config.get("offsetY", {}).get(emotion_str, 0) + char_offset[1]
        
        # 角色图片直接paste（因为角色图片通常已经处理好了透明度）
        overlay_layer = Image.new("RGBA", self._canvas_size, (0, 0, 0, 0))
        overlay_layer.paste(overlay, (paste_x, paste_y), overlay)
        return overlay_layer
    
    def _draw_extra_component(self, component):
        """绘制额外组件 - 修复：统一使用alpha_composite进行alpha混合"""
        overlay_file = component.get("overlay", "")
        if not overlay_file:
            return None
        
        overlay_path = get_resource_path(os.path.join("assets", "shader", overlay_file))
        if not os.path.exists(overlay_path):
            return None
        
        extra_img = load_image_cached(overlay_path)
        
        # 应用缩放和填充模式
        scale = component.get("scale", 1.0)
        fill_mode = component.get("fill_mode", "fit")
        
        if scale != 1.0:
            original_width, original_height = extra_img.size
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            extra_img = extra_img.resize((new_width, new_height), Image.Resampling.BILINEAR)
        
        # 应用填充模式
        canvas_width, canvas_height = self._canvas_size
        extra_img = apply_fill_mode(extra_img, canvas_width, canvas_height, fill_mode)

        # 使用统一位置计算函数
        align = component.get("align", "top-left")
        offset_x = component.get("offset_x", 0)
        offset_y = component.get("offset_y", 0)
        
        paste_x, paste_y = calculate_component_position(canvas_width, canvas_height,extra_img.width, extra_img.height,align,offset_x,offset_y)
        
        # 创建透明图层并粘贴额外图片
        overlay_layer = Image.new("RGBA", self._canvas_size, (0, 0, 0, 0))
        overlay_layer.paste(extra_img, (paste_x, paste_y), extra_img)
        
        return overlay_layer

    def _draw_text_component(self, component):
        """绘制文本组件 - 文本组件没有透明度问题，无需修改"""
        # 检查是否启用
        if not component.get("enabled", True):
            return None
        
        # 获取文本内容
        text_content = component.get("text", "")
        if not text_content:
            return None
        
        # 获取文本样式
        font_family = component.get("font_family", "font3")
        font_size = component.get("font_size", 90)
        text_color = component.get("text_color", "#FFFFFF")
        shadow_color = component.get("shadow_color", "#000000")
        shadow_offset_x = component.get("shadow_offset_x", 4)
        shadow_offset_y = component.get("shadow_offset_y", 4)
        max_width = component.get("max_width", 500)
        
        # 获取对齐方式
        align = component.get("align", "top-left")
        offset_x = component.get("offset_x", 0)
        offset_y = component.get("offset_y", 0)
        
        # 创建绘制对象
        target = Image.new("RGBA", self._canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(target)
        
        # 加载字体
        font = load_font_cached(font_family, font_size)
        
        # 计算文本位置
        canvas_width, canvas_height = self._canvas_size
        
        # 简单的换行处理
        lines = []
        words = [uint for uint in text_content]
        current_line = ""
        
        for word in words:
            test_line = f"{current_line}{word}" if current_line else word
            test_width = int(draw.textlength(test_line, font=font))
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        if not lines:
            return target
        
        # 计算总文本高度
        line_height = int(font_size * 1.2)  # 行高为字号的1.2倍
        
        # 为每行文本计算位置并绘制
        for i, line in enumerate(lines):
            line_width = int(draw.textlength(line, font=font))
            
            # 计算单行位置
            line_x, line_y = calculate_component_position(canvas_width, canvas_height,line_width, font_size,align,offset_x,offset_y + i * line_height)
            
            # 绘制阴影
            draw.text((line_x + shadow_offset_x, line_y + shadow_offset_y),line,fill=shadow_color,font=font,anchor="la")
            
            # 绘制主文字
            draw.text((line_x, line_y),line,fill=text_color,font=font,anchor="la")
        
        return target

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
            
            # 绘制阴影文字
            draw.text((shadow_x, shadow_y), text, fill=(0, 0, 0), font=font,anchor="ls")

            # 绘制主文字
            draw.text((current_x, baseline_y), text, fill=font_color, font=font,anchor="ls")
            
            # 更新下一个文字的起始位置
            current_x += text_width
        
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
        self._cache_manager.clear_cache("character")
        self._cache_manager.clear_cache("layers")
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
            if CONFIGS.gui_settings.get("preloading", {}).get("preload_character", False):
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
            self._current_base_image = self._generate_base_image_with_text(character_name, background_index, emotion_index)
        except:
            print("预览图生成出错")
            self._current_base_image = Image.new("RGBA", (10, 10), color=(0, 0, 0, 0))

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