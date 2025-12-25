"""配置管理模块"""
import os
from typing import Dict, Any, Optional
import yaml
import json
from sys import platform
from path_utils import get_base_path, get_resource_path, ensure_path_exists

class StyleConfig:
    """样式配置类"""
    
    def __init__(self):
        self.default_config = self._load_default_style_config() # 默认配置文件的内容格式和styles.yml基本一致
        if self.default_config:
            default = self.default_config.get("default", {})
            # 设置属性
            for key, value in default.items():
                setattr(self, key, value)

    def _load_default_style_config(self):
        """从 defaultstyle.yml 加载默认样式配置"""
        try:
            filepath = get_resource_path(os.path.join("config", "defaultstyle.yml"))
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                print(f"警告：默认样式文件不存在: {filepath}")
                return None
        except Exception as e:
            print(f"加载默认样式配置失败: {e}")
            return None
    
    def get_bracket_color(self, character_name=None):
        """获取强调色，根据是否使用角色颜色返回不同的颜色"""
        if self.use_character_color and character_name:
            # 使用角色颜色
            from config import CONFIGS
            if character_name in CONFIGS.text_configs_dict and CONFIGS.text_configs_dict[character_name]:
                first_config = CONFIGS.text_configs_dict[character_name][0]
                font_color = first_config.get("font_color", (239, 79, 84))
                return f"#{font_color[0]:02x}{font_color[1]:02x}{font_color[2]:02x}"
        
        # 返回配置的强调色
        return self.bracket_color

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, base_path=None):
        # 如果没有提供base_path，使用自动检测的路径
        self.base_path = base_path if base_path else get_base_path()
        self.config_path = get_resource_path("config")

        self.config = AppConfig(os.path.dirname(os.path.abspath(__file__)))

        # 规范化平台键
        self.platform = platform
        if platform.startswith('win'):
            self.platform = 'win32'
        elif platform == 'darwin':
            self.platform = 'darwin'
        else:
            self.platform = 'win32'

        # 情感匹配相关
        self.emotion_list = ["平静", "喜悦", "喜爱", "惊讶", "困惑", "无语", "悲伤", "愤怒", "恐惧"]

        # 当前预览相关
        self.current_character_index = 2

        # 状态变量(为None时为随机选择,否则为手动选择)
        self.selected_emotion = None
        self.selected_background = None
        
        # 样式配置
        self.style_configs = {}
        self.current_style = "default"
        self.style = StyleConfig()

        # 加载版本信息
        self.version_info = self.load_version_info()
        # 设置版本号属性
        self.version = self.version_info["version"] # 需要存在version.yml文件

        # 配置加载
        self.mahoshojo = self.load_config("chara_meta")
        self.text_configs_dict = self.load_config("text_configs")
        self.character_list = list(self.mahoshojo.keys())
        self.current_character = self.mahoshojo[self.character_list[self.current_character_index - 1]]
        self.keymap = self.load_config("keymap")
        self.process_whitelist = self.load_config("process_whitelist")
        self.gui_settings = self.load_config("settings")

        # 确保enabled只有在display为True时才可能为True
        sm = self.gui_settings["sentiment_matching"]
        sm["enabled"] &= sm["display"]
        self.ai_models = self.gui_settings.get("sentiment_matching", {}).get("model_configs", {})

        self.background_count = self._get_background_count()  # 背景图片数量
        
        # 加载样式配置
        self._load_style_configs()

    def apply_style(self, style_name: str):
        """应用指定的样式配置"""
        if style_name in self.style_configs:
            style_data = self.style_configs[style_name]
            self.current_style = style_name
            
            # 更新样式对象
            for key, value in style_data.items():
                if hasattr(self.style, key):
                    setattr(self.style, key, value)
            
            # 如果使用角色颜色作为强调色，更新强调色
            if self.style.use_character_color:
                self._update_bracket_color_from_character()
            
            # 保存上次选择的样式到GUI设置
            self.gui_settings["last_style"] = style_name
            self.save_gui_settings()

    def update_style(self, style_name: str, style_data: Dict[str, Any]):
        """更新样式配置"""
        if style_name in self.style_configs:
            # 确保有image_components字段
            if "image_components" not in style_data:
                style_data["image_components"] = self.style_configs[style_name].get("image_components", [])
            
            self.style_configs[style_name] = style_data
            
            # 如果更新的是当前样式，立即应用
            if self.current_style == style_name:
                self.apply_style(style_name)
                
            return self.save_style_configs()
        return False
    
    def _load_style_configs(self):
        """加载样式配置"""
        # 加载styles.yml文件
        styles_data = self._load_yaml_file("styles.yml") or {}
        
        if not styles_data:
            # 如果没有样式配置，创建默认配置
            styles_data = {"default": self.style.default_config.get("default", {})}
            self._save_yaml_file("styles.yml", styles_data)
        
        self.style_configs = styles_data
        self.current_style = self.gui_settings.get("last_style","default")
        
        # 应用当前样式
        self.apply_style(self.current_style)
    
    def _update_bracket_color_from_character(self):
        """根据当前角色的文本颜色更新强调色"""
        character_name = self.get_character()
        if character_name in self.text_configs_dict and self.text_configs_dict[character_name]:
            # 获取第一个文本配置的颜色
            first_config = self.text_configs_dict[character_name][0]
            font_color = first_config.get("font_color", (255, 255, 255))
            # 将RGB转换为十六进制
            self.style.bracket_color = f"#{font_color[0]:02x}{font_color[1]:02x}{font_color[2]:02x}"

    def _get_background_count(self) -> int:
        """动态获取背景图片数量"""
        try:
            background_dir = get_resource_path(os.path.join("assets", "background"))
            if os.path.exists(background_dir):
                # 统计所有c开头的背景图片
                bg_files = [f for f in os.listdir(background_dir) if f.lower().startswith('c')]
                return len(bg_files)
            else:
                print(f"警告：背景图片目录不存在: {background_dir}")
                return 0
        except Exception as e:
            print(f"获取背景数量失败: {e}")
            return 0
    
    def reload_configs(self):
        """重新加载配置（用于热键更新后）"""
        # 重新加载快捷键映射
        self.keymap = self.load_config("keymap")
        # 重新加载进程白名单
        self.process_whitelist = self.load_config("process_whitelist")
        # 重新加载GUI设置
        self.gui_settings = self.load_config("settings")

    def load_config(self, config_type: str, *args) -> Any:
        """
        通用配置加载函数
        
        Args:
            config_type: 配置类型，支持: 'chara_meta', 'text_configs', 
                        'keymap', 'process_whitelist', 'settings'
            *args: 额外参数，如平台类型或配置键名
        
        Returns:
            配置数据
        """
        config_list = ["chara_meta", "text_configs", "keymap", "process_whitelist", "settings"]
        if config_type not in config_list:
            raise ValueError(f"不支持的配置类型: {config_type}")
        
        # 加载配置文件
        config = self._load_yaml_file(f"{config_type}.yml")
        
        if config_type in ["keymap", "process_whitelist"]:
            # 处理平台特定配置
            if config:
                config = config.get(self.platform, {})
            else:
                config = self._get_default_setting(config_type)
        elif config_type == "settings":
            # 处理settings配置，确保所有字段都存在
            default_settings = self._get_default_setting("settings")
            if config:
                # 递归合并默认值和文件配置
                default_settings |= config
                config = default_settings
            else:
                config = default_settings
                self.gui_settings = config
                self.save_gui_settings()
        
        return config
    
    def _get_default_setting(self, config_type: str) -> Dict[str, Any]:
        """获取默认设置"""
        # print(f"获取默认配置：{config_type}")

        if config_type == "settings":
            return {
                "pre_resize": 1080,
                "preloading": {
                "preload_character": True,
                "preload_background": True,
                },
                "cut_settings": {
                    "cut_mode": "全选剪切"
                },
                "image_compression": {
                    "pixel_reduction_enabled": True,
                    "pixel_reduction_ratio": 40
                },
                "quick_characters": {
                    "character_1": "ema",
                    "character_2": "hiro", 
                    "character_3": "sherry",
                    "character_4": "yuki",
                    "character_5": "meruru",
                    "character_6": "reia"
                },
                "sentiment_matching": {
                    "display": False,
                    "enabled": False,
                    "ai_model": "ollama",
                    "model_configs": {
                        "chatGPT": {
                            "api_key": '',
                            "base_url": "https://api.openai.com/v1/",
                            "model": "gpt-3.5-turbo"
                        },
                        "deepseek": {
                            "api_key": '',
                            "base_url": "https://api.deepseek.com",
                            "model": "deepseek-chat"
                        },
                        "ollama": {
                            "api_key": '',
                            "base_url": "http://localhost:11434/v1/",
                            "model": "OmniDimen"
                        }
                    }
                }
            }
        elif config_type == "keymap":
            if self.platform == "win32":
                return {
                    "start_generate": "<ctrl>+e",
                    "next_character": "<ctrl>+<shift>+l",
                    "prev_character": "<ctrl>+<shift>+j",
                    "next_emotion": "<ctrl>+<shift>+o",
                    "prev_emotion": "<ctrl>+<shift>+u",
                    "next_background": "<ctrl>+<shift>+k",
                    "prev_background": "<ctrl>+<shift>+i",
                    "toggle_listener": "<ctrl>+<alt>+p",
                    "character_1": "<ctrl>+1",
                    "character_2": "<ctrl>+2",
                    "character_3": "<ctrl>+3",
                    "character_4": "<ctrl>+4",
                    "character_5": "<ctrl>+5",
                    "character_6": "<ctrl>+6"
                }
            elif self.platform == "darwin":
                return {
                        "start_generate": "<cmd>+e",
                        "next_character": "<cmd>+<shift>+l",
                        "prev_character": "<cmd>+<shift>+j",
                        "next_emotion": "<cmd>+<shift>+o",
                        "prev_emotion": "<cmd>+<shift>+u",
                        "next_background": "<cmd>+<shift>+k",
                        "prev_background": "<cmd>+<shift>+i",
                        "toggle_listener": "<cmd>+<alt>+p",
                        "character_1": "<cmd>+1",
                        "character_2": "<cmd>+2",
                        "character_3": "<cmd>+3",
                        "character_4": "<cmd>+4",
                        "character_5": "<cmd>+5",
                        "character_6": "<cmd>+6"
                    }
        else:
            return {}

    def _load_yaml_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """通用YAML文件加载函数"""
        filepath = get_resource_path(os.path.join("config", filename))
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding="utf-8") as fp:
                return yaml.safe_load(fp) or {}
        except Exception as e:
            print(f"加载配置文件 {filename} 失败: {e}")
            return None
    
    def _save_yaml_file(self, filename: str, data: Dict[str, Any]) -> bool:
        """通用YAML文件保存函数"""
        try:
            filepath = ensure_path_exists(get_resource_path(os.path.join("config", filename)))
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            print(f"保存配置文件 {filename} 失败: {e}")
            return False

    def get_character(self, index: str | None = None, full_name: bool = False) -> str:
        """获取角色名称"""
        if index is not None:
            return self.mahoshojo[index]["full_name"] if full_name else index
        else:
            chara = self.character_list[self.current_character_index - 1]
            return self.mahoshojo[chara]["full_name"] if full_name else chara
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """获取可用模型配置"""
        # 直接从配置中获取，无需额外处理
        model_configs = self.gui_settings.get("sentiment_matching", {}).get("model_configs", {})
        
        # 构建模型信息字典
        available_models = {}
        model_descriptions = {
            "ollama": "本地运行的Ollama服务",
            "deepseek": "DeepSeek在线API", 
            "chatGPT": "OpenAI ChatGPT服务"
        }
        
        for model_type, model_config in model_configs.items():
            available_models[model_type] = {
                "name": model_type.capitalize(),
                "base_url": model_config.get("base_url", ""),
                "api_key": model_config.get("api_key", ""),
                "model": model_config.get("model", ""),
                "description": model_config.get("description", model_descriptions.get(model_type, f"{model_type} AI服务"))
            }
        
        return available_models
        
    def save_keymap(self, new_hotkeys=None):
        """保存快捷键设置到keymap.yml"""
        if new_hotkeys is None:
            return False
            
        # 加载现有配置
        keymap_data = self._load_yaml_file("keymap.yml") or {self.platform: self._get_default_setting("keymap")}
        
        # 检查是否有变化
        current_hotkeys = keymap_data.get(self.platform, {})
        have_change=False
        for key,value in new_hotkeys.items():
            if current_hotkeys.get(key,None) != value:
                have_change = True
                break
        if not have_change:
            return False

        # 合并新的快捷键设置到当前平台
        if self.platform not in keymap_data:
            keymap_data[self.platform] = {}
        keymap_data[self.platform] |= new_hotkeys

        # 保存回文件
        return self._save_yaml_file("keymap.yml", keymap_data)

    def save_process_whitelist(self, processes):
        """保存进程白名单"""
        # 加载现有配置
        existing_data = self._load_yaml_file("process_whitelist.yml") or {}
        
        # 检查是否有变化
        current_processes = existing_data.get(self.platform, [])
        if sorted(processes) == sorted(current_processes):
            return False
        
        # 更新当前平台的白名单
        existing_data[self.platform] = processes

        # 保存回文件
        return self._save_yaml_file("process_whitelist.yml", existing_data)
        
    def save_gui_settings(self):
        """保存GUI设置到settings.yml（仅更新变化的部分）"""
        # 加载现有配置
        existing_data = self._load_yaml_file("settings.yml") or {}
        
        # 没有变化就返回个False
        if json.dumps(existing_data, sort_keys=True) == json.dumps(self.gui_settings, sort_keys=True):
            return False
        
        # 新设置到现有数据中
        existing_data |= self.gui_settings
        
        # 保存回文件
        return self._save_yaml_file("settings.yml", existing_data)

    def save_style_configs(self):
        """保存样式配置到文件"""
        # 检查是否有变化
        existing_data = self._load_yaml_file("styles.yml") or {}
        if self.style_configs == existing_data:
            return True  # 没有变化，不保存
    
        return self._save_yaml_file("styles.yml", self.style_configs)

    def load_version_info(self) -> Dict[str, Any]:
        """加载版本信息"""
        try:
            return self._load_yaml_file("version.yml")
        except Exception as e:
            print(f"加载版本信息失败: {e}")
            return {"version": "0.0.0"}

    def get_program_info(self) -> Dict[str, Any]:
        """获取程序信息"""
        program_info = self.version_info["program"]
        return {
            "name": program_info["name"],
            "version": self.version,
            "author": program_info["author"],
            "description": program_info["description"],
            "github": program_info["github"],
            "origin_project": program_info["origin_project"]
        }
    
    def get_contact_info(self) -> Dict[str, str]:
        """获取联系信息"""
        return self.version_info.get("contact", {})
    
    def get_version_history(self) -> list:
        """获取版本历史"""
        return self.version_info.get("history", [])
    
    def get_sorted_image_components(self):
        """获取排序后的图片组件列表（按图层顺序）"""
        return sorted(self.style.image_components, key=lambda x: x.get("layer", 0))
    
class AppConfig:
    """应用配置类"""
    def __init__(self, base_path=None):
        # 使用样式配置中的文本框区域
        self.KEY_DELAY = 0.05  # 按键延迟
        self.AUTO_PASTE_IMAGE = True
        self.AUTO_SEND_IMAGE = True
        # 使用自动检测的基础路径
        self.BASE_PATH = base_path if base_path else get_base_path()
        self.ASSETS_PATH = get_resource_path("assets")


CONFIGS = ConfigLoader()