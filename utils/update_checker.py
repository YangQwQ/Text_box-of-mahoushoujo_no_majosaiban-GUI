# update_checker.py
import requests
import json
from typing import Dict, Any, Optional
from datetime import datetime
from config import CONFIGS

class UpdateChecker:
    """检查更新类"""
    
    def __init__(self, repo_url: str = None):
        # 如果没有提供repo_url，尝试从CONFIGS获取
        if repo_url is None:
            program_info = CONFIGS.get_program_info()
            repo_url = program_info["github"]
        
        self.repo_url = repo_url
        self.username = None
        self.repo_name = None
        self._parse_repo_url()
    
    def _parse_repo_url(self):
        """解析GitHub仓库URL"""
        if self.repo_url.endswith('/'):
            repo_url = self.repo_url[:-1]
        else:
            repo_url = self.repo_url
        
        parts = repo_url.split('/')
        if len(parts) < 5:
            raise ValueError("无效的GitHub URL")
        
        self.username = parts[-2]
        self.repo_name = parts[-1]
    
    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """获取GitHub仓库的最新release信息"""
        if not self.username or not self.repo_name:
            raise ValueError("未设置GitHub仓库信息")
        
        # 构建API URL
        api_url = f"https://api.github.com/repos/{self.username}/{self.repo_name}/releases/latest"
        
        try:
            # 发送GET请求
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 格式化发布时间 - 转换为本地时间
                published_at = data.get('published_at', 'N/A')
                if published_at != 'N/A':
                    try:
                        # GitHub返回的是UTC时间，转换为本地时间
                        dt_utc = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        dt_local = dt_utc.astimezone()
                        published_at = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        # 如果转换失败，保留原始时间
                        print(f"时间转换失败: {e}")
                
                # 提取主要信息
                latest_release = {
                    'version': data.get('tag_name', 'N/A'),
                    'version_name': data.get('name', 'N/A'),
                    'published_at': published_at,
                    'is_prerelease': data.get('prerelease', False),
                    'is_draft': data.get('draft', False),
                    'release_notes': data.get('body', 'N/A'),
                    'assets': []
                }
                
                # 提取资产信息
                assets = data.get('assets', [])
                for asset in assets:
                    latest_release['assets'].append({
                        'name': asset.get('name', 'N/A'),
                        'size': asset.get('size', 0),
                        'download_count': asset.get('download_count', 0),
                        'download_url': asset.get('browser_download_url', 'N/A')
                    })
                
                return latest_release
                
            elif response.status_code == 404:
                return {"error": "未找到release信息，可能该仓库没有发布任何release"}
            else:
                return {"error": f"请求失败: {response.status_code}", "details": response.text}
                
        except requests.exceptions.Timeout:
            return {"error": "请求超时，请检查网络连接"}
        except requests.exceptions.RequestException as e:
            return {"error": f"请求发生错误: {e}"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析错误: {e}"}
    
    def check_update(self, current_version: str = None) -> Dict[str, Any]:
        """检查更新，返回更新信息"""
        # 如果没有提供当前版本，使用CONFIGS.version
        if current_version is None:
            current_version = CONFIGS.version
        
        latest_release = self.get_latest_release()
        
        if isinstance(latest_release, dict) and 'error' in latest_release:
            return latest_release
        
        result = {
            'has_update': False,
            'current_version': current_version,
            'latest_release': latest_release
        }
        
        # 简单版本比较（移除v前缀进行比较）
        current_ver = current_version.replace('v', '').replace('V', '')
        latest_ver = latest_release['version'].replace('v', '').replace('V', '')
        
        try:
            # 简单的版本号比较
            current_parts = [int(x) for x in current_ver.split('.')]
            latest_parts = [int(x) for x in latest_ver.split('.')]
            
            # 确保版本号长度一致
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            # 比较版本号
            for i in range(max_len):
                if latest_parts[i] > current_parts[i]:
                    result['has_update'] = True
                    break
                elif latest_parts[i] < current_parts[i]:
                    result['has_update'] = False
                    break
        
        except ValueError:
            # 如果版本号不是数字格式，直接比较字符串
            result['has_update'] = latest_ver != current_ver
        
        return result


# 创建单例实例
update_checker = UpdateChecker()
