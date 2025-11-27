"""配置加载模块"""
import os
import yaml


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, base_path):
        self.base_path = base_path
        self.config_path = os.path.join(base_path, "config")
        
    def load_chara_meta(self):
        """加载角色元数据"""
        with open(os.path.join(self.config_path, "chara_meta.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config["mahoshojo"]
    
    def load_text_configs(self):
        """加载文本配置"""
        with open(os.path.join(self.config_path, "text_configs.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config["text_configs"]
    
    def load_keymap(self, platform):
        """加载快捷键映射"""
        with open(os.path.join(self.config_path, "keymap.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config.get(platform, {})
    
    def load_process_whitelist(self, platform):
        """加载进程白名单"""
        with open(os.path.join(self.config_path, "process_whitelist.yml"), 'r', encoding="utf-8") as fp:
            config = yaml.safe_load(fp)
            return config.get(platform, [])