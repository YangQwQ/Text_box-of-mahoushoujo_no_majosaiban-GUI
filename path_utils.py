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

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持打包环境"""
    base_path = get_base_path()
    
    program_dir_path = os.path.join(base_path, relative_path)
    if os.path.exists(program_dir_path):
        return program_dir_path
    else:
        return ""

def ensure_path_exists(file_path):
    """确保文件路径的目录存在"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return file_path

def get_available_fonts() -> list:
    """获取可用字体列表，只返回文件名（不含扩展名）"""
    fonts_dir = get_resource_path(os.path.join("assets", "fonts"))
    font_files = []
    
    if not fonts_dir:
        print(f"字体目录不存在: {fonts_dir}")
        return []
    
    supported_formats = ('.ttf', '.otf', '.ttc', '.woff', '.woff2')
    
    for file in os.listdir(fonts_dir):
        if file.lower().endswith(supported_formats):
            # 只返回文件名（不含扩展名）
            font_name = os.path.splitext(file)[0]
            font_files.append(font_name)
    
    return sorted(set(font_files))


def get_background_list() -> list:
    """获取背景文件列表"""
    try:
        background_dir = get_resource_path(os.path.join("assets", "background"))
        if background_dir:
            # 获取所有图片文件
            image_extensions = ['.webp', '.png', '.jpg', '.jpeg', '.bmp', '.gif']
            bg_files = []
            for f in os.listdir(background_dir):
                # 检查是否为图片文件
                if any(f.lower().endswith(ext) for ext in image_extensions):
                    bg_files.append(f)
            return sorted(bg_files)
        else:
            print(f"警告：背景图片目录不存在: {background_dir}")
            return []
    except Exception as e:
        print(f"获取背景文件列表失败: {e}")
        return []