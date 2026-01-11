# image_processor.py - 和dll交互的模块
import ctypes
import json
import time
import emoji
from io import BytesIO
from ctypes import c_char_p, c_int, POINTER, c_ubyte, c_void_p, c_float, create_string_buffer, cast
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image

class EnhancedImageLoaderDLL:
    """增强的图像加载DLL包装器，使用JSON传递配置"""
    
    def __init__(self, dll_path: str = None):
        from path_utils import get_internal_path
        
        if dll_path is None:
            dll_path = get_internal_path("dll/Image_Processor.dll")
        
        if not dll_path:
            raise FileNotFoundError(f"DLL文件不存在: {dll_path}")
        
        print(f"正在加载DLL图片合成器: {dll_path}")
        try:
            self.dll = ctypes.CDLL(dll_path)
            self._define_function_signatures()
            self._define_config_functions()
            print("DLL图片合成器加载成功")
        except OSError as e:
            raise OSError(f"加载DLL失败: {e}")
        
        self.layer_cache = False
        self._psd_buffers = []
    
    def _define_function_signatures(self):
        """定义DLL函数签名"""
        # 清理缓存
        self.dll.clear_cache.argtypes = [c_char_p]
        self.dll.clear_cache.restype = None

        # 修改：根据C++签名更新generate_image参数
        self.dll.generate_image.argtypes = [
            c_int,                      # canvas_width
            c_int,                      # canvas_height
            c_char_p,                   # components_json
            c_void_p,                   # image_data (RGBA数据指针)
            c_int,                      # image_width
            c_int,                      # image_height
            c_int,                      # image_pitch
            POINTER(POINTER(c_ubyte)),  # out_data
            POINTER(c_int),             # out_width
            POINTER(c_int)              # out_height
        ]
        self.dll.generate_image.restype = c_int

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
            c_float    # min_image_ratio
        ]
        self.dll.set_global_config.restype = None
        
        # 更新GUI设置
        self.dll.update_gui_settings.argtypes = [
            c_char_p   # settings_json
        ]
        self.dll.update_gui_settings.restype = None
    
    def set_global_config(self, assets_path: str, min_image_ratio: float = 0.2):
        """设置全局配置到DLL"""
        assets_path_bytes = assets_path.encode('utf-8')
        self.dll.set_global_config(
            assets_path_bytes,
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
            self.layer_cache = False
        print(f"DLL缓存已清理: {cache_type}")
    
    def _pil_to_rgba_bytes(self, img: Image.Image) -> tuple[bytes, int, int]:
        """返回 RGBA 字节流、宽、高"""
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        return img.tobytes(), img.width, img.height

    def generate_complete_image(
        self,
        canvas_width: int,
        canvas_height: int,
        components: List[Dict[str, Any]],
    ) -> Optional[Image.Image]:
        """生成完整的图像，使用JSON传递组件配置"""
        # 1. 准备外部图像数据（用于character组件的PSD图像）
        external_image_data = None
        external_image_width = 0
        external_image_height = 0
        external_image_pitch = 0
        
        # 2. 确保缓冲区列表存在
        if not hasattr(self, '_psd_buffers'):
            self._psd_buffers = []
        
        # 清空之前的缓冲区
        self._psd_buffers.clear()
        
        # 查找character组件中的PSD图像
        for comp in components:
            if comp.get("type") == "character" and comp.get("overlay") == "__PSD__":
                img = comp.pop("__psd_image__", None)  # PIL.Image
                if img:
                    # 转换为RGBA格式
                    img_rgba = img.convert("RGBA")
                    width, height = img_rgba.size
                    pitch = width * 4
                    rgba_bytes = img_rgba.tobytes()
                    
                    # 创建缓冲区并保存引用
                    buffer = create_string_buffer(rgba_bytes)
                    self._psd_buffers.append(buffer)
                    
                    # 设置外部图像数据参数
                    external_image_data = cast(buffer, c_void_p)
                    external_image_width = width
                    external_image_height = height
                    external_image_pitch = pitch
                    
                    break
        
        # 3. 序列化 JSON
        components_json = json.dumps(components, ensure_ascii=False).encode('utf-8')
        
        # 4. 调用 DLL
        out_data = POINTER(c_ubyte)()
        out_w, out_h = c_int(), c_int()
        
        result = self.dll.generate_image(
            canvas_width,
            canvas_height,
            components_json,
            external_image_data if external_image_data else c_void_p(None),
            external_image_width,
            external_image_height,
            external_image_pitch,
            ctypes.byref(out_data),
            ctypes.byref(out_w),
            ctypes.byref(out_h)
        )
        
        if result != 1:  # LOAD_SUCCESS = 1
            print(f"生成完整图像失败，错误码: {result}")
            return None
        
        # 转换为PIL Image
        width = out_w.value
        height = out_h.value
        
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

# 辅助函数：提取emoji并替换为占位符
def _extract_emojis_and_replace(src: str):
    """提取emoji并获取字节位置"""
    emoji_infos = emoji.emoji_list(src)
    if not emoji_infos:
        return [], []
    
    emojis = []
    positions = []  # 记录字节位置
    
    # 用于将字符索引转换为字节索引的辅助函数
    def char_index_to_byte_index(char_index):
        # 将前char_index个字符编码为UTF-8，然后返回字节数
        return len(src[:char_index].encode("utf-8"))
    
    for info in emoji_infos:
        s = info["match_start"]  # 字符索引
        e = info["match_end"]
        # 转换为字节索引
        s_byte = char_index_to_byte_index(s)
        e_byte = char_index_to_byte_index(e)
        emojis.append(src[s:e])
        positions.append((s_byte, e_byte))  # 记录字节位置元组
    return emojis, positions

def draw_content_auto(
    text: Optional[str] = None, 
    content_image: Optional[Image.Image] = None
) -> bytes:
    """简化的绘制函数，只处理emoji提取，其他交给C++"""
    st = time.time()
    
    # 提取emoji
    emoji_list = []
    emoji_position = []
    if text:
        emoji_list, emoji_position = _extract_emojis_and_replace(text)
    
    print(f"Emoji提取用时: {int((time.time()-st)*1000)}ms")
    st = time.time()
    
    # 准备图片数据
    image_data = None
    image_width = 0
    image_height = 0
    image_pitch = 0
    
    if content_image:
        # 将图片转换为RGBA格式
        img_rgba = content_image.convert("RGBA")
        image_data = img_rgba.tobytes()
        image_width, image_height = img_rgba.size
        image_pitch = image_width * 4
    
    # 调用C++端的简化函数
    try:
        loader = get_enhanced_loader()
        result_image = loader.draw_content_simple(
            text=text or "",
            emoji_list=emoji_list,
            emoji_position=emoji_position,
            image_data=image_data,
            image_width=image_width,
            image_height=image_height,
            image_pitch=image_pitch,
        )
        
        print(f"C++ drawing time: {int((time.time()-st)*1000)}ms")
        st = time.time()
        
        if not result_image:
            raise Exception("C++ drawing failed")
        
        # 转换为BMP格式
        buf = BytesIO()
        img_rgb = result_image.convert("RGB")
        img_rgb.save(buf, format="BMP")
        bmp_data = buf.getvalue()[14:]
        
        print(f"输出耗时: {int((time.time()-st)*1000)}ms")
        return bmp_data
        
    except Exception as e:
        print(f"绘制失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

# 全局实例
_enhanced_loader = None

def get_enhanced_loader() -> EnhancedImageLoaderDLL:
    """获取增强的图像加载器"""
    global _enhanced_loader
    if _enhanced_loader is None:
        _enhanced_loader = EnhancedImageLoaderDLL()
    return _enhanced_loader

def generate_image_with_dll(
    canvas_size: tuple,
    components: List[Dict[str, Any]],
) -> Optional[Image.Image]:
    """使用DLL生成图像"""
    loader = get_enhanced_loader()
    return loader.generate_complete_image(
        canvas_size[0],
        canvas_size[1],
        components
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
    
    # 调用C++端的更新函数
    if hasattr(loader.dll, 'update_style_config'):
        loader.dll.update_style_config.argtypes = [c_char_p]
        loader.dll.update_style_config.restype = None
        loader.dll.update_style_config(style_json)
        print(f"Style configuration updated")
    else:
        print(f"Warning: update_style_config function not found in DLL")