from typing import Optional, Dict, Any, List
import re

import openai
from config import CONFIGS


class AIClientManager:
    """AI客户端管理器"""
    
    def __init__(self):
        self.clients = {}
        self.current_client = None
        
    def initialize_client(self, client_type: str, config: Dict[str, Any]) -> bool:
        """初始化AI客户端"""
        try:
            openai.api_key = config.get("api_key", "")
            openai.base_url = config.get("base_url", "http://localhost:11434/v1/")
            self.current_client = client_type

            return self._test_connection(config.get("model", ""))
            
        except Exception as e:
            print(f"初始化AI客户端失败: {e}")
            return False, e
    
    def _test_connection(self, model_name: str) -> bool:
        """测试连接"""
        try:
            # 发送一个简单的测试请求
            response = openai.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return response.choices[0].message.content is not None, ""
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False, e
    
class SentimentAnalyzer:
    def __init__(self):
        self.client_manager = AIClientManager()  # 使用客户端管理器
        self.is_initialized = False
        # self.emotion_list = CONFIGS.emotion_list
        
        self.selected_emotion = None #用来在generate_image里显示选择的表情

    def initialize(self, client_type: str, config: Dict[str, Any]) -> bool:
        """
        初始化函数 - 使用新的配置结构
        """
        try:
            # 使用客户端管理器初始化
            success,error_msg = self.client_manager.initialize_client(client_type, config)
            
            if success and self._send_request("请任意回复"):
                print(f"{client_type} 情感分析器初始化成功")
                return True, ""
            else:
                print(f"{client_type} 客户端初始化失败")
                return False, error_msg
                
        except Exception as e:
            print(f"初始化失败: {e}")
            self.is_initialized = False
            return False, e
    
    def _send_request(self, message: str) -> str:
        """发送请求到对应的API"""
        return self._send_request_with_prompt("请任意回复",message)

    def _send_request_with_prompt(self, message: str, custom_prompt: str = None) -> str:
        """发送请求到对应的API，可使用自定义提示词"""
        try:
            prompt = custom_prompt if custom_prompt is not None else self.rule_prompt
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ]

            # 获取模型配置
            models = CONFIGS.get_available_models()
            current_client = self.client_manager.current_client
            model_name = models[current_client]["model"] if current_client in models else "deepseek-chat"

            response = openai.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                stream=False
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"请求失败: {e}")
            raise

    def analyze_sentiment_with_options(self, text: str, options: List[str]) -> Optional[str]:
        """
        分析文本并从给定选项中选择最匹配的一项
        
        Args:
            text: 用户输入文本
            options: 可选的表情/情感列表
            
        Returns:
            选中的选项，如果失败返回第一个选项
        """
        if not self.client_manager.current_client:
            print("未设置AI客户端，请先调用initialize函数")
            return None
        
        if not options:
            print("没有提供选项列表")
            return None
        
        try:
            # 构建包含选项的提示词
            options_str = ', '.join(options)
            custom_prompt = f"""你是一个聊天文本情感分析助手。请分析用户输入文本的情感，并从以下选项列表中选择最接近的一个能表现这个情感的动作、表情等内容的选项：[{options_str}]。

    规则：
    1. 只返回选项中的词汇，不要添加其他内容
    2. 无法判断或无内容时返回第一个选项
    3. 选项列表总是以最新的为准

    请开始分析随后的用户输入："""
            
            # 发送请求
            response = self._send_request_with_prompt(text, custom_prompt)
            print(f"AI原始回复: {response}")
            
            # 从回复中提取选项
            selected_option = self._extract_option(response, options)
            return selected_option if selected_option else (options[0] if options else None)
            
        except Exception as e:
            print(f"情感分析请求失败: {e}")
            return options[0] if options else None

    # 保留辅助函数
    def _extract_option(self, response: str, options: List[str]) -> Optional[str]:
        """从AI回复中提取选项"""
        cleaned_response = response.strip()
        
        # 直接匹配选项（完全匹配）
        for option in options:
            if option == cleaned_response:
                return option
        
        # 如果完全匹配失败，尝试包含匹配
        for option in options:
            if option in cleaned_response:
                return option
        
        # 如果包含匹配失败，尝试忽略大小写匹配
        for option in options:
            if option.lower() in cleaned_response.lower():
                return option
        
        return None