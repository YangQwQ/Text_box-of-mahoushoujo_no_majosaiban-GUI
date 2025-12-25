"""文件加载工具"""
import os
import threading
import queue
from PIL import ImageFont, Image
from typing import Callable, Tuple
import time

from path_utils import get_resource_path, get_font_path
from config import CONFIGS

class UnifiedImageCacheManager:
    """统一的图片缓存管理器"""
    
    def __init__(self):
        # 核心缓存
        self._font_cache = {}
        self._background_cache = {}    # 背景图片缓存（包含裁剪信息）
        self._character_cache = {}     # 角色图片缓存（包含裁剪和缩放信息）
        self._general_image_cache = {} # 通用图片缓存
        self._cached_layers_sequence = []  # 缓存的图层序列
    
    def clear_cache(self, cache_type: str = "all"):
        """清理指定类型的缓存"""
        if cache_type in ("background", "all"):
            self._background_cache.clear()
            print("背景缓存已清理")
        
        if cache_type in ("character", "all"):
            self._character_cache.clear()
            print("角色缓存已清理")
        
        if cache_type in ("image", "all"):
            self._general_image_cache.clear()
            print("通用图片缓存已清理")
        
        if cache_type in ("layers", "all"):
            self._cached_layers_sequence.clear()
            print("图层序列缓存已清理")
        
    # 背景缓存相关方法
    def get_background(self, cache_key: str):
        """获取背景缓存"""
        if cache_key in self._background_cache:
            return self._background_cache[cache_key]
        return None
    
    def set_background(self, cache_key: str, image: Image.Image):
        """设置背景缓存"""
        self._background_cache[cache_key] = image
    
    # 角色缓存相关方法
    def get_character(self, cache_key: str):
        """获取角色缓存"""
        if cache_key in self._character_cache:
            return self._character_cache[cache_key]
        return None
    
    def set_character(self, cache_key: str, image: Image.Image):
        """设置角色缓存"""
        self._character_cache[cache_key] = image
    
    # 通用图片缓存相关方法
    def get_image(self, cache_key: str):
        """获取通用图片缓存"""
        if cache_key in self._general_image_cache:
            return self._general_image_cache[cache_key]
        return None
    
    def set_image(self, cache_key: str, image: Image.Image):
        """设置通用图片缓存"""
        self._general_image_cache[cache_key] = image
    
    # 字体缓存相关方法
    def get_font(self, cache_key: str):
        """获取字体缓存"""
        return self._font_cache.get(cache_key)
    
    def set_font(self, cache_key: str, font: ImageFont.FreeTypeFont):
        """设置字体缓存"""
        self._font_cache[cache_key] = font
    
    # 图层序列缓存相关方法
    @property
    def cached_layers_sequence(self):
        """获取缓存的图层序列"""
        return self._cached_layers_sequence
    
    @cached_layers_sequence.setter
    def cached_layers_sequence(self, value):
        """设置缓存的图层序列"""
        self._cached_layers_sequence = value

# 全局缓存管理器实例
_unified_cache_manager = UnifiedImageCacheManager()

def get_unified_cache_manager() -> UnifiedImageCacheManager:
    """获取统一缓存管理器实例"""
    return _unified_cache_manager

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
        height = 2048
    elif ratio == "16:9":
        height = 1440
    else:  # "3:1" 或默认
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

def calculate_component_position(canvas_width: int, canvas_height: int, 
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

def apply_fill_mode(image: Image.Image, target_width: int, target_height: int, 
                   fill_mode: str = "fit") -> Image.Image:
    """应用填充模式到图片"""
    img_width, img_height = image.size
    
    if fill_mode == "fit":
        # 适应边界：如果图片尺寸大于目标尺寸，则缩小；如果小于，则保持原尺寸
        if img_width > target_width or img_height > target_height:
            # 图片太大，需要缩小
            width_ratio = target_width / img_width
            height_ratio = target_height / img_height
            ratio = min(width_ratio, height_ratio)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # 如果图片比目标小，不放大
    elif fill_mode == "width":
        # 适应宽度：将图片宽度调整到与目标宽度一致
        if img_width != target_width:
            ratio = target_width / img_width
            new_height = int(img_height * ratio)
            image = image.resize((target_width, new_height), Image.Resampling.LANCZOS)
    elif fill_mode == "height":
        # 适应高度：将图片高度调整到与目标高度一致
        if img_height != target_height:
            ratio = target_height / img_height
            new_width = int(img_width * ratio)
            image = image.resize((new_width, target_height), Image.Resampling.LANCZOS)
    
    return image

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

        self._unified_cache = get_unified_cache_manager()
        
        # 新增：用于在主线程中安全执行回调
        self._main_thread_callback_queue = queue.Queue()
        self._main_thread_callback_running = False

        # 启动工作线程
        self._worker_thread = threading.Thread(
            target=self._preload_worker, 
            daemon=True,
            name="PreloadWorker"
        )
        self._worker_thread.start()
        
        # 启动主线程回调处理器
        self._start_main_thread_callback_processor()
    
    def _start_main_thread_callback_processor(self):
        """启动主线程回调处理器（在主线程中调用）"""
        # 这个方法将在主线程中被调用
        self._main_thread_callback_running = True
    
    def _safe_update_status(self, message: str):
        """安全更新状态 - 将回调放入队列，由主线程处理"""
        if self._update_callback and message:
            # 将消息放入队列
            self._main_thread_callback_queue.put(message)
    
    def process_main_thread_callbacks(self):
        """处理主线程回调 - 这个方法需要在主线程中定期调用"""
        if not self._main_thread_callback_running:
            return
            
        try:
            # 处理队列中的所有回调
            while True:
                try:
                    message = self._main_thread_callback_queue.get_nowait()
                    if self._update_callback:
                        try:
                            self._update_callback(message)
                        except Exception as e:
                            print(f"更新状态回调失败: {str(e)}")
                except queue.Empty:
                    break
        except Exception as e:
            print(f"处理主线程回调失败: {str(e)}")
    
    def set_update_callback(self, callback: Callable[[str], None]):
        """设置状态更新回调"""
        self._update_callback = callback
    
    def update_status(self, message: str):
        """更新状态 - 工作线程使用这个安全版本"""
        self._safe_update_status(message)

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
            
            # 获取所有角色组件的配置
            character_components = []
            for component in CONFIGS.style.image_components:
                if component.get("type") == "character":
                    character_components.append(component)
            
            # 预加载所有表情图片
            for emotion_index in range(1, emotion_count + 1):
                # 检查是否需要中断
                if self._should_interrupt():
                    self.update_status(f"角色 {character_name} 预加载被中断")
                    return
                
                # 为每个角色组件预加载（不同组件可能有不同缩放）
                for component in character_components:
                    # 检查是否使用固定角色
                    use_fixed_character = component.get("use_fixed_character", False)
                    if use_fixed_character:
                        # 如果是固定角色，检查是否匹配当前角色
                        fixed_char_name = component.get("character_name", "")
                        if fixed_char_name != character_name:
                            continue
                    
                    # 加载并预处理角色图片
                    self._preload_character_image(character_name, emotion_index, component)
                
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
        # 创建缓存键
        cache_key = f"{character_name}_{emotion_index}_{component.get('scale', 1.0)}"

        # 检查统一缓存
        cached_character = self._unified_cache.get_character(cache_key)
        if cached_character is not None:
            return cached_character
        
        try:
            # 获取角色图片路径
            character_path = get_character_path(character_name, emotion_index)
            img = Image.open(character_path).convert("RGBA")
            
            # 获取角色配置中的缩放（无论是否固定角色都需要）
            character_config = CONFIGS.mahoshojo.get(character_name, {})
            character_scale = character_config.get("scale", 1.0)
            
            # 获取组件缩放
            component_scale = component.get("scale", 1.0)
            
            # 计算总缩放 = 角色配置缩放 × 组件缩放
            total_scale = character_scale * component_scale
            
            # 应用总缩放
            if total_scale != 1.0:
                original_width, original_height = img.size
                new_width = int(original_width * total_scale)
                new_height = int(original_height * total_scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 保存到统一缓存
            self._unified_cache.set_character(cache_key, img)
            return img
            
        except FileNotFoundError:
            # 创建默认透明图片
            default_img = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
            self._unified_cache.set_character(cache_key, default_img)
            return default_img
        
    def _preload_background_task(self):
        """预加载所有背景图片"""
        try:
            self.update_status("正在预加载背景图片...")
            components = CONFIGS.style_configs.get(CONFIGS.gui_settings.get("last_style","default"), {}).get("image_components",{})
            total_to_process = 1
            total_processed = 0
            # 从所有样式配置中收集背景组件
            for component in components:
                if component.get("type") == "background" and component.get("enabled", True):
                    if  not component.get("use_fixed_background", False):
                        total_to_process = CONFIGS.background_count
                        for file_index in range(total_to_process):
                            if self._should_interrupt():
                                self.update_status("背景图片预加载被中断")
                                return
                            if components != CONFIGS.style_configs.get(CONFIGS.gui_settings.get("last_style","default"), {}).get("image_components",{}):
                                self.update_status("背景图片预加载中断")
                                return
                            component["overlay"] = f"c{file_index + 1}"
                            load_background_component_safe(component)
                            total_processed += 1
                            
                            # 实时更新进度
                            progress = total_processed / total_to_process
                            self.update_status(f"预加载背景 ({total_processed}/{total_to_process}) ({progress:.0%})")
                    else:
                        load_background_component_safe(component)
                        total_processed += 1
                        break
            self.update_status("背景图片预加载完成")
        except Exception as e:
            self.update_status(f"背景图片预加载失败: {str(e)}")
            
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

# 缓存字体
def load_font_cached(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """使用字体名称加载字体，支持多种格式（TTF、OTF等）"""
    cache_key = f"{font_name}_{size}"
    cache_manager = get_unified_cache_manager()
    
    font = cache_manager.get_font(cache_key)
    if font is not None:
        return font
    
    # 获取字体路径（支持多种格式）
    font_path = get_font_path(font_name)
    
    if os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, size=size)
            cache_manager.set_font(cache_key, font)
            return font
        except Exception as e:
            print(f"字体加载失败: {font_path}, 错误: {e}")
            return ImageFont.truetype(font_path, size=size)
    else:
        print(f"字体文件不存在: {font_path}")
        return ImageFont.truetype(font_path, size=size)

def load_image_cached(image_path: str) -> Image.Image:
    """通用图片缓存加载，支持透明通道"""
    cache_manager = get_unified_cache_manager()
    
    cached_image = cache_manager.get_image(image_path)
    if cached_image is not None:
        return cached_image.copy()
    
    if image_path and os.path.exists(image_path):
        image = Image.open(image_path).convert("RGBA")
        cache_manager.set_image(image_path, image)
        return image.copy()
    else:
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

def load_background_component_safe(component: dict) -> Image.Image:
    """安全加载背景组件图片 - 统一处理逻辑"""
    canvas_width, canvas_height = calculate_canvas_size()
    if  not component or not component.get("enabled", True):
        return Image.new("RGBA", (canvas_width, canvas_height), color="black")

    overlay_file = component.get("overlay", "")
    scale = component.get("scale", 1.0)
    fill_mode = component.get("fill_mode", "fit")
    align = component.get("align", "top-left")
    offset_x = component.get("offset_x", 0)
    offset_y = component.get("offset_y", 0)
    
    cache_key = f"bg_component_{overlay_file}_{canvas_width}_{canvas_height}"
    cache_manager = get_unified_cache_manager()
    
    # 检查缓存
    cached_bg = cache_manager.get_background(cache_key)
    if cached_bg is not None:
        return cached_bg.copy()

    if not overlay_file or overlay_file == "":
        return Image.new("RGBA", (canvas_width, canvas_height), color="black")
    
    # 查找背景文件
    # 先在background文件夹中查找
    overlay_path = get_background_path(overlay_file.split(".")[0])
    if not os.path.exists(overlay_path):
        # 如果在background文件夹没找到，尝试shader文件夹
        overlay_path = get_resource_path(os.path.join("assets", "shader", overlay_file))
        if not os.path.exists(overlay_path):
            # 如果都不存在，创建透明背景
            return Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    
    # 加载背景图片
    try:
        bg_img = Image.open(overlay_path).convert("RGBA")
        img_width, img_height = bg_img.size

        # 确定目标尺寸 - 修复填充模式逻辑
        if fill_mode == "fit":
            # 适应边界：如果图片尺寸大于目标尺寸，则缩小；如果小于，则保持原尺寸
            if img_width > canvas_width or img_height > canvas_height:
                # 图片太大，需要缩小到适应画布
                width_ratio = canvas_width / img_width
                height_ratio = canvas_height / img_height
                ratio = min(width_ratio, height_ratio)
                target_width = int(img_width * ratio)
                target_height = int(img_height * ratio)
            else:
                # 图片比画布小，不放大
                target_width = img_width
                target_height = img_height
        elif fill_mode == "width":
            # 适应宽度：将图片宽度调整到与目标宽度一致
            target_width = canvas_width
            target_height = int(img_height * (canvas_width / img_width))
        elif fill_mode == "height":
            # 适应高度：将图片高度调整到与目标高度一致
            target_height = canvas_height
            target_width = int(img_width * (canvas_height / img_height))
        else:
            # 默认适应边界
            if img_width > canvas_width or img_height > canvas_height:
                width_ratio = canvas_width / img_width
                height_ratio = canvas_height / img_height
                ratio = min(width_ratio, height_ratio)
                target_width = int(img_width * ratio)
                target_height = int(img_height * ratio)
            else:
                target_width = img_width
                target_height = img_height

        # 如果图片尺寸与目标尺寸不同，调整图片
        if (target_width, target_height) != (img_width, img_height):
            bg_img = bg_img.resize((int(target_width * scale), int(target_height * scale)), Image.Resampling.BILINEAR)

        # 计算对齐位置
        bg_width, bg_height = bg_img.size
        paste_x, paste_y = calculate_component_position(
            canvas_width, canvas_height,
            bg_width, bg_height,
            align,
            offset_x,
            offset_y
        )

        # 创建画布并粘贴
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
        canvas.paste(bg_img, (paste_x, paste_y), bg_img)
        bg_img = canvas

        # 调整尺寸保存
        pre_resize = CONFIGS.gui_settings.get("pre_resize", 2560)
        if (bg_width)!= pre_resize:
            bg_img = bg_img.resize((pre_resize, int(pre_resize * canvas_height/canvas_width)), Image.Resampling.LANCZOS)

        # 保存到缓存
        cache_manager.set_background(cache_key, bg_img)

        return bg_img.copy()
        
    except Exception as e:
        print(f"加载背景组件失败: {overlay_path}, 错误: {e}")
        return Image.new("RGB", (canvas_width, canvas_height), color="black")

def load_character_safe(character_name: str, emotion_index: int, component: dict = None) -> Image.Image:
    """安全加载角色图片，使用预处理后的缓存"""
    # 如果没有提供组件配置，查找角色组件
    if component is None:
        character_component = None
        for comp in CONFIGS.style.image_components:
            if comp.get("type") == "character":
                character_component = comp
                break
        
        if not character_component:
            # 创建默认透明图片
            default_img = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
            return default_img
        
        component = character_component
    
    # 创建缓存键
    preload_manager = get_preload_manager()
    cache_key = f"{character_name}_{emotion_index}_{component.get('scale', 1.0)}"
    
    cache_manager = get_unified_cache_manager()
    
    cached_character = cache_manager.get_character(cache_key)
    if cached_character is not None:
        return cached_character.copy()
    
    # 如果缓存中没有，尝试从文件加载并处理
    character_image = preload_manager._preload_character_image(character_name, emotion_index, component)
    return character_image.copy()

# 创建全局预加载管理器实例
_preload_manager = PreloadManager()

def get_preload_manager() -> PreloadManager:
    """获取预加载管理器实例"""
    return _preload_manager