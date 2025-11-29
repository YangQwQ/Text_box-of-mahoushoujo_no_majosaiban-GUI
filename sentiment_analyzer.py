import requests
import json
import time
import re
from typing import Optional, Dict, Any, List

class SentimentAnalyzer:
    def __init__(self):
        self.current_api = None
        self.api_config = {}
        self.is_initialized = False
        self.emotion_list = ["无感情", "愤怒", "嫌弃", "疑惑", "惊讶", "伤心", "害羞", "开心", "恐惧", "无语", "大笑"]
        
        # 更严格的规则提示词
        self.rule_prompt = """你是一个专门的情感分析助手。你的任务非常简单：分析用户输入文本的情感，并从以下11个选项中选择最匹配的一个：["无感情", "愤怒", "嫌弃", "疑惑", "惊讶", "伤心", "害羞", "开心", "恐惧", "无语", "大笑"]。

规则：
1. 只返回情感词汇，不要添加任何解释、问候或其他内容
2. 如果情感不明显，选择最接近的选项
3. 如果确实无法判断，返回"无感情"

请严格按照这个格式回复，现在请回复"好的"以确认你理解了规则。"""
        
    def initialize(self, api_type: str, **kwargs) -> bool:
        """
        初始化函数 - 尝试连接API并发送规则提示词
        """
        self.api_config = kwargs
        self.current_api = api_type
        
        try:
            # 发送规则提示词
            response = self._send_request(self.rule_prompt)
            
            # 检查回复是否包含确认信息
            if self._check_initialization_response(response):
                self.is_initialized = True
                print(f"{api_type} API 初始化成功")
                return True
            else:
                print(f"AI未正确确认规则，回复: {response}")
                self.is_initialized = False
                return False
                
        except Exception as e:
            print(f"初始化失败: {e}")
            self.is_initialized = False
            return False
    
    def _send_request(self, message: str) -> str:
        """发送请求到对应的API"""
        if self.current_api == 'ollama':
            return self._send_ollama_request(message)
        elif self.current_api == 'deepseek':
            return self._send_deepseek_request(message)
        else:
            raise ValueError("未设置有效的API类型")
    
    def _send_ollama_request(self, message: str) -> str:
        """发送请求到本地Ollama"""
        url = self.api_config.get('url', 'http://localhost:11434/api/generate')
        model = self.api_config.get('model', 'qwen2.5:7b')
        
        # 对于Ollama，每次请求都带上系统提示
        full_prompt = f"{self.rule_prompt}\n\n用户输入: {message}"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # 降低随机性
                "top_p": 0.3,       # 限制选择范围
                "num_predict": 10   # 限制输出长度
            }
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get('response', '').strip()
    
    def _send_deepseek_request(self, message: str) -> str:
        """发送请求到DeepSeek API"""
        api_key = self.api_config.get('api_key')
        if not api_key:
            raise ValueError("DeepSeek API需要api_key")
        
        url = self.api_config.get('url', 'https://api.deepseek.com/chat/completions')
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 对于DeepSeek，使用system消息来设置角色
        messages = [
            {"role": "system", "content": self.rule_prompt},
            {"role": "user", "content": message}
        ]
        
        payload = {
            "model": self.api_config.get('model', 'deepseek-chat'),
            "messages": messages,
            "stream": False,
            "temperature": 0.1,
            "max_tokens": 10
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    
    def _check_initialization_response(self, response: str) -> bool:
        """检查初始化回复是否成功"""
        confirmation_keywords = ['好的','无感情', '明白', '了解', '知道了', '没问题', '确认', 'ok', 'okay', 'yes', '理解']
        response_lower = response.lower()
        
        for keyword in confirmation_keywords:
            if keyword in response_lower:
                return True
        return False
    
    def _extract_emotion(self, response: str) -> Optional[str]:
        """从AI回复中提取情感词汇"""
        # 清理回复文本
        cleaned_response = re.sub(r'[^\w\u4e00-\u9fff]', '', response)
        
        # 直接匹配情感词汇
        for emotion in self.emotion_list:
            if emotion in cleaned_response:
                return emotion
        return None
    
    def send_rule_and_detect(self) -> bool:
        """
        规则发送与检测函数
        """
        if not self.current_api:
            print("未设置API类型，请先调用initialize函数")
            return False
            
        try:
            response = self._send_request("请确认你理解规则")
            success = self._check_initialization_response(response)
            
            if success:
                self.is_initialized = True
                print("规则发送成功，AI已确认")
            else:
                self.is_initialized = False
                print(f"规则发送失败，AI回复: {response}")
                
            return success
            
        except Exception as e:
            print(f"规则发送失败: {e}")
            self.is_initialized = False
            return False
    
    def switch_api(self, new_api_type: str, **kwargs) -> bool:
        """
        API切换函数
        """
        print(f"正在从 {self.current_api} 切换到 {new_api_type}")
        
        old_config = self.api_config.copy()
        old_api = self.current_api
        
        try:
            self.api_config = kwargs
            self.current_api = new_api_type
            self.is_initialized = False
            
            success = self.initialize(new_api_type, **kwargs)
            
            if success:
                print(f"成功切换到 {new_api_type}")
                return True
            else:
                self.api_config = old_config
                self.current_api = old_api
                print(f"切换到 {new_api_type} 失败，已恢复原有配置")
                return False
                
        except Exception as e:
            self.api_config = old_config
            self.current_api = old_api
            print(f"切换过程中发生错误: {e}，已恢复原有配置")
            return False
    
    def analyze_sentiment(self, text: str, max_retries: int = 1) -> Optional[str]:
        """
        情感检测函数
        """
        if not self.current_api:
            print("未设置API类型，请先调用initialize函数")
            return None
        
        for attempt in range(max_retries + 1):
            try:
                if self.current_api == 'ollama':
                    # 对于Ollama，规则已经在_send_ollama_request中包含了
                    response = self._send_ollama_request(text)
                else:
                    # 对于DeepSeek，使用专门的请求方法
                    response = self._send_deepseek_request(text)
                
                print(f"AI原始回复: {response}")
                
                # 提取情感
                emotion = self._extract_emotion(response)
                
                if emotion:
                    return emotion
                
                # 如果不在列表中，重新发送规则
                if attempt < max_retries:
                    print(f"无法从回复中提取有效情感，重新发送规则 (尝试 {attempt + 1}/{max_retries})")
                    self.send_rule_and_detect()
                    time.sleep(1)
                else:
                    print("达到最大重试次数，无法获得有效情感分析结果")
                    return None
                    
            except Exception as e:
                print(f"情感分析请求失败: {e}")
                if attempt < max_retries:
                    print(f"重试中... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(1)
                else:
                    return None
        
        return None

# 使用示例
def main():
    analyzer = SentimentAnalyzer()
    
    # 初始化Ollama
    print("=== 初始化Ollama ===")
    ollama_success = analyzer.initialize(
        api_type='ollama',
        url='http://localhost:11434/api/generate',
        model='qwen2.5'
    )
    
    if ollama_success:
        test_texts = [
            "我草，你这个有点吊",
            "嘻嘻",
            "你什么意思！",
            "我喜欢你",
            "我不理解"
        ]
        
        for text in test_texts:
            result = analyzer.analyze_sentiment(text)
            print(f"文本: '{text}' -> 情感: {result}")
            print("-" * 50)

if __name__ == "__main__":
    main()