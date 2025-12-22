"""文件加载工具"""
import os
import threading
import queue
from PIL import ImageFont, Image, ImageDraw
from typing import Callable, Dict, Any, Optional, Tuple
import time

from path_utils import get_resource_path, get_font_path
from config import CONFIGS

# 资源缓存
_font_cache = {}
_background_cache = {}  # 背景图片缓存（包含裁剪信息）
_character_cache = {}   # 角色图片缓存（包含裁剪和缩放信息）
_general_image_cache = {}  # 通用图片缓存

# 组件缓存管理器
class ComponentCacheManager:
    """组件缓存管理器 - 统一管理所有图片组件的缓存"""
    
    def __init__(self):
        self._overlay_cache = {}  # 统一遮罩图片缓存（文本框、名称框、额外组件）
        self._namebox_with_text_cache = {}  # 带文字的名称框缓存
        self._current_style_hash = ""  # 当前样式哈希，用于检测样式变化
    
    def get_overlay_cache(self, overlay_file: str, scale: float = 1.0) -> Optional[Image.Image]:
        """获取遮罩图片缓存"""
        cache_key = f"{overlay_file}_{scale}"
        return self._overlay_cache.get(cache_key)
    
    def set_overlay_cache(self, overlay_file: str, scale: float, image: Image.Image):
        """设置遮罩图片缓存"""
        cache_key = f"{overlay_file}_{scale}"
        self._overlay_cache[cache_key] = image.copy()
    
    def get_namebox_with_text_cache(self, character_name: str, overlay_file: str, scale: float = 1.0) -> Optional[Image.Image]:
        """获取带文字的名称框缓存"""
        cache_key = f"{character_name}_{overlay_file}_{scale}"
        return self._namebox_with_text_cache.get(cache_key)
    
    def set_namebox_with_text_cache(self, character_name: str, overlay_file: str, scale: float, image: Image.Image):
        """设置带文字的名称框缓存"""
        cache_key = f"{character_name}_{overlay_file}_{scale}"
        self._namebox_with_text_cache[cache_key] = image.copy()
    
    def clear_cache(self):
        """清理所有缓存"""
        self._overlay_cache.clear()
        self._namebox_with_text_cache.clear()
        print("组件缓存已清理")
    
    def update_style_hash(self):
        """更新样式哈希，用于检测样式变化"""
        # 创建样式的哈希值，基于关键配置
        style_data = {
            "aspect_ratio": CONFIGS.style.aspect_ratio,
            "font_family": CONFIGS.style.font_family,
            "textbox_config": {
                "x": CONFIGS.style.textbox_x,
                "y": CONFIGS.style.textbox_y,
                "width": CONFIGS.style.textbox_width,
                "height": CONFIGS.style.textbox_height
            },
            "image_components": CONFIGS.style.image_components
        }
        
        # 简单的哈希计算
        import hashlib
        style_str = str(style_data)
        new_hash = hashlib.md5(style_str.encode()).hexdigest()
        
        if new_hash != self._current_style_hash:
            self._current_style_hash = new_hash
            self.clear_cache()
            return True
        return False


# 全局组件缓存管理器实例
_component_cache_manager = ComponentCacheManager()

def get_component_cache_manager() -> ComponentCacheManager:
    """获取组件缓存管理器实例"""
    return _component_cache_manager

def get_image_path(base_name: str, sub_dir: str = "", with_ext: bool = True) -> str:
    """获取图片路径，支持多种格式"""
    supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
    
    for ext in supported_formats:
        if sub_dir:
            path = get_resource_path(os.path.join("assets", sub_dir, f"{base_name}{ext}"))
        else:
            path = get_resource_path(f"{base_name}{ext}")
        
        if os.path.exists(path):
            return path if with_ext else path[:-len(ext)]
    
    # 如果所有格式都不存在，返回默认png格式的路径
    if sub_dir:
        return get_resource_path(os.path.join("assets", sub_dir, f"{base_name}.png"))
    else:
        raise FileNotFoundError(f"{base_name}文件未找到")

def get_background_path(background_name: str) -> str:
    """获取背景图片路径"""
    return get_image_path(background_name, "background")

def get_character_path(character_name: str, emotion_index: int) -> str:
    """获取角色图片路径"""
    base_name = f"{character_name} ({emotion_index})"
    return get_image_path(base_name, os.path.join("chara", character_name))

def calculate_canvas_size() -> Tuple[int, int]:
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

def calculate_crop_box(img: Image.Image, target_width: int, target_height: int) -> Tuple[int, int, int, int]:
    """计算裁剪区域，确保图片填充目标尺寸"""
    img_width, img_height = img.size
    img_ratio = img_width / img_height
    target_ratio = target_width / target_height
    
    if img_ratio > target_ratio:
        # 图片比目标更宽，需要裁剪宽度
        crop_height = img_height
        crop_width = int(crop_height * target_ratio)
        
        # 水平居中裁剪
        left = (img_width - crop_width) // 2
        top = 0
        right = left + crop_width
        bottom = crop_height
    else:
        # 图片比目标更高，需要裁剪高度
        crop_width = img_width
        crop_height = int(crop_width / target_ratio)
        
        # 底部居中的裁剪位置（通常背景图底部更重要）
        left = 0
        top = img_height - crop_height
        right = crop_width
        bottom = img_height
    
    return (left, top, right, bottom)

# 预加载状态管理类
class PreloadManager:
    """预加载管理器"""
    def __init__(self):
        self._preload_status = {
            'total_items': 0,
            'loaded_items': 0,
            'is_complete': False
        }
        self._update_callback = None
        self._lock = threading.Lock()
        self._current_character = None       # 当前预加载的角色
        self._should_stop = threading.Event()  # 停止信号
        self._task_queue = queue.Queue(maxsize=2)  # 任务队列，最多存储2个任务
        
        # 新增：当前执行的任务信息
        self._current_task_type = None  # 当前正在执行的任务类型
        self._current_task_character = None  # 当前正在执行的角色任务的角色名
        self._interrupt_event = threading.Event()  # 中断当前任务的事件
        
        # 启动工作线程
        self._worker_thread = threading.Thread(
            target=self._preload_worker, 
            daemon=True,
            name="PreloadWorker"
        )
        self._worker_thread.start()
    
    def set_update_callback(self, callback: Callable[[str], None]):
        """设置状态更新回调"""
        self._update_callback = callback
    
    def update_status(self, message: str):
        """更新状态"""
        if self._update_callback:
            self._update_callback(message)

    def _preload_worker(self):
        """工作线程，持续处理预加载任务"""
        while not self._should_stop.is_set():
            try:
                # 等待有任务需要处理
                task = self._task_queue.get(timeout=0.1)
                
                task_type = task.get('type')
                
                # 设置当前执行的任务信息
                with self._lock:
                    self._current_task_type = task_type
                    if task_type == 'character':
                        self._current_task_character = task.get('character_name')
                    else:
                        self._current_task_character = None
                
                # 清除中断信号
                self._interrupt_event.clear()
                
                if task_type == 'character':
                    self._preload_character_task(task['character_name'])
                elif task_type == 'background':
                    self._preload_background_task()
                
                # 重置当前执行的任务信息
                with self._lock:
                    self._current_task_type = None
                    self._current_task_character = None
                
                # 标记任务完成
                self._task_queue.task_done()
                
            except queue.Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                self.update_status(f"预加载工作线程异常: {str(e)}")
                with self._lock:
                    self._current_task_type = None
                    self._current_task_character = None
    
    def _should_interrupt(self) -> bool:
        """检查是否应该中断当前任务"""
        return self._interrupt_event.is_set()
    
    def _preload_character_task(self, character_name: str):
        """预加载指定角色的所有表情图片，并进行预裁剪"""
        try:
            with self._lock:
                self._current_character = character_name
                self._preload_status['is_complete'] = False
            
            if character_name not in CONFIGS.mahoshojo:
                self.update_status(f"角色 {character_name} 配置不存在")
                return
            
            emotion_count = CONFIGS.mahoshojo[character_name]["emotion_count"]
            
            # 更新总项目数
            with self._lock:
                self._preload_status['total_items'] = emotion_count
                self._preload_status['loaded_items'] = 0
            
            self.update_status(f"开始预加载角色 {character_name}")
            
            # 计算角色组件配置
            character_component = None
            for component in CONFIGS.style.image_components:
                if component.get("type") == "character":
                    character_component = component
                    break
            
            if not character_component:
                self.update_status(f"找不到角色组件配置，跳过预加载 {character_name}")
                return
            
            # 预加载所有表情图片
            for emotion_index in range(1, emotion_count + 1):
                # 检查是否需要中断
                if self._should_interrupt():
                    self.update_status(f"角色 {character_name} 预加载被中断")
                    return
                
                # 加载并预处理角色图片
                self._preload_character_image(character_name, emotion_index, character_component)
                
                # 更新已加载项目数
                with self._lock:
                    self._preload_status['loaded_items'] = emotion_index
                
                # 实时更新进度
                progress = emotion_index / emotion_count
                if self._update_callback:
                    self.update_status(f"预加载角色 {character_name}: {emotion_index}/{emotion_count} ({progress:.0%})")
            
            with self._lock:
                self._preload_status['is_complete'] = True
            
            self.update_status(f"角色 {character_name} 预加载完成")
            
        except Exception as e:
            self.update_status(f"角色 {character_name} 预加载失败: {str(e)}")
            with self._lock:
                self._preload_status['is_complete'] = True
    
    def _preload_character_image(self, character_name: str, emotion_index: int, component: dict):
        """预加载单个角色图片并进行预处理"""
        cache_key = f"{character_name}_{emotion_index}"
        
        if cache_key in _character_cache:
            return _character_cache[cache_key]
        
        try:
            # 获取角色图片路径
            character_path = get_character_path(character_name, emotion_index)
            img = Image.open(character_path).convert("RGBA")
            
            # 应用总缩放因子（角色自身缩放 × 组件缩放）
            character_scale = CONFIGS.current_character.get("scale", 1.0)
            component_scale = component.get("scale", 1.0)
            total_scale = character_scale * component_scale
            
            if total_scale != 1.0:
                original_width, original_height = img.size
                new_width = int(original_width * total_scale)
                new_height = int(original_height * total_scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 缓存处理后的图片
            _character_cache[cache_key] = img
            return img
            
        except FileNotFoundError:
            # 创建默认透明图片
            default_img = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
            _character_cache[cache_key] = default_img
            return default_img
    
    def _preload_background_task(self):
        """预加载所有背景图片，并进行预裁剪"""
        try:
            self.update_status("正在预加载背景图片...")
            
            # 计算画布尺寸
            canvas_width, canvas_height = calculate_canvas_size()
            
            background_count = CONFIGS.background_count
            
            for background_index in range(1, background_count + 1):
                # 检查是否需要中断
                if self._should_interrupt():
                    self.update_status("背景图片预加载被中断")
                    return
                
                # 预加载背景图片
                self._preload_background_image(f"c{background_index}", canvas_width, canvas_height)
                
                # 实时更新进度
                progress = background_index / background_count
                if background_index % 5 == 0 or background_index == background_count:
                    self.update_status(f"预加载背景: {background_index}/{background_count} ({progress:.0%})")
            
            self.update_status("背景图片预加载完成")
        except Exception as e:
            self.update_status(f"背景图片预加载失败: {str(e)}")
    
    def _preload_background_image(self, background_name: str, canvas_width: int, canvas_height: int):
        """预加载单个背景图片并进行预处理"""
        cache_key = f"{background_name}_{canvas_width}_{canvas_height}"
        
        if cache_key in _background_cache:
            return _background_cache[cache_key]
        
        try:
            # 获取背景图片路径
            background_path = get_background_path(background_name)
            img = Image.open(background_path).convert("RGBA")
            
            # 计算裁剪区域并裁剪
            crop_box = calculate_crop_box(img, canvas_width, canvas_height)
            img = img.crop(crop_box).resize(
                (canvas_width, canvas_height), 
                Image.Resampling.LANCZOS
            )
            
            # 缓存处理后的图片
            _background_cache[cache_key] = img
            return img
            
        except FileNotFoundError:
            # 创建默认图片
            default_img = Image.new("RGBA", (canvas_width, canvas_height), (100, 100, 200))
            _background_cache[cache_key] = default_img
            return default_img

    def submit_preload_task(self, task_type: str, **kwargs) -> bool:
        """
        提交预加载任务的通用方法
        
        Args:
            task_type: 任务类型 ('character' 或 'background')
            **kwargs: 任务参数
                - character_name: 角色名称（仅用于角色预加载）
        
        Returns:
            bool: 是否成功提交任务
        """
        try:
            # 构建任务
            if task_type == 'character':
                if 'character_name' not in kwargs:
                    self.update_status("角色预加载任务缺少角色名称参数")
                    return False
                
                character_name = kwargs['character_name']
                task = {
                    'type': 'character', 
                    'character_name': character_name
                }
                task_desc = f"角色 {character_name}"
                
                # 检查当前是否有同类型的角色任务正在执行
                with self._lock:
                    current_task_type = self._current_task_type
                    current_task_character = self._current_task_character
                
                # 如果当前正在执行的是角色任务，则中断它
                if current_task_type == 'character':
                    self._interrupt_event.set()
                    self.update_status(f"中断当前角色任务以加载 {character_name}")
                    # 给一点时间让任务响应中断
                    time.sleep(0.1)
                
            elif task_type == 'background':
                task = {'type': 'background'}
                task_desc = "背景图片"
                
                # 如果当前正在执行的是背景任务，则不需要中断
                # 背景任务通常较快，且可以继续执行
            else:
                self.update_status(f"未知的预加载任务类型: {task_type}")
                return False
            
            # 处理队列中的任务
            if self._task_queue.full():
                # 根据任务类型决定处理策略
                temp_tasks = []
                try:
                    # 遍历队列，处理不同类型的任务
                    while not self._task_queue.empty():
                        existing_task = self._task_queue.get_nowait()
                        
                        # 如果是角色任务且当前提交的也是角色任务，则丢弃旧的
                        if existing_task.get('type') == task_type == 'character':
                            # 丢弃同类型的旧任务
                            self._task_queue.task_done()
                            self.update_status(f"丢弃旧的{task_desc}预加载任务，替换为新任务")
                        # 如果是背景任务且当前提交的是角色任务，则保留背景任务
                        elif existing_task.get('type') == 'background' and task_type == 'character':
                            temp_tasks.append(existing_task)
                        # 如果是角色任务且当前提交的是背景任务，则保留角色任务
                        elif existing_task.get('type') == 'character' and task_type == 'background':
                            temp_tasks.append(existing_task)
                        else:
                            # 其他情况丢弃
                            self._task_queue.task_done()
                            
                except queue.Empty:
                    pass
                
                # 将需要保留的任务放回队列
                for temp_task in temp_tasks:
                    try:
                        self._task_queue.put_nowait(temp_task)
                    except queue.Full:
                        # 如果队列已满，则丢弃最不重要的任务
                        break
            
            # 放入新任务
            try:
                self._task_queue.put_nowait(task)
                self.update_status(f"已提交{task_desc}预加载任务")
                return True
            except queue.Full:
                self.update_status(f"{task_desc}预加载任务队列已满，任务被丢弃")
                return False
                
        except Exception as e:
            self.update_status(f"提交{task_type}预加载任务失败: {str(e)}")
            return False
    
    def clear_caches(self, cache_type: str = "all"):
        """清理特定类型的缓存"""
        global _background_cache, _character_cache, _general_image_cache
        
        if cache_type in ("background", "all"):
            _background_cache.clear()
            print("背景缓存已清理")
        
        if cache_type in ("character", "all"):
            _character_cache.clear()
            print("角色缓存已清理")
        
        if cache_type in ("image", "all"):
            _general_image_cache.clear()
            print("通用图片缓存已清理")
        
        if cache_type in ("component", "all"):
            get_component_cache_manager().clear_cache()
    
    def get_preload_progress(self) -> float:
        """获取预加载进度"""
        with self._lock:
            if self._preload_status['total_items'] == 0:
                return 0.0
            
            progress = self._preload_status['loaded_items'] / self._preload_status['total_items']
            return min(progress, 1.0)
    
    def get_preload_status(self) -> Dict[str, Any]:
        """获取预加载状态"""
        with self._lock:
            return {
                'loaded_items': self._preload_status['loaded_items'],
                'total_items': self._preload_status['total_items'],
                'is_complete': self._preload_status['is_complete'],
                'current_character': self._current_character,
                'current_task_type': self._current_task_type,
                'current_task_character': self._current_task_character
            }

# 缓存字体
def load_font_cached(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """使用字体名称加载字体，支持多种格式（TTF、OTF等）"""
    cache_key = f"{font_name}_{size}"
    if cache_key not in _font_cache:
        # 获取字体路径（支持多种格式）
        font_path = get_font_path(font_name)
        
        if os.path.exists(font_path):
            try:
                _font_cache[cache_key] = ImageFont.truetype(font_path, size=size)
            except Exception as e:
                print(f"字体加载失败: {font_path}, 错误: {e}")
                return ImageFont.truetype(font_path, size=size)
        else:
            print(f"字体文件不存在: {font_path}")
            return ImageFont.truetype(font_path, size=size)
    
    return _font_cache[cache_key]

def load_image_cached(image_path: str) -> Image.Image:
    """通用图片缓存加载，支持透明通道"""
    cache_key = image_path
    if cache_key not in _general_image_cache:
        if image_path and os.path.exists(image_path):
            _general_image_cache[cache_key] = Image.open(image_path).convert("RGBA")
        else:
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
    return _general_image_cache[cache_key].copy()

# 安全加载背景图片（使用预裁剪的缓存）
def load_background_safe(background_name: str) -> Image.Image:
    """安全加载背景图片，使用预裁剪的缓存"""
    # 计算画布尺寸
    canvas_width, canvas_height = calculate_canvas_size()
    cache_key = f"{background_name}_{canvas_width}_{canvas_height}"
    
    if cache_key in _background_cache:
        return _background_cache[cache_key].copy()
    
    # 如果缓存中没有，尝试从文件加载并裁剪
    preload_manager = get_preload_manager()
    return preload_manager._preload_background_image(background_name, canvas_width, canvas_height)

# 安全加载角色图片（使用预处理后的缓存）
def load_character_safe(character_name: str, emotion_index: int) -> Image.Image:
    """安全加载角色图片，使用预处理后的缓存"""
    cache_key = f"{character_name}_{emotion_index}"
    
    if cache_key in _character_cache:
        return _character_cache[cache_key].copy()
    
    # 如果缓存中没有，尝试从文件加载并处理
    preload_manager = get_preload_manager()
    
    # 查找角色组件配置
    character_component = None
    for component in CONFIGS.style.image_components:
        if component.get("type") == "character":
            character_component = component
            break
    
    if not character_component:
        # 创建默认透明图片
        default_img = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
        return default_img
    
    return preload_manager._preload_character_image(character_name, emotion_index, character_component)

def clear_cache(cache_type: str = "all"):
    """清理特定类型的缓存 - 已弃用，请使用PreloadManager.clear_caches()"""
    get_preload_manager().clear_caches(cache_type)

# 创建全局预加载管理器实例
_preload_manager = PreloadManager()

def get_preload_manager() -> PreloadManager:
    """获取预加载管理器实例"""
    return _preload_manager