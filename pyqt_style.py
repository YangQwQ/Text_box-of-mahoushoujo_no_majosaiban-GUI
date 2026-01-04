# -*- coding: utf-8 -*-
"""样式窗口模块"""

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDialogButtonBox,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_StyleWindow:
    """样式窗口UI"""
    
    def setupUi(self, StyleWindow):
        if not StyleWindow.objectName():
            StyleWindow.setObjectName(u"StyleWindow")
        StyleWindow.resize(400, 300)
        
        self.verticalLayout = QVBoxLayout(StyleWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        
        # 样式选择组
        style_group = QGroupBox(StyleWindow)
        style_group.setObjectName(u"style_group")
        gridLayout = QGridLayout(style_group)
        gridLayout.setObjectName(u"gridLayout")
        
        self.label_style = QLabel(style_group)
        self.label_style.setObjectName(u"label_style")
        gridLayout.addWidget(self.label_style, 0, 0, 1, 1)
        
        self.comboBox_style = QComboBox(style_group)
        self.comboBox_style.setObjectName(u"comboBox_style")
        gridLayout.addWidget(self.comboBox_style, 0, 1, 1, 1)
        
        self.label_align = QLabel(style_group)
        self.label_align.setObjectName(u"label_align")
        gridLayout.addWidget(self.label_align, 1, 0, 1, 1)
        
        self.comboBox_align = QComboBox(style_group)
        self.comboBox_align.setObjectName(u"comboBox_align")
        gridLayout.addWidget(self.comboBox_align, 1, 1, 1, 1)
        
        self.verticalLayout.addWidget(style_group)
        
        # 按钮组
        self.buttonBox = QDialogButtonBox(StyleWindow)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)
        self.verticalLayout.addWidget(self.buttonBox)
        
        self.retranslateUi(StyleWindow)
        
        QMetaObject.connectSlotsByName(StyleWindow)

    def retranslateUi(self, StyleWindow):
        StyleWindow.setWindowTitle(QCoreApplication.translate("StyleWindow", u"样式编辑", None))
        self.label_style.setText(QCoreApplication.translate("StyleWindow", u"样式选择:", None))
        self.label_align.setText(QCoreApplication.translate("StyleWindow", u"文本对齐:", None))