# -*- coding: utf-8 -*-
"""组件模板模块"""

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_CharacterComponent:
    """角色组件模板"""
    
    def setupUi(self, CharacterComponent):
        if not CharacterComponent.objectName():
            CharacterComponent.setObjectName(u"CharacterComponent")
        CharacterComponent.resize(597, 200)
        
        self.verticalLayout = QVBoxLayout(CharacterComponent)
        self.verticalLayout.setObjectName(u"verticalLayout")
        
        # 角色选择组
        self.groupBox_CharaSelect = QGroupBox(CharacterComponent)
        self.groupBox_CharaSelect.setObjectName(u"groupBox_CharaSelect")
        self.horizontalLayout_25 = QHBoxLayout(self.groupBox_CharaSelect)
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.horizontalLayout_25.setContentsMargins(20, 0, 20, 5)
        
        self.label_charaSelect = QLabel(self.groupBox_CharaSelect)
        self.label_charaSelect.setObjectName(u"label_charaSelect")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_charaSelect.sizePolicy().hasHeightForWidth())
        self.label_charaSelect.setSizePolicy(sizePolicy)
        self.label_charaSelect.setMinimumSize(QSize(60, 0))
        self.horizontalLayout_25.addWidget(self.label_charaSelect)

        self.comboBox_charaSelect = QComboBox(self.groupBox_CharaSelect)
        self.comboBox_charaSelect.setObjectName(u"comboBox_charaSelect")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.comboBox_charaSelect.sizePolicy().hasHeightForWidth())
        self.comboBox_charaSelect.setSizePolicy(sizePolicy1)
        self.comboBox_charaSelect.setMinimumSize(QSize(150, 0))
        self.horizontalLayout_25.addWidget(self.comboBox_charaSelect)

        self.label_poiseSelect = QLabel(self.groupBox_CharaSelect)
        self.label_poiseSelect.setObjectName(u"label_poiseSelect")
        sizePolicy.setHeightForWidth(self.label_poiseSelect.sizePolicy().hasHeightForWidth())
        self.label_poiseSelect.setSizePolicy(sizePolicy)
        self.label_poiseSelect.setMinimumSize(QSize(100, 0))
        self.label_poiseSelect.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalLayout_25.addWidget(self.label_poiseSelect)

        self.comboBox_poiseSelect = QComboBox(self.groupBox_CharaSelect)
        self.comboBox_poiseSelect.setObjectName(u"comboBox_poiseSelect")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(1)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.comboBox_poiseSelect.sizePolicy().hasHeightForWidth())
        self.comboBox_poiseSelect.setSizePolicy(sizePolicy2)
        self.horizontalLayout_25.addWidget(self.comboBox_poiseSelect)

        self.label_posSelect = QLabel(self.groupBox_CharaSelect)
        self.label_posSelect.setObjectName(u"label_posSelect")
        sizePolicy.setHeightForWidth(self.label_posSelect.sizePolicy().hasHeightForWidth())
        self.label_posSelect.setSizePolicy(sizePolicy)
        self.label_posSelect.setMinimumSize(QSize(100, 0))
        self.label_posSelect.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalLayout_25.addWidget(self.label_posSelect)

        self.comboBox_posSelect = QComboBox(self.groupBox_CharaSelect)
        self.comboBox_posSelect.setObjectName(u"comboBox_posSelect")
        sizePolicy2.setHeightForWidth(self.comboBox_posSelect.sizePolicy().hasHeightForWidth())
        self.comboBox_posSelect.setSizePolicy(sizePolicy2)
        self.horizontalLayout_25.addWidget(self.comboBox_posSelect)

        self.verticalLayout.addWidget(self.groupBox_CharaSelect)

        # 表情配置组
        self.groupBox_EmotionSelect = QGroupBox(CharacterComponent)
        self.groupBox_EmotionSelect.setObjectName(u"groupBox_EmotionSelect")
        self.horizontalLayout_26 = QHBoxLayout(self.groupBox_EmotionSelect)
        self.horizontalLayout_26.setObjectName(u"horizontalLayout_26")
        self.horizontalLayout_26.setContentsMargins(20, 0, 20, 5)
        
        self.checkBox_randomEmotion = QCheckBox(self.groupBox_EmotionSelect)
        self.checkBox_randomEmotion.setObjectName(u"checkBox_randomEmotion")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(2)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.checkBox_randomEmotion.sizePolicy().hasHeightForWidth())
        self.checkBox_randomEmotion.setSizePolicy(sizePolicy3)
        self.checkBox_randomEmotion.setMinimumSize(QSize(235, 0))
        self.horizontalLayout_26.addWidget(self.checkBox_randomEmotion)

        self.label_emotionFilter = QLabel(self.groupBox_EmotionSelect)
        self.label_emotionFilter.setObjectName(u"label_emotionFilter")
        sizePolicy.setHeightForWidth(self.label_emotionFilter.sizePolicy().hasHeightForWidth())
        self.label_emotionFilter.setSizePolicy(sizePolicy)
        self.label_emotionFilter.setMinimumSize(QSize(100, 0))
        self.label_emotionFilter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalLayout_26.addWidget(self.label_emotionFilter)

        self.comboBox_emotionFilter = QComboBox(self.groupBox_EmotionSelect)
        self.comboBox_emotionFilter.setObjectName(u"comboBox_emotionFilter")
        sizePolicy2.setHeightForWidth(self.comboBox_emotionFilter.sizePolicy().hasHeightForWidth())
        self.comboBox_emotionFilter.setSizePolicy(sizePolicy2)
        self.horizontalLayout_26.addWidget(self.comboBox_emotionFilter)

        self.label_emotionSelect = QLabel(self.groupBox_EmotionSelect)
        self.label_emotionSelect.setObjectName(u"label_emotionSelect")
        sizePolicy.setHeightForWidth(self.label_emotionSelect.sizePolicy().hasHeightForWidth())
        self.label_emotionSelect.setSizePolicy(sizePolicy)
        self.label_emotionSelect.setMinimumSize(QSize(100, 0))
        self.label_emotionSelect.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalLayout_26.addWidget(self.label_emotionSelect)

        self.comboBox_emotionSelect = QComboBox(self.groupBox_EmotionSelect)
        self.comboBox_emotionSelect.setObjectName(u"comboBox_emotionSelect")
        sizePolicy2.setHeightForWidth(self.comboBox_emotionSelect.sizePolicy().hasHeightForWidth())
        self.comboBox_emotionSelect.setSizePolicy(sizePolicy2)
        self.horizontalLayout_26.addWidget(self.comboBox_emotionSelect)

        self.verticalLayout.addWidget(self.groupBox_EmotionSelect)
        
        self.retranslateUi(CharacterComponent)
        QMetaObject.connectSlotsByName(CharacterComponent)

    def retranslateUi(self, CharacterComponent):
        CharacterComponent.setWindowTitle(QCoreApplication.translate("CharacterComponent", u"角色组件", None))
        self.groupBox_CharaSelect.setTitle(QCoreApplication.translate("CharacterComponent", u"角色配置", None))
        self.label_charaSelect.setText(QCoreApplication.translate("CharacterComponent", u"选择角色", None))
        self.label_poiseSelect.setText(QCoreApplication.translate("CharacterComponent", u"姿势", None))
        self.label_posSelect.setText(QCoreApplication.translate("CharacterComponent", u"动作", None))
        self.groupBox_EmotionSelect.setTitle(QCoreApplication.translate("CharacterComponent", u"表情配置", None))
        self.checkBox_randomEmotion.setText(QCoreApplication.translate("CharacterComponent", u"随机表情", None))
        self.label_emotionFilter.setText(QCoreApplication.translate("CharacterComponent", u"表情筛选", None))
        self.label_emotionSelect.setText(QCoreApplication.translate("CharacterComponent", u"选择表情", None))


class Ui_BackgroundComponent:
    """背景组件模板"""
    
    def setupUi(self, BackgroundComponent):
        if not BackgroundComponent.objectName():
            BackgroundComponent.setObjectName(u"BackgroundComponent")
        BackgroundComponent.resize(400, 200)
        
        self.verticalLayout = QVBoxLayout(BackgroundComponent)
        self.verticalLayout.setObjectName(u"verticalLayout")
        
        # 随机背景复选框
        self.checkBox_randomBg = QCheckBox(BackgroundComponent)
        self.checkBox_randomBg.setObjectName(u"checkBox_randomBg")
        self.checkBox_randomBg.setMinimumSize(QSize(100, 0))
        self.verticalLayout.addWidget(self.checkBox_randomBg)
        
        # 背景选择部分
        bg_select_layout = QHBoxLayout()
        bg_select_layout.setObjectName(u"bg_select_layout")
        
        self.label_bgSelect = QLabel(BackgroundComponent)
        self.label_bgSelect.setObjectName(u"label_bgSelect")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_bgSelect.sizePolicy().hasHeightForWidth())
        self.label_bgSelect.setSizePolicy(sizePolicy)
        self.label_bgSelect.setMinimumSize(QSize(90, 0))
        self.label_bgSelect.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        bg_select_layout.addWidget(self.label_bgSelect)
        
        self.comboBox_bgSelect = QComboBox(BackgroundComponent)
        self.comboBox_bgSelect.setObjectName(u"comboBox_bgSelect")
        self.comboBox_bgSelect.setMinimumSize(QSize(0, 30))
        bg_select_layout.addWidget(self.comboBox_bgSelect)
        
        self.verticalLayout.addLayout(bg_select_layout)
        
        # 背景颜色部分
        color_layout = QHBoxLayout()
        color_layout.setObjectName(u"color_layout")
        
        self.label_bgColor = QLabel(BackgroundComponent)
        self.label_bgColor.setObjectName(u"label_bgColor")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_bgColor.sizePolicy().hasHeightForWidth())
        self.label_bgColor.setSizePolicy(sizePolicy1)
        self.label_bgColor.setMinimumSize(QSize(90, 0))
        self.label_bgColor.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        color_layout.addWidget(self.label_bgColor)
        
        self.lineEdit_bgColor = QLineEdit(BackgroundComponent)
        self.lineEdit_bgColor.setObjectName(u"lineEdit_bgColor")
        self.lineEdit_bgColor.setMinimumSize(QSize(0, 30))
        color_layout.addWidget(self.lineEdit_bgColor)
        
        self.widget_bgColorPreview = QWidget(BackgroundComponent)
        self.widget_bgColorPreview.setObjectName(u"widget_bgColorPreview")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.widget_bgColorPreview.sizePolicy().hasHeightForWidth())
        self.widget_bgColorPreview.setSizePolicy(sizePolicy2)
        self.widget_bgColorPreview.setMinimumSize(QSize(30, 30))
        color_layout.addWidget(self.widget_bgColorPreview)
        
        self.verticalLayout.addLayout(color_layout)
        
        self.retranslateUi(BackgroundComponent)
        QMetaObject.connectSlotsByName(BackgroundComponent)

    def retranslateUi(self, BackgroundComponent):
        BackgroundComponent.setWindowTitle(QCoreApplication.translate("BackgroundComponent", u"背景组件", None))
        self.checkBox_randomBg.setText(QCoreApplication.translate("BackgroundComponent", u"随机背景", None))
        self.label_bgSelect.setText(QCoreApplication.translate("BackgroundComponent", u"指定背景", None))
        self.label_bgColor.setText(QCoreApplication.translate("BackgroundComponent", u"指定颜色", None))
        self.lineEdit_bgColor.setPlaceholderText(QCoreApplication.translate("BackgroundComponent", u"#FFFFFF", None))


class Ui_ImageComponent:
    """图片组件模板"""
    
    def setupUi(self, ImageComponent):
        if not ImageComponent.objectName():
            ImageComponent.setObjectName(u"ImageComponent")
        ImageComponent.resize(400, 100)
        
        self.verticalLayout = QVBoxLayout(ImageComponent)
        self.verticalLayout.setObjectName(u"verticalLayout")
        
        self.label = QLabel(ImageComponent)
        self.label.setObjectName(u"label")
        self.label.setText(u"图片组件模板")
        self.verticalLayout.addWidget(self.label)
        
        self.retranslateUi(ImageComponent)
        QMetaObject.connectSlotsByName(ImageComponent)

    def retranslateUi(self, ImageComponent):
        ImageComponent.setWindowTitle(QCoreApplication.translate("ImageComponent", u"图片组件", None))


class Ui_NameboxComponent:
    """名字框组件模板"""
    
    def setupUi(self, NameboxComponent):
        if not NameboxComponent.objectName():
            NameboxComponent.setObjectName(u"NameboxComponent")
        NameboxComponent.resize(400, 100)
        
        self.verticalLayout = QVBoxLayout(NameboxComponent)
        self.verticalLayout.setObjectName(u"verticalLayout")
        
        self.label = QLabel(NameboxComponent)
        self.label.setObjectName(u"label")
        self.label.setText(u"名字框组件模板")
        self.verticalLayout.addWidget(self.label)
        
        self.retranslateUi(NameboxComponent)
        QMetaObject.connectSlotsByName(NameboxComponent)

    def retranslateUi(self, NameboxComponent):
        NameboxComponent.setWindowTitle(QCoreApplication.translate("NameboxComponent", u"名字框组件", None))


class Ui_TextComponent:
    """文本组件模板"""
    
    def setupUi(self, TextComponent):
        if not TextComponent.objectName():
            TextComponent.setObjectName(u"TextComponent")
        TextComponent.resize(400, 100)
        
        self.verticalLayout = QVBoxLayout(TextComponent)
        self.verticalLayout.setObjectName(u"verticalLayout")
        
        self.label = QLabel(TextComponent)
        self.label.setObjectName(u"label")
        self.label.setText(u"文本组件模板")
        self.verticalLayout.addWidget(self.label)
        
        self.retranslateUi(TextComponent)
        QMetaObject.connectSlotsByName(TextComponent)

    def retranslateUi(self, TextComponent):
        TextComponent.setWindowTitle(QCoreApplication.translate("TextComponent", u"文本组件", None))


class Ui_ExtraComponent:
    """其他组件模板"""
    
    def setupUi(self, ExtraComponent):
        if not ExtraComponent.objectName():
            ExtraComponent.setObjectName(u"ExtraComponent")
        ExtraComponent.resize(400, 100)
        
        self.verticalLayout = QVBoxLayout(ExtraComponent)
        self.verticalLayout.setObjectName(u"verticalLayout")
        
        self.label = QLabel(ExtraComponent)
        self.label.setObjectName(u"label")
        self.label.setText(u"其他组件模板")
        self.verticalLayout.addWidget(self.label)
        
        self.retranslateUi(ExtraComponent)
        QMetaObject.connectSlotsByName(ExtraComponent)

    def retranslateUi(self, ExtraComponent):
        ExtraComponent.setWindowTitle(QCoreApplication.translate("ExtraComponent", u"其他组件", None))