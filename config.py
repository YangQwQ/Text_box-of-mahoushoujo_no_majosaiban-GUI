"""配置管理模块"""
import os
from typing import Dict, Any, Optional
import yaml
from sys import platform
from path_utils import get_base_path, get_resource_path, ensure_path_exists


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

        #当前预览相关
        self.current_character_index = 2

        # 状态变量(为None时为随机选择,否则为手动选择)
        self.selected_emotion = None
        self.selected_background = None

        #配置加载
        self.mahoshojo = {}
        self.text_configs_dict = {}
        self.character_list = []
        self.current_character = {}
        self.keymap = {}
        self.process_whitelist = []
        self._load_configs()

        self.background_count = self._get_background_count()  # 背景图片数量
    
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
            
    def _load_configs(self):
        """加载所有配置"""
        self.mahoshojo = self.load_config("chara_meta")
        self.character_list = list(self.mahoshojo.keys())
        self.current_character = self.mahoshojo[self.character_list[self.current_character_index - 1]]

        self.text_configs_dict = self.load_config("text_configs")
        self.keymap = self.load_config("keymap")
        self.process_whitelist = self.load_config("process_whitelist")

        self.gui_settings = self.load_config("settings")
        
        # 直接从配置中获取ai_models，不需要额外处理
        self.ai_models = self.gui_settings.get("sentiment_matching", {}).get("model_configs", {})
        
        # 确保enabled只有在display为True时才可能为True
        sm = self.gui_settings["sentiment_matching"]
        sm["enabled"] &= sm["display"]
    
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
                config = self._merge_dicts(default_settings, config)
            else:
                config = default_settings
                self.gui_settings = config
                self.save_gui_settings()
        
        return config
    
    def _merge_dicts(self, default: Dict, override: Dict) -> Dict:
        """递归合并两个字典"""
        result = default.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    def _get_default_setting(self, config_type: str) -> Dict[str, Any]:
        """获取默认设置"""
        print(f"获取默认配置：{config_type}")

        if config_type == "settings":
            return {
                "font_family": "font3",
                "font_size": 90,
                "text_color": '#FFFFFF',
                "bracket_color": '#EF4F54',
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
        
        # 合并新的快捷键设置到当前平台
        if self.platform not in keymap_data:
            keymap_data[self.platform] = {}
        keymap_data[self.platform].update(new_hotkeys)

        # 保存回文件
        return self._save_yaml_file("keymap.yml", keymap_data)
    
    def save_process_whitelist(self, processes):
        """保存进程白名单"""
        # 加载现有配置
        existing_data = self._load_yaml_file("process_whitelist.yml") or {}
        
        # 更新当前平台的白名单
        existing_data[self.platform] = processes
        
        # 保存回文件
        return self._save_yaml_file("process_whitelist.yml", existing_data)
        
    def save_gui_settings(self):
        """保存GUI设置到settings.yml"""
        # 直接保存当前配置
        return self._save_yaml_file("settings.yml", self.gui_settings)


class AppConfig:
    """应用配置类"""
    
    def __init__(self, base_path=None):
        # self.BOX_RECT = ((728, 355), (2339, 800))  # 文本框区域坐标
        self.BOX_RECT = ((760, 355), (2339, 800))
        self.KEY_DELAY = 0.05  # 按键延迟
        self.AUTO_PASTE_IMAGE = True
        self.AUTO_SEND_IMAGE = True
        # 使用自动检测的基础路径
        self.BASE_PATH = base_path if base_path else get_base_path()
        self.ASSETS_PATH = get_resource_path("assets")


CONFIGS = ConfigLoader()