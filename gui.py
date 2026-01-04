# gui.py - 修改后的主程序
"""PyQt 版本主程序入口"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QComboBox, QGroupBox, QTabWidget, QScrollArea, QSizePolicy, QSpacerItem, QLineEdit
from PySide6.QtCore import Qt, QTimer, QPoint, QMetaObject, Slot, Q_ARG
from PySide6.QtGui import QImage, QPixmap
import threading
import traceback

from ui_pyqt_main import Ui_MainWindow
from core import ManosabaCore
from config import CONFIGS
from pyqt_tabs import CharacterTabWidget, BackgroundTabWidget


class ManosabaMainWindow(QMainWindow):
    """魔裁文本框 PyQt 主窗口"""
      
    def __init__(self):
        super().__init__()
        
        # 设置UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # 存储角色和背景标签页引用
        self.character_tabs = []
        self.background_tab = None
        
        # 初始化核心
        self.core = ManosabaCore()
        self.core.set_gui_callback(self._on_sentiment_analyzer_status_changed)
        self.core.set_status_callback(self.update_status)
        
        # 图片生成状态
        self.is_generating = False
        
        # 预览图缩放相关
        self.zoom_level = 1.0
        self.last_mouse_pos = None
        self.is_dragging = False
        
        # 初始化界面
        self._setup_ui()
        
        # 连接信号槽
        self._connect_signals()
        
        # 初始化数据
        self._init_data()
        
        # 添加防抖定时器
        self._preview_update_timer = QTimer()
        self._preview_update_timer.setSingleShot(True)
        self._preview_update_timer.timeout.connect(self._delayed_update_preview)
        
        # 初始预览
        QTimer.singleShot(100, self.update_preview)

    def _setup_ui(self):
        """设置UI界面"""
        # 设置窗口标题
        self.setWindowTitle("魔裁文本框生成器")
        
        # 初始化样式选择下拉框
        self._init_style_combo()
        
        # 初始化角色和背景标签页
        self._init_components_tabs()
        
        # 设置预览区域支持鼠标交互
        self._setup_preview_interaction()
        
        # 初始化设置
        self._init_settings()
        
        # 调整预览区域大小
        self._adjust_preview_size()
    
    def _init_components_tabs(self):
        """初始化组件标签页"""
        # 清除现有标签页（除了背景标签页）
        while self.ui.tabWidget_Layer.count() > 1:
            widget = self.ui.tabWidget_Layer.widget(1)
            if widget:
                widget.deleteLater()
            self.ui.tabWidget_Layer.removeTab(1)
        
        # 清空标签页引用
        self.character_tabs.clear()
        self.background_tab = None
        
        # 获取预览样式的组件
        sorted_components = CONFIGS.get_sorted_preview_components()
        
        if not sorted_components:
            print("警告：没有找到预览样式的组件")
            return
        
        # 分离背景组件和角色组件
        background_components = [c for c in sorted_components if c.get("type") == "background"]
        character_components = [c for c in sorted_components if c.get("type") == "character"]
        
        # 设置背景标签页（第一个标签页）
        if background_components and self.ui.tabWidget_Layer.count() > 0:
            bg_component = background_components[0]
            bg_layer = bg_component.get("layer", 0)
            
            # 准备UI控件
            ui_controls = {
                'checkBox_randomBg': self.ui.checkBox_randomBg,
                'comboBox_bgSelect': self.ui.comboBox_bgSelect,
                'lineEdit_bgColor': self.ui.lineEdit,
                'widget_bgColorPreview': self.ui.widget_bgColorPreview
            }
            
            # 创建背景标签页管理器
            self.background_tab = BackgroundTabWidget(
                self, 
                component_config=bg_component,
                layer_index=bg_layer,
                ui_controls=ui_controls
            )
            self.background_tab.config_changed.connect(self._on_component_config_changed)
            
            # 更新标签页标题
            tab_name = bg_component.get("name", "背景")
            self.ui.tabWidget_Layer.setTabText(0, tab_name)
        
        # 为每个角色组件创建标签页
        for component in character_components:
            layer_index = component.get("layer", 0)
            
            # 创建角色标签页
            tab = CharacterTabWidget(self, component_config=component, layer_index=layer_index)
            tab.config_changed.connect(self._on_component_config_changed)
            
            # 使用组件名、角色名或默认名称
            if "name" in component:
                tab_name = component["name"]
            elif "character_name" in component:
                char_id = component["character_name"]
                full_name = CONFIGS.get_character(char_id, full_name=True)
                tab_name = f"{full_name}"
            else:
                tab_name = f"角色 {layer_index}"
            
            self.ui.tabWidget_Layer.addTab(tab, tab_name)
            self.character_tabs.append(tab)
    
    def _on_component_config_changed(self):
        """组件配置改变事件 - 添加防抖"""
        # 取消之前的定时器
        self._preview_update_timer.stop()
        # 重新启动定时器，延迟300ms更新预览
        self._preview_update_timer.start(300)
    
    def _init_style_combo(self):
        """初始化样式选择下拉框"""
        available_styles = list(CONFIGS.style_configs.keys())
        self.ui.comboBox_StyleSelect.clear()
        self.ui.comboBox_StyleSelect.addItems(available_styles)
        
        # 设置当前样式
        current_style = CONFIGS.current_style
        index = self.ui.comboBox_StyleSelect.findText(current_style)
        if index >= 0:
            self.ui.comboBox_StyleSelect.setCurrentIndex(index)
    
    def _setup_preview_interaction(self):
        """设置预览区域鼠标交互"""
        # 启用鼠标跟踪
        self.ui.PreviewImg.setMouseTracking(True)
        
        # 设置拖动模式为手形拖动
        self.ui.PreviewImg.setDragMode(self.ui.PreviewImg.DragMode.ScrollHandDrag)
        
        # 设置接受滚轮事件
        self.ui.PreviewImg.viewport().installEventFilter(self)
        
        # 创建场景
        scene = QGraphicsScene()
        self.ui.PreviewImg.setScene(scene)
        
        # 连接鼠标事件
        self.ui.PreviewImg.mousePressEvent = self._preview_mouse_press
        self.ui.PreviewImg.mouseMoveEvent = self._preview_mouse_move
        self.ui.PreviewImg.mouseReleaseEvent = self._preview_mouse_release
        self.ui.PreviewImg.wheelEvent = self._preview_wheel
    
    def _adjust_preview_size(self):
        """调整预览区域大小"""
        # 设置预览视图的策略，使其可以扩展
        self.ui.PreviewImg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 设置滚动区域策略
        self.ui.scrollArea.setWidgetResizable(True)
        
        # 调整预览图大小以适应窗口
        self.ui.scrollAreaWidgetContents.setMinimumHeight(400)
    
    def _init_settings(self):
        """初始化设置"""
        # 自动粘贴和自动发送
        self.ui.checkBox_AutoPaste.setChecked(CONFIGS.config.AUTO_PASTE_IMAGE)
        self.ui.checkBox_AutoSend.setChecked(CONFIGS.config.AUTO_SEND_IMAGE)
        
        # 情感匹配
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        if sentiment_settings.get("display", False):
            self.ui.checkBox_EmoMatch.setChecked(sentiment_settings.get("enabled", False))
        else:
            self.ui.checkBox_EmoMatch.hide()
    
    def _connect_signals(self):
        """连接信号槽"""
        # 样式选择
        self.ui.comboBox_StyleSelect.currentIndexChanged.connect(self.on_style_changed)
        
        # 设置相关
        self.ui.checkBox_AutoPaste.toggled.connect(self.on_auto_paste_changed)
        self.ui.checkBox_AutoSend.toggled.connect(self.on_auto_send_changed)
        self.ui.checkBox_EmoMatch.toggled.connect(self.on_sentiment_matching_changed)
        
        # 按钮
        self.ui.Button_RefreshPreview.clicked.connect(self.update_preview)
        
        # 菜单栏
        self.ui.menu_setting.triggered.connect(self._open_settings)
        self.ui.menu_style.triggered.connect(self._open_style)
        self.ui.menu_about.triggered.connect(self._open_about)
    
    def _init_data(self):
        """初始化数据"""
        # 更新情感分析器按钮状态
        self._update_sentiment_button_state()
        
        # 更新状态
        self.update_status("就绪")
    
    def _update_sentiment_button_state(self):
        """更新情感匹配按钮状态"""
        sentiment_settings = CONFIGS.gui_settings.get("sentiment_matching", {})
        if not sentiment_settings.get("display", False):
            return
        
        if self.core.sentiment_analyzer_status['initializing']:
            self.ui.checkBox_EmoMatch.setEnabled(False)
            self.ui.checkBox_EmoMatch.setChecked(True)
        elif self.core.sentiment_analyzer_status['initialized']:
            self.ui.checkBox_EmoMatch.setEnabled(True)
            self.ui.checkBox_EmoMatch.setChecked(sentiment_settings.get("enabled", False))
        else:
            self.ui.checkBox_EmoMatch.setEnabled(True)
            self.ui.checkBox_EmoMatch.setChecked(False)
    
    def on_style_changed(self, index):
        """样式改变事件"""
        if index < 0:
            return
        
        style_name = self.ui.comboBox_StyleSelect.currentText()
        if style_name in CONFIGS.style_configs:
            # 应用新样式
            CONFIGS.apply_style(style_name)
            
            # 重新初始化组件标签页
            self._init_components_tabs()
            
            # 更新预览
            self.update_preview()
            self.update_status(f"已切换到样式: {style_name}")
    
    def on_auto_paste_changed(self, checked):
        """自动粘贴设置改变"""
        CONFIGS.config.AUTO_PASTE_IMAGE = checked
    
    def on_auto_send_changed(self, checked):
        """自动发送设置改变"""
        CONFIGS.config.AUTO_SEND_IMAGE = checked
    
    def on_sentiment_matching_changed(self):
        """情感匹配设置改变"""
        self.core.toggle_sentiment_matching()
    
    def _on_sentiment_analyzer_status_changed(self, initialized, enabled, initializing=False):
        """情感分析器状态变化回调"""
        # 使用 QMetaObject.invokeMethod 在主线程中更新UI
        if initializing:
            QMetaObject.invokeMethod(self, "_update_sentiment_ui_initializing", 
                                    Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(self, "_update_sentiment_ui", 
                                    Qt.ConnectionType.QueuedConnection,
                                    Q_ARG(bool, enabled))
    
    @Slot()
    def _update_sentiment_ui_initializing(self):
        """在主线程中更新情感匹配UI（初始化中）"""
        self.ui.checkBox_EmoMatch.setEnabled(False)
        self.ui.checkBox_EmoMatch.setChecked(True)
        self.update_status("正在初始化情感分析器...")
    
    @Slot(bool)
    def _update_sentiment_ui(self, enabled):
        """在主线程中更新情感匹配UI"""
        self.ui.checkBox_EmoMatch.setEnabled(True)
        self.ui.checkBox_EmoMatch.setChecked(enabled)
        if enabled:
            self.update_status("情感匹配功能已启用")
        else:
            self.update_status("情感匹配功能已禁用")
        
    def _delayed_update_preview(self):
        """延迟更新预览"""
        self.update_preview()
        self.update_status("组件配置已更新")

    def update_preview(self):
        """更新预览"""
        # 确保没有重复调用
        if self._preview_update_timer.isActive():
            return
            
        try:
            preview_image, info = self.core.generate_preview()
            self._update_preview_ui(preview_image, info)
        except Exception as e:
            error_msg = f"预览生成失败: {str(e)}"
            print(traceback.format_exc())
            self.update_status(error_msg)

    def _update_preview_ui(self, preview_image, info):
        """更新预览UI"""
        try:
            # 转换PIL图像为QPixmap
            if preview_image.mode == "RGBA":
                # RGBA图像
                image = QImage(preview_image.tobytes(), preview_image.width, 
                            preview_image.height, QImage.Format.Format_RGBA8888)
            else:
                # RGB图像
                preview_image = preview_image.convert("RGB")
                image = QImage(preview_image.tobytes(), preview_image.width,
                            preview_image.height, QImage.Format.Format_RGB888)
            
            pixmap = QPixmap.fromImage(image)
            
            # 设置到QGraphicsView中
            scene = self.ui.PreviewImg.scene()
            if scene is None:
                scene = QGraphicsScene()
                self.ui.PreviewImg.setScene(scene)
            
            # 清除现有内容
            scene.clear()
            
            # 添加图片
            pixmap_item = QGraphicsPixmapItem(pixmap)
            scene.addItem(pixmap_item)
            scene.setSceneRect(pixmap.rect())
            
            # 调整视图以适应图片
            self.ui.PreviewImg.fitInView(pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            
            # 更新预览信息
            info_parts = info.split("\n")
            if len(info_parts) >= 3:
                info_text = f"{info_parts[0]} | {info_parts[1]} | {info_parts[2]}"
                self.ui.label_PreviewInfo.setText(info_text)
            else:
                self.ui.label_PreviewInfo.setText(info)
            
        except Exception as e:
            self.update_status(f"预览更新失败: {str(e)}")
            print(traceback.format_exc())
    
    def generate_image(self):
        """生成图片"""
        if self.is_generating:
            return
        
        self.is_generating = True
        self.update_status("正在生成图片...")
        
        def generate_in_thread():
            try:
                result = self.core.generate_image()
                QMetaObject.invokeMethod(self, "_on_generation_complete", 
                                        Qt.ConnectionType.QueuedConnection,
                                        Q_ARG(str, result))
            except Exception as e:
                error_msg = f"生成失败: {str(e)}"
                print(traceback.format_exc())
                QMetaObject.invokeMethod(self, "_on_generation_complete", 
                                        Qt.ConnectionType.QueuedConnection,
                                        Q_ARG(str, error_msg))
            finally:
                self.is_generating = False
        
        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()
    
    @Slot(str)
    def _on_generation_complete(self, result):
        """生成完成后的回调函数"""
        self.update_status(result)
        self.update_preview()
    
    @Slot(str)
    def update_status(self, message):
        """更新状态栏"""
        self.ui.statusbar.showMessage(message, 5000)  # 显示5秒
    
    # 预览图鼠标交互功能
    def _preview_mouse_press(self, event):
        """预览图鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = event.pos()
            self.is_dragging = True
            event.accept()
        else:
            # 调用父类方法处理其他鼠标按钮
            self.ui.PreviewImg.__class__.mousePressEvent(self.ui.PreviewImg, event)
    
    def _preview_mouse_move(self, event):
        """预览图鼠标移动事件"""
        if self.is_dragging and self.last_mouse_pos is not None:
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            
            # 滚动视图
            h_scroll = self.ui.PreviewImg.horizontalScrollBar()
            v_scroll = self.ui.PreviewImg.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() - delta.x())
            v_scroll.setValue(v_scroll.value() - delta.y())
            event.accept()
        else:
            # 调用父类方法
            self.ui.PreviewImg.__class__.mouseMoveEvent(self.ui.PreviewImg, event)
    
    def _preview_mouse_release(self, event):
        """预览图鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.last_mouse_pos = None
            event.accept()
        else:
            # 调用父类方法
            self.ui.PreviewImg.__class__.mouseReleaseEvent(self.ui.PreviewImg, event)
    
    def _preview_wheel(self, event):
        """预览图滚轮事件 - 缩放"""
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            # 放大
            self.zoom_level *= zoom_factor
            self.ui.PreviewImg.scale(zoom_factor, zoom_factor)
        else:
            # 缩小
            self.zoom_level /= zoom_factor
            self.ui.PreviewImg.scale(1/zoom_factor, 1/zoom_factor)
        event.accept()
    
    def _open_settings(self):
        """打开设置窗口"""
        # TODO: 实现设置窗口
        self.update_status("设置窗口功能待实现")
    
    def _open_style(self):
        """打开样式窗口"""
        # TODO: 实现样式窗口
        self.update_status("样式窗口功能待实现")
    
    def _open_about(self):
        """打开关于窗口"""
        # TODO: 实现关于窗口
        self.update_status("关于窗口功能待实现")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = ManosabaMainWindow()
    
    # 显示窗口
    main_window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main()