# pyqt_about.py
"""PyQt 关于窗口"""

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QThread, Signal
import traceback

from ui.about_window import Ui_AboutWindow
from config import CONFIGS
from utils.update_checker import update_checker


class CheckUpdateThread(QThread):
    """检查更新线程"""
    update_result = Signal(dict)
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        """执行更新检查"""
        try:
            result = update_checker.check_update(self.current_version)
            self.update_result.emit(result)
        except Exception as e:
            self.update_result.emit({"error": str(e)})


class AboutWindow(QDialog):
    """关于窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置UI
        self.ui = Ui_AboutWindow()
        self.ui.setupUi(self)
        
        # 存储更新线程
        self.update_thread = None
        
        # 内容类型标志位
        self.content_type = "original"  # original, version_history, update_check
        self.version_history_content = ""
        self.update_check_content = ""
        
        # 初始化界面
        self._setup_ui()
        
        # 连接信号槽
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 设置窗口属性
        self.setWindowTitle("关于 - 魔裁文本框生成器")
        self.setFixedSize(644, 738)
        
        # 获取程序信息
        program_info = CONFIGS.get_program_info()
        
        # 设置版本信息
        self.ui.label_2.setText(f"v{program_info['version']}")
        
        # 设置原始程序描述
        self._set_original_description()
        
        # 设置贡献者信息
        authors = program_info.get("author", [])
        if isinstance(authors, list):
            authors_text = ", ".join(authors)
        else:
            authors_text = str(authors)
        self.ui.label_contributers.setText(authors_text)
        
    def _set_original_description(self):
        """设置原始程序描述"""
        program_info = CONFIGS.get_program_info()
        
        description = (
            f"{program_info.get('description', '')}\n\n"
            "情感匹配使用说明：\n"
            "1. 下载ollama\n"
            "2. 在ollama中运行 OmniDimen 模型\n"
            "3. 启用程序内的情感匹配功能\n"
            "   （在setting.yml中启用sentiment_matching的display）\n"
            "4. 勾选主界面的情感匹配即可\n\n"
            "注意事项：\n"
            "• 有bug请及时反馈\n"
            "• 检查更新按钮可能对网络有要求"
        )
        
        self.ui.textBrowser.setPlainText(description)
        self.content_type = "original"
        
        # 滚动到顶部
        self.ui.textBrowser.verticalScrollBar().setValue(0)
    
    def _set_version_history_content(self):
        """设置版本历史内容"""
        try:
            version_history = CONFIGS.get_version_history()
            
            if not version_history:
                history_text = "暂无版本历史信息"
                self.version_history_content = history_text
                return
            
            # 构建版本历史文本
            history_text = "版本历史：\n\n"
            for i, version in enumerate(version_history, 1):
                history_text += f"版本 {version.get('version', '未知')}\n"
                history_text += f"发布时间: {version.get('date', '未知')}\n"
                history_text += "更新说明:\n"
                
                descriptions = version.get("description", [])
                if isinstance(descriptions, list):
                    for desc in descriptions:
                        history_text += f"• {desc}\n"
                else:
                    history_text += f"• {descriptions}\n"
                
                if i < len(version_history):
                    history_text += "\n" + "=" * 50 + "\n\n"
            
            self.version_history_content = history_text
            
        except Exception as e:
            self.version_history_content = f"获取版本历史失败: {str(e)}"
    
    def _set_update_check_content(self, result):
        """设置更新检查内容"""
        try:
            if isinstance(result, dict) and "error" in result:
                # 检查出错
                error_msg = f"检查更新失败: {result['error']}"
                self.update_check_content = f"更新检查结果：\n❌ {error_msg}"
                return
            
            if result.get("has_update", False):
                # 有更新可用
                latest = result["latest_release"]
                
                # 构建更新信息
                update_info = (
                    f"更新检查结果：\n"
                    f"✅ 有新版本可用: {latest['version']}\n\n"
                    f"版本信息：\n"
                    f"• 版本: {latest['version']}\n"
                    f"• 名称: {latest['version_name']}\n"
                    f"• 发布时间: {latest.get('published_at', '未知')}\n"
                    f"• 预发布: {'是' if latest.get('is_prerelease', False) else '否'}\n\n"
                )
                
                # 添加发布说明（截取前500字符）
                notes = latest.get("release_notes", "无更新说明")
                if len(notes) > 500:
                    notes = notes[:500] + "..."
                update_info += f"发布说明：\n{notes}\n\n"
                
                # 添加下载链接
                assets = latest.get("assets", [])
                if assets:
                    update_info += "文件列表：\n"
                    for i, asset in enumerate(assets[:3]):  # 最多显示3个
                        update_info += f"• {asset.get('name', '未知文件')} "
                        update_info += f"({self._format_size(asset.get('size', 0))})\n"
                    
                    if len(assets) > 3:
                        update_info += f"• ... 等 {len(assets)} 个文件\n"
                
                # GitHub页面链接提示
                update_info += (
                    f"\n下载链接：\n"
                    f"{update_checker.repo_url}releases/latest"
                )
                
                self.update_check_content = update_info
                
            else:
                # 已是最新版本
                self.update_check_content = (
                    f"更新检查结果：\n✅ 当前已是最新版本！\n"
                    f"当前版本: v{CONFIGS.version}"
                )
                
        except Exception as e:
            error_msg = f"处理更新结果时出错: {str(e)}"
            self.update_check_content = f"更新检查结果：\n❌ {error_msg}"
    
    def _connect_signals(self):
        """连接信号槽"""
        self.ui.pushButton.clicked.connect(self.toggle_version_history)
        self.ui.pushButton_2.clicked.connect(self.check_update)
    
    def toggle_version_history(self):
        """切换版本历史显示"""
        if self.content_type == "version_history":
            self._set_original_description()
        else:
            if not self.version_history_content:
                self._set_version_history_content()
            
            # 更新文本显示
            self.ui.textBrowser.setPlainText(self.version_history_content)
            self.content_type = "version_history"
        
        # 滚动到顶部
        self.ui.textBrowser.verticalScrollBar().setValue(0)
    
    def check_update(self):
        """检查更新"""
        # 如果当前已经显示更新检查内容，切换回原始内容
        if self.content_type == "update_check":
            self._set_original_description()
            return
        
        # 显示检查中状态
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_2.setText("检查中...")
        
        # 更新程序描述显示检查中
        self.ui.textBrowser.setPlainText("正在检查更新...")
        self.content_type = "update_check"
        
        # 启动检查更新线程
        self.update_thread = CheckUpdateThread(CONFIGS.version)
        self.update_thread.update_result.connect(self._on_update_check_complete)
        self.update_thread.finished.connect(self._on_update_thread_finished)
        self.update_thread.start()
    
    def _on_update_check_complete(self, result):
        """更新检查完成"""
        try:
            # 生成更新检查内容
            self._set_update_check_content(result)
            
            # 更新文本显示
            self.ui.textBrowser.setPlainText(self.update_check_content)
            self.content_type = "update_check"
            
        except Exception as e:
            error_msg = f"处理更新结果时出错: {str(e)}\n{traceback.format_exc()}"
            self.ui.textBrowser.setPlainText(f"更新检查结果：\n❌ {error_msg}")
            self.content_type = "update_check"
    
    def _on_update_thread_finished(self):
        """更新线程完成"""
        # 恢复按钮状态
        self.ui.pushButton_2.setEnabled(True)
        self.ui.pushButton_2.setText("检查更新")
        
        # 清理线程
        if self.update_thread:
            self.update_thread.deleteLater()
            self.update_thread = None
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果更新线程正在运行，等待它完成
        if self.update_thread and self.update_thread.isRunning():
            self.update_thread.quit()
            self.update_thread.wait(2000)  # 等待2秒
        
        event.accept()