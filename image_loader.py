# image_loader.py - 和dll交互的模块
import os
import ctypes
import json
from ctypes import c_char_p, c_int, POINTER, c_ubyte, c_void_p, c_float, c_bool
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image
import numpy as np

# 定义C结构体对应的Python类
class DrawRequest(ctypes.Structure):
    _fields_ = [
        ("canvas_width", ctypes.c_int),
        ("canvas_height", ctypes.c_int),
        
        # 文本区域
        ("text_x", ctypes.c_int),
        ("text_y", ctypes.c_int),
        ("text_width", ctypes.c_int),
        ("text_height", ctypes.c_int),
        
        # 文本属性
        ("font_name", ctypes.c_char * 256),
        ("font_size", ctypes.c_int),
        ("text_color", ctypes.c_ubyte * 4),
        ("shadow_color", ctypes.c_ubyte * 4),
        ("bracket_color", ctypes.c_ubyte * 4),
        ("shadow_offset_x", ctypes.c_int),
        ("shadow_offset_y", ctypes.c_int),
        ("text_align", ctypes.c_int),
        ("text_valign", ctypes.c_int),
        ("line_spacing", ctypes.c_float),
        
        # 文本内容指针
        ("lines", ctypes.c_void_p),
        ("line_count", ctypes.c_int),
        
        # 图片区域
        ("image_x", ctypes.c_int),
        ("image_y", ctypes.c_int),
        ("image_width", ctypes.c_int),
        ("image_height", ctypes.c_int),
        
        # 图片属性
        ("image_data", ctypes.POINTER(ctypes.c_ubyte)),
        ("image_data_width", ctypes.c_int),
        ("image_data_height", ctypes.c_int),
        ("image_data_pitch", ctypes.c_int),
        ("fill_mode", ctypes.c_int),
        ("image_align", ctypes.c_int),
        ("image_valign", ctypes.c_int),
        ("image_padding", ctypes.c_int),
        ("min_image_ratio", ctypes.c_float),
    ]

class TextFragment(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_char * 1024),
        ("r", ctypes.c_ubyte),
        ("g", ctypes.c_ubyte),
        ("b", ctypes.c_ubyte),
        ("a", ctypes.c_ubyte),
    ]

class TextLine(ctypes.Structure):
    _fields_ = [
        ("fragments", ctypes.POINTER(TextFragment)),
        ("fragment_count", ctypes.c_int),
        ("line_height", ctypes.c_int),
        ("total_width", ctypes.c_int),
    ]


class EnhancedImageLoaderDLL:
    """增强的图像加载DLL包装器，使用JSON传递配置"""
    
    def __init__(self, dll_path: str = None):
        from path_utils import get_internal_path
        
        if dll_path is None:
            dll_path = get_internal_path("image_loader.dll")
        
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"DLL文件不存在: {dll_path}")
        
        print(f"正在加载增强版DLL: {dll_path}")
        try:
            self.dll = ctypes.CDLL(dll_path)
            self._define_function_signatures()
            # # 新增函数签名
            # self._define_draw_functions()
            # 新增：配置相关函数
            self._define_config_functions()
            print("增强版DLL加载成功")
        except OSError as e:
            raise OSError(f"加载DLL失败: {e}")
        
        self.layer_cache = []
    
    def _define_function_signatures(self):
        """定义DLL函数签名"""
        
        # 清理缓存
        self.dll.clear_cache.argtypes = [c_char_p]
        self.dll.clear_cache.restype = None
        
        # 生成完整图像（使用JSON字符串）
        self.dll.generate_complete_image.argtypes = [
            c_char_p,                # assets_path
            c_int,                   # canvas_width
            c_int,                   # canvas_height
            c_char_p,                # components_json
            c_char_p,                # character_name
            c_int,                   # emotion_index
            c_int,                   # background_index
            POINTER(POINTER(c_ubyte)),  # out_data
            POINTER(c_int),          # out_width
            POINTER(c_int)           # out_height
        ]
        self.dll.generate_complete_image.restype = c_int
        
        # 清理所有资源
        self.dll.cleanup_all.argtypes = []
        self.dll.cleanup_all.restype = None
        
        # 释放图像数据
        self.dll.free_image_data.argtypes = [POINTER(c_ubyte)]
        self.dll.free_image_data.restype = None
    
    def _define_config_functions(self):
        """定义配置相关函数签名"""
        # 设置全局配置
        self.dll.set_global_config.argtypes = [
            c_char_p,  # assets_path
            c_bool,    # preload_character
            c_bool,    # preload_background
            c_int,     # pre_resize
            c_float    # min_image_ratio
        ]
        self.dll.set_global_config.restype = None
        
        # 更新GUI设置
        self.dll.update_gui_settings.argtypes = [
            c_char_p   # settings_json
        ]
        self.dll.update_gui_settings.restype = None
    
    def set_global_config(self, assets_path: str, preload_character: bool = False, 
                         preload_background: bool = False, pre_resize: int = 1080,
                         min_image_ratio: float = 0.2):
        """设置全局配置到DLL"""
        assets_path_bytes = assets_path.encode('utf-8')
        self.dll.set_global_config(
            assets_path_bytes,
            c_bool(preload_character),
            c_bool(preload_background),
            c_int(pre_resize),
            c_float(min_image_ratio)
        )
        print("DLL全局配置已设置")
    
    def update_gui_settings(self, settings: Dict[str, Any]):
        """更新GUI设置到DLL"""
        settings_json = json.dumps(settings, ensure_ascii=False).encode('utf-8')
        self.dll.update_gui_settings(settings_json)
        print("DLL GUI设置已更新")
    
    def clear_cache(self, cache_type: str = "all"):
        """清理缓存 - 替换原来的clear_cache"""
        cache_type_bytes = cache_type.encode('utf-8')
        self.dll.clear_cache(cache_type_bytes)
        if cache_type in ["all", "layers"]:
            self.layer_cache.clear()
        print(f"DLL缓存已清理: {cache_type}")
    
    def generate_complete_image(
        self,
        assets_path: str,
        canvas_width: int,
        canvas_height: int,
        components: List[Dict[str, Any]],
        character_name: str,
        emotion_index: int,
        background_index: int
    ) -> Optional[Image.Image]:
        """生成完整的图像，使用JSON传递组件配置"""
        
        # 将组件列表转换为JSON字符串
        components_json = json.dumps(components, ensure_ascii=False)
        
        # 准备输出参数
        out_data = POINTER(c_ubyte)()
        out_width = c_int()
        out_height = c_int()
        
        # 调用DLL函数
        assets_path_bytes = assets_path.encode('utf-8')
        components_json_bytes = components_json.encode('utf-8')
        character_name_bytes = character_name.encode('utf-8')
        
        result = self.dll.generate_complete_image(
            assets_path_bytes,
            canvas_width,
            canvas_height,
            components_json_bytes,
            character_name_bytes,
            emotion_index,
            background_index,
            ctypes.byref(out_data),
            ctypes.byref(out_width),
            ctypes.byref(out_height)
        )
        
        if result != 1:  # LOAD_SUCCESS = 1
            print(f"生成完整图像失败，错误码: {result}")
            return None
        
        # 转换为PIL Image
        width = out_width.value
        height = out_height.value
        
        if width <= 0 or height <= 0:
            print(f"无效的图像尺寸: {width}x{height}")
            return None
        
        # 读取数据
        data_size = width * height * 4
        addr = ctypes.cast(out_data, c_void_p).value
        if not addr:
            print("无效的图像数据地址")
            return None
        
        try:
            image_data = ctypes.string_at(addr, data_size)
            
            # 创建PIL Image
            img = Image.frombytes('RGBA', (width, height), image_data)
            
            # 释放DLL分配的内存
            self.dll.free_image_data(out_data)
            
            print(f"图像生成成功: {width}x{height}")
            return img
        except Exception as e:
            print(f"创建图像失败: {str(e)}")
            if out_data:
                self.dll.free_image_data(out_data)
            return None
    
    def cleanup(self):
        """清理所有资源"""
        try:
            self.dll.cleanup_all()
            print("所有资源已清理")
        except Exception as e:
            print(f"清理资源异常: {str(e)}")
    
    def __del__(self):
        self.cleanup()

    # def _define_draw_functions(self):
    #     """定义绘图相关函数签名"""
    #     # 绘制内容和文本
    #     self.dll.draw_content_with_text.argtypes = [
    #         ctypes.POINTER(DrawRequest),
    #         ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte)),
    #         ctypes.POINTER(ctypes.c_int),
    #         ctypes.POINTER(ctypes.c_int)
    #     ]
    #     self.dll.draw_content_with_text.restype = ctypes.c_int
        
    # def draw_content(
    #     self,
    #     text_rect: Tuple[int, int, int, int],
    #     image_rect: Tuple[int, int, int, int],
    #     text_lines: List[Dict[str, Any]],
    #     image_data: Optional[bytes] = None,
    #     image_width: int = 0,
    #     image_height: int = 0,
    #     image_pitch: int = 0,
    #     **kwargs
    # ) -> Optional[Image.Image]:
    #     """绘制内容和文本到背景图片上"""
        
    #     # 准备DrawRequest结构
    #     request = DrawRequest()
        
    #     # 设置画布尺寸（从缓存中获取，这里使用默认值，实际在C端会使用缓存的预览图）
    #     request.canvas_width = 2560
    #     request.canvas_height = 1440
        
    #     # 设置文本区域
    #     text_x, text_y, text_x2, text_y2 = text_rect
    #     request.text_x = text_x
    #     request.text_y = text_y
    #     request.text_width = text_x2 - text_x
    #     request.text_height = text_y2 - text_y
        
    #     # 设置字体和颜色
    #     request.font_name = kwargs.get('font_name', 'font3').encode('utf-8')
    #     request.font_size = kwargs.get('font_size', 24)
        
    #     text_color = kwargs.get('text_color', (255, 255, 255, 255))
    #     request.text_color = (ctypes.c_ubyte * 4)(*text_color)
        
    #     shadow_color = kwargs.get('shadow_color', (0, 0, 0, 255))
    #     request.shadow_color = (ctypes.c_ubyte * 4)(*shadow_color)
        
    #     bracket_color = kwargs.get('bracket_color', (255, 255, 255, 255))
    #     request.bracket_color = (ctypes.c_ubyte * 4)(*bracket_color)
        
    #     request.shadow_offset_x = kwargs.get('shadow_offset_x', 2)
    #     request.shadow_offset_y = kwargs.get('shadow_offset_y', 2)
        
    #     # 设置文本对齐
    #     align_map = {"left": 0, "center": 1, "right": 2}
    #     valign_map = {"top": 0, "middle": 1, "bottom": 2}
    #     request.text_align = align_map.get(kwargs.get('text_align', 'left'), 0)
    #     request.text_valign = valign_map.get(kwargs.get('text_valign', 'top'), 0)
    #     request.line_spacing = kwargs.get('line_spacing', 0.15)
        
    #     # 设置图片区域
    #     image_x, image_y, image_x2, image_y2 = image_rect
    #     request.image_x = image_x
    #     request.image_y = image_y
    #     request.image_width = image_x2 - image_x
    #     request.image_height = image_y2 - image_y
        
    #     # 设置填充模式和对齐
    #     fill_mode_map = {"fit": 0, "width": 1, "height": 2}
    #     request.fill_mode = fill_mode_map.get(kwargs.get('fill_mode', 'fit'), 0)
    #     request.image_align = align_map.get(kwargs.get('image_align', 'center'), 1)
    #     request.image_valign = valign_map.get(kwargs.get('image_valign', 'middle'), 1)
    #     request.image_padding = kwargs.get('image_padding', 12)
    #     request.min_image_ratio = kwargs.get('min_image_ratio', 0.2)
        
    #     # 准备内容图片数据（如果有）
    #     if image_data and image_width > 0 and image_height > 0:
    #         # 将图像数据转换为C指针
    #         img_ptr = (ctypes.c_ubyte * len(image_data)).from_buffer_copy(image_data)
    #         request.image_data = ctypes.cast(img_ptr, ctypes.POINTER(ctypes.c_ubyte))
    #         request.image_data_width = image_width
    #         request.image_data_height = image_height
    #         request.image_data_pitch = image_pitch
    #     else:
    #         request.image_data = None
    #         request.image_data_width = 0
    #         request.image_data_height = 0
    #         request.image_data_pitch = 0
        
    #     # 准备文本行数据
    #     self._prepare_text_lines(request, text_lines)
        
    #     # 调用DLL绘制
    #     out_data = ctypes.POINTER(ctypes.c_ubyte)()
    #     out_width = ctypes.c_int()
    #     out_height = ctypes.c_int()
        
    #     result = self.dll.draw_content_with_text(
    #         ctypes.byref(request),
    #         ctypes.byref(out_data),
    #         ctypes.byref(out_width),
    #         ctypes.byref(out_height)
    #     )
        
    #     if result != 1:
    #         print(f"绘制失败，错误码: {result}")
    #         return None
        
    #     # 转换为PIL Image
    #     width = out_width.value
    #     height = out_height.value
        
    #     if width <= 0 or height <= 0:
    #         print(f"无效的图像尺寸: {width}x{height}")
    #         return None
        
    #     # 读取数据
    #     data_size = width * height * 4
    #     addr = ctypes.cast(out_data, ctypes.c_void_p).value
        
    #     if not addr:
    #         print("无效的图像数据地址")
    #         return None
        
    #     try:
    #         image_data = ctypes.string_at(addr, data_size)
            
    #         # 创建PIL Image
    #         img = Image.frombytes('RGBA', (width, height), image_data)
            
    #         # 释放DLL分配的内存
    #         self.dll.free_image_data(out_data)
            
    #         print(f"内容绘制成功: {width}x{height}")
    #         return img
    #     except Exception as e:
    #         print(f"创建图像失败: {str(e)}")
    #         if out_data:
    #             self.dll.free_image_data(out_data)
    #         return None
    
    def _prepare_text_lines(self, request: DrawRequest, text_lines: List[Dict[str, Any]]):
        """准备文本行数据"""
        if not text_lines:
            request.lines = None
            request.line_count = 0
            return
        
        # 创建TextLine数组
        line_count = len(text_lines)
        line_array = (TextLine * line_count)()
        
        for i, line_info in enumerate(text_lines):
            line = line_array[i]
            
            # 设置行属性
            line.line_height = line_info.get('line_height', 30)
            line.total_width = line_info.get('total_width', 0)
            
            # 准备文本片段
            fragments = line_info.get('fragments', [])
            fragment_count = len(fragments)
            
            if fragment_count > 0:
                fragment_array = (TextFragment * fragment_count)()
                
                for j, fragment_info in enumerate(fragments):
                    fragment = fragment_array[j]
                    
                    # 设置文本
                    text = fragment_info.get('text', '')
                    fragment.text = text[:1023].encode('utf-8')
                    
                    # 设置颜色
                    color = fragment_info.get('color', (255, 255, 255, 255))
                    fragment.r = color[0]
                    fragment.g = color[1]
                    fragment.b = color[2]
                    fragment.a = color[3]
                
                line.fragments = ctypes.cast(fragment_array, ctypes.POINTER(TextFragment))
                line.fragment_count = fragment_count
        
        # 将指针保存到Python对象中，防止被垃圾回收
        self._line_array = line_array
        
        request.lines = ctypes.cast(line_array, ctypes.c_void_p)
        request.line_count = line_count

    def draw_content_simple(
        self,
        text: str,
        emoji_list: List[str],
        emoji_position: List[Tuple[int, int]],
        image_data: Optional[bytes] = None,
        image_width: int = 0,
        image_height: int = 0,
        image_pitch: int = 0
    ) -> Optional[Image.Image]:
        """简化的绘制函数"""
        # 准备emoji数据（包括位置）
        emoji_data = {
            "emojis": emoji_list,
            "positions": emoji_position  # 传递位置信息
        }
        emoji_json = json.dumps(emoji_data, ensure_ascii=False).encode('utf-8')
        
        # 准备文本数据
        text_bytes = text.encode('utf-8') if text else b""
        
        # 调用DLL函数
        out_data = POINTER(ctypes.c_ubyte)()
        out_width = ctypes.c_int()
        out_height = ctypes.c_int()
        
        result = self.dll.draw_content_simple(
            text_bytes,
            emoji_json,
            image_data,
            image_width,
            image_height,
            image_pitch,
            ctypes.byref(out_data),
            ctypes.byref(out_width),
            ctypes.byref(out_height)
        )
        
        if result != 1:
            print(f"绘制失败，错误码: {result}")
            return None
        
        # 转换图像数据
        width = out_width.value
        height = out_height.value
        
        if width <= 0 or height <= 0:
            print(f"无效的图像尺寸: {width}x{height}")
            return None
        
        data_size = width * height * 4
        addr = ctypes.cast(out_data, ctypes.c_void_p).value
        if not addr:
            return None
        
        try:
            image_bytes = ctypes.string_at(addr, data_size)
            img = Image.frombytes('RGBA', (width, height), image_bytes)
            self.dll.free_image_data(out_data)
            return img
        except Exception:
            if out_data:
                self.dll.free_image_data(out_data)
            return None

# 添加全局函数
def draw_content_simple_dll(
    text: str,
    emoji_list: List[str],
    emoji_position: List[Tuple[int, int]],  # 新增参数
    image_data: Optional[bytes] = None,
    image_width: int = 0,
    image_height: int = 0,
    image_pitch: int = 0
) -> Optional[Image.Image]:
    """调用简化的绘制函数 - 更新参数"""
    loader = get_enhanced_loader()
    return loader.draw_content_simple(text, emoji_list, emoji_position, 
                                      image_data, image_width, image_height, image_pitch)

# 全局实例
_enhanced_loader = None

def get_enhanced_loader() -> EnhancedImageLoaderDLL:
    """获取增强的图像加载器"""
    global _enhanced_loader
    if _enhanced_loader is None:
        _enhanced_loader = EnhancedImageLoaderDLL()
    return _enhanced_loader

def generate_image_with_dll(
    assets_path: str,
    canvas_size: tuple,
    components: List[Dict[str, Any]],
    character_name: str,
    emotion_index: int,
    background_index: int
) -> Optional[Image.Image]:
    """使用DLL生成图像"""
    loader = get_enhanced_loader()
    return loader.generate_complete_image(
        assets_path,
        canvas_size[0],
        canvas_size[1],
        components,
        character_name,
        emotion_index,
        background_index
    )

def clear_cache(cache_type: str = "all"):
    """清理DLL缓存 - 替换原来的clear_cache"""
    loader = get_enhanced_loader()
    loader.clear_cache(cache_type)

def set_dll_global_config(assets_path: str, **kwargs):
    """设置DLL全局配置"""
    loader = get_enhanced_loader()
    loader.set_global_config(assets_path, **kwargs)

def update_dll_gui_settings(settings: Dict[str, Any]):
    """更新DLL GUI设置"""
    loader = get_enhanced_loader()
    loader.update_gui_settings(settings)

def update_style_config(style_config):
    """更新C++端的样式配置"""
    loader = get_enhanced_loader()
    
    # 构建样式配置字典
    style_dict = {
        "aspect_ratio": getattr(style_config, 'aspect_ratio', '16:9'),
        "bracket_color": getattr(style_config, 'bracket_color', '#FFFFFF'),
        "font_family": getattr(style_config, 'font_family', 'font3'),
        "font_size": getattr(style_config, 'font_size', 55),
        "paste_image_settings": getattr(style_config, 'paste_image_settings', {
            "align": "center",
            "enabled": "mixed",
            "fill_mode": "width",
            "height": 800,
            "valign": "middle",
            "width": 800,
            "x": 1500,
            "y": 200
        }),
        "shadow_color": getattr(style_config, 'shadow_color', '#000000'),
        "shadow_offset_x": getattr(style_config, 'shadow_offset_x', 0),
        "shadow_offset_y": getattr(style_config, 'shadow_offset_y', 0),
        "text_align": getattr(style_config, 'text_align', 'left'),
        "text_color": getattr(style_config, 'text_color', '#FFFFFF'),
        "text_valign": getattr(style_config, 'text_valign', 'top'),
        "textbox_height": getattr(style_config, 'textbox_height', 245),
        "textbox_width": getattr(style_config, 'textbox_width', 1579),
        "textbox_x": getattr(style_config, 'textbox_x', 470),
        "textbox_y": getattr(style_config, 'textbox_y', 1080),
        "use_character_color": getattr(style_config, 'use_character_color', True)
    }
    
    # 将配置转换为JSON字符串
    style_json = json.dumps(style_dict, ensure_ascii=False).encode('utf-8')
    
    # 调用C++端的更新函数（需要先在DLL中添加这个函数）
    if hasattr(loader.dll, 'update_style_config'):
        loader.dll.update_style_config.argtypes = [c_char_p]
        loader.dll.update_style_config.restype = None
        loader.dll.update_style_config(style_json)
        print(f"Style configuration updated")
    else:
        print(f"Warning: update_style_config function not found in DLL")