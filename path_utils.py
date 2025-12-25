"""路径工具模块 - 处理打包环境下的路径问题"""

import os
import sys


def get_base_path():
    """获取程序的基础路径，支持打包环境和开发环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return base_path

def get_internal_path(relative_path):
    """获取程序的临时解压路径"""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            # 单文件模式：文件在临时解压目录
            base_path = sys._MEIPASS
        else:
            # 单目录模式：文件在可执行文件目录
            base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 在打包环境中，优先从程序所在目录查找
    if getattr(sys, 'frozen', False):
        # 首先尝试程序目录下的资源文件
        program_dir_path = os.path.join(base_path, relative_path)
        if os.path.exists(program_dir_path):
            return program_dir_path
    
    # 开发环境或打包环境未找到资源时，使用基础路径
    resource_path = os.path.join(base_path, relative_path)
    return resource_path

def set_window_icon(window, icon_name="icon.ico"):
    """为窗口设置图标"""
    try:
        icon_path = get_resource_path(os.path.join("assets", icon_name))
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
            return True
    except Exception as e:
        print(f"设置窗口图标失败: {e}")
    return False

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持打包环境"""
    base_path = get_base_path()
    
    # 在打包环境中，优先从程序所在目录查找
    if getattr(sys, 'frozen', False):
        # 首先尝试程序目录下的资源文件
        program_dir_path = os.path.join(base_path, relative_path)
        if os.path.exists(program_dir_path):
            return program_dir_path
    
    # 开发环境或打包环境未找到资源时，使用基础路径
    resource_path = os.path.join(base_path, relative_path)
    return resource_path


def ensure_path_exists(file_path):
    """确保文件路径的目录存在"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return file_path

def get_font_path(font_name: str) -> str:
    """获取字体文件路径，支持多种格式"""
    supported_formats = ['.ttf', '.otf', '.ttc', '.woff', '.woff2']
    
    # 尝试在assets/fonts目录下查找字体
    for ext in supported_formats:
        font_path = get_resource_path(os.path.join("assets", "fonts", f"{font_name}{ext}"))
        if os.path.exists(font_path):
            return font_path
    
    # 如果所有格式都不存在，返回默认ttf格式的路径
    return get_resource_path(os.path.join("assets", "fonts", f"{font_name}.ttf"))

def get_available_fonts() -> list:
    """获取可用字体列表，只返回文件名（不含扩展名）"""
    fonts_dir = get_resource_path(os.path.join("assets", "fonts"))
    font_files = []
    
    if not os.path.exists(fonts_dir):
        print(f"字体目录不存在: {fonts_dir}")
        return []
    
    supported_formats = ('.ttf', '.otf', '.ttc', '.woff', '.woff2')
    
    for file in os.listdir(fonts_dir):
        if file.lower().endswith(supported_formats):
            # 只返回文件名（不含扩展名）
            font_name = os.path.splitext(file)[0]
            font_files.append(font_name)
    
    return sorted(set(font_files))

def is_font_available(font_name: str) -> bool:
    """检查字体是否可用"""
    font_path = os.path.join("assets", "fonts", font_name)
    resolved_font_path = get_resource_path(font_path)
    return os.path.exists(resolved_font_path)