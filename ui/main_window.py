# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Manosaba TextBoxkBVwst.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect, QSize, Qt)
from PySide6.QtGui import (QFont)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame,
    QGraphicsView, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QStatusBar,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(737, 702)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, 0, -1, -1)
        self.widget = QWidget(self.centralwidget)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout_2 = QHBoxLayout(self.widget)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        self.menu_setting = QPushButton(self.widget)
        self.menu_setting.setObjectName(u"menu_setting")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.menu_setting.sizePolicy().hasHeightForWidth())
        self.menu_setting.setSizePolicy(sizePolicy1)
        self.menu_setting.setMinimumSize(QSize(0, 30))
        self.menu_setting.setStyleSheet(u"QPushButton {\n"
"    background-color: #2b2b2b;\n"
"    border: 1px solid #3a3a3a;\n"
"    color: #d0d0d0;\n"
"    padding: 5px 15px;\n"
"    text-align: center;\n"
"    font-size: 13px;\n"
"    font-weight: normal;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #3a3a3a;\n"
"    border: 1px solid #4a4a4a;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #4a4a4a;\n"
"    border: 1px solid #5a5a5a;\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #1a4b7e;\n"
"    border: 1px solid #2a5b8e;\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"QPushButton:disabled {\n"
"    background-color: #1a1a1a;\n"
"    border: 1px solid #2a2a2a;\n"
"    color: #5a5a5a;\n"
"}")

        self.horizontalLayout_2.addWidget(self.menu_setting)

        self.menu_style = QPushButton(self.widget)
        self.menu_style.setObjectName(u"menu_style")
        sizePolicy1.setHeightForWidth(self.menu_style.sizePolicy().hasHeightForWidth())
        self.menu_style.setSizePolicy(sizePolicy1)
        self.menu_style.setMinimumSize(QSize(0, 30))
        self.menu_style.setStyleSheet(u"QPushButton {\n"
"    background-color: #2b2b2b;\n"
"    border: 1px solid #3a3a3a;\n"
"    color: #d0d0d0;\n"
"    padding: 5px 15px;\n"
"    text-align: center;\n"
"    font-size: 13px;\n"
"    font-weight: normal;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #3a3a3a;\n"
"    border: 1px solid #4a4a4a;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #4a4a4a;\n"
"    border: 1px solid #5a5a5a;\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #1a4b7e;\n"
"    border: 1px solid #2a5b8e;\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"QPushButton:disabled {\n"
"    background-color: #1a1a1a;\n"
"    border: 1px solid #2a2a2a;\n"
"    color: #5a5a5a;\n"
"}")

        self.horizontalLayout_2.addWidget(self.menu_style)

        self.menu_about = QPushButton(self.widget)
        self.menu_about.setObjectName(u"menu_about")
        sizePolicy1.setHeightForWidth(self.menu_about.sizePolicy().hasHeightForWidth())
        self.menu_about.setSizePolicy(sizePolicy1)
        self.menu_about.setMinimumSize(QSize(0, 30))
        self.menu_about.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.menu_about.setStyleSheet(u"QPushButton {\n"
"    background-color: #2b2b2b;\n"
"    border: 1px solid #3a3a3a;\n"
"    color: #d0d0d0;\n"
"    padding: 5px 15px;\n"
"    text-align: center;\n"
"    font-size: 13px;\n"
"    font-weight: normal;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #3a3a3a;\n"
"    border: 1px solid #4a4a4a;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #4a4a4a;\n"
"    border: 1px solid #5a5a5a;\n"
"}\n"
"\n"
"QPushButton:checked {\n"
"    background-color: #1a4b7e;\n"
"    border: 1px solid #2a5b8e;\n"
"    color: #ffffff;\n"
"}\n"
"\n"
"QPushButton:disabled {\n"
"    background-color: #1a1a1a;\n"
"    border: 1px solid #2a2a2a;\n"
"    color: #5a5a5a;\n"
"}")
        self.menu_about.setFlat(False)

        self.horizontalLayout_2.addWidget(self.menu_about)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.widget)

        self.frame_Cfg = QFrame(self.centralwidget)
        self.frame_Cfg.setObjectName(u"frame_Cfg")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.frame_Cfg.sizePolicy().hasHeightForWidth())
        self.frame_Cfg.setSizePolicy(sizePolicy2)
        self.frame_Cfg.setFrameShape(QFrame.Shape.WinPanel)
        self.frame_Cfg.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_Cfg)
        self.horizontalLayout.setSpacing(15)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_StyleSelect = QLabel(self.frame_Cfg)
        self.label_StyleSelect.setObjectName(u"label_StyleSelect")
        self.label_StyleSelect.setMinimumSize(QSize(65, 0))
        self.label_StyleSelect.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.label_StyleSelect)

        self.comboBox_StyleSelect = QComboBox(self.frame_Cfg)
        self.comboBox_StyleSelect.setObjectName(u"comboBox_StyleSelect")

        self.horizontalLayout.addWidget(self.comboBox_StyleSelect)

        self.checkBox_AutoPaste = QCheckBox(self.frame_Cfg)
        self.checkBox_AutoPaste.setObjectName(u"checkBox_AutoPaste")

        self.horizontalLayout.addWidget(self.checkBox_AutoPaste)

        self.checkBox_AutoSend = QCheckBox(self.frame_Cfg)
        self.checkBox_AutoSend.setObjectName(u"checkBox_AutoSend")

        self.horizontalLayout.addWidget(self.checkBox_AutoSend)

        self.checkBox_EmoMatch = QCheckBox(self.frame_Cfg)
        self.checkBox_EmoMatch.setObjectName(u"checkBox_EmoMatch")

        self.horizontalLayout.addWidget(self.checkBox_EmoMatch)

        self.horizontalLayout.setStretch(1, 2)

        self.verticalLayout.addWidget(self.frame_Cfg)

        self.tabWidget_Layer = QTabWidget(self.centralwidget)
        self.tabWidget_Layer.setObjectName(u"tabWidget_Layer")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tabWidget_Layer.sizePolicy().hasHeightForWidth())
        self.tabWidget_Layer.setSizePolicy(sizePolicy3)
        self.tabWidget_Layer.setMinimumSize(QSize(0, 200))
        self.tab_bg1 = QWidget()
        self.tab_bg1.setObjectName(u"tab_bg1")
        self.horizontalLayout_4 = QHBoxLayout(self.tab_bg1)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.frame_BgLayerCfg = QFrame(self.tab_bg1)
        self.frame_BgLayerCfg.setObjectName(u"frame_BgLayerCfg")
        self.frame_BgLayerCfg.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_BgLayerCfg.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_BgLayerCfg)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupBox_BgLayerCfg = QGroupBox(self.frame_BgLayerCfg)
        self.groupBox_BgLayerCfg.setObjectName(u"groupBox_BgLayerCfg")
        self.gridLayout = QGridLayout(self.groupBox_BgLayerCfg)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(25, 0, -1, 0)
        self.comboBox_bgSelect = QComboBox(self.groupBox_BgLayerCfg)
        self.comboBox_bgSelect.setObjectName(u"comboBox_bgSelect")
        self.comboBox_bgSelect.setMinimumSize(QSize(0, 30))

        self.gridLayout.addWidget(self.comboBox_bgSelect, 3, 4, 1, 1)

        self.label_bgColor = QLabel(self.groupBox_BgLayerCfg)
        self.label_bgColor.setObjectName(u"label_bgColor")
        sizePolicy.setHeightForWidth(self.label_bgColor.sizePolicy().hasHeightForWidth())
        self.label_bgColor.setSizePolicy(sizePolicy)
        self.label_bgColor.setMinimumSize(QSize(90, 0))
        self.label_bgColor.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.label_bgColor.setMargin(0)

        self.gridLayout.addWidget(self.label_bgColor, 4, 2, 1, 1)

        self.widget_bgColorPreview = QWidget(self.groupBox_BgLayerCfg)
        self.widget_bgColorPreview.setObjectName(u"widget_bgColorPreview")
        sizePolicy1.setHeightForWidth(self.widget_bgColorPreview.sizePolicy().hasHeightForWidth())
        self.widget_bgColorPreview.setSizePolicy(sizePolicy1)
        self.widget_bgColorPreview.setMinimumSize(QSize(30, 30))

        self.gridLayout.addWidget(self.widget_bgColorPreview, 4, 5, 1, 1)

        self.label_bgSelect = QLabel(self.groupBox_BgLayerCfg)
        self.label_bgSelect.setObjectName(u"label_bgSelect")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.label_bgSelect.sizePolicy().hasHeightForWidth())
        self.label_bgSelect.setSizePolicy(sizePolicy4)
        self.label_bgSelect.setMinimumSize(QSize(90, 0))
        self.label_bgSelect.setMaximumSize(QSize(90, 16777215))
        self.label_bgSelect.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.gridLayout.addWidget(self.label_bgSelect, 3, 2, 1, 1)

        self.checkBox_randomBg = QCheckBox(self.groupBox_BgLayerCfg)
        self.checkBox_randomBg.setObjectName(u"checkBox_randomBg")
        self.checkBox_randomBg.setMinimumSize(QSize(100, 0))
        self.checkBox_randomBg.setTristate(False)

        self.gridLayout.addWidget(self.checkBox_randomBg, 3, 1, 1, 1)

        self.lineEdit = QLineEdit(self.groupBox_BgLayerCfg)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setMinimumSize(QSize(0, 30))

        self.gridLayout.addWidget(self.lineEdit, 4, 4, 1, 1)

        self.gridLayout.setColumnStretch(2, 1)

        self.verticalLayout_4.addWidget(self.groupBox_BgLayerCfg)


        self.horizontalLayout_4.addWidget(self.frame_BgLayerCfg)

        self.tabWidget_Layer.addTab(self.tab_bg1, "")

        self.verticalLayout.addWidget(self.tabWidget_Layer)

        self.frame_PreviewArea = QFrame(self.centralwidget)
        self.frame_PreviewArea.setObjectName(u"frame_PreviewArea")
        self.frame_PreviewArea.setSizeIncrement(QSize(0, 0))
        self.frame_PreviewArea.setBaseSize(QSize(0, 0))
        self.frame_PreviewArea.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_PreviewArea.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_PreviewArea)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget_PreviewInfo = QWidget(self.frame_PreviewArea)
        self.widget_PreviewInfo.setObjectName(u"widget_PreviewInfo")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.widget_PreviewInfo.sizePolicy().hasHeightForWidth())
        self.widget_PreviewInfo.setSizePolicy(sizePolicy5)
        self.widget_PreviewInfo.setMinimumSize(QSize(0, 25))
        self.widget_PreviewInfo.setBaseSize(QSize(0, 0))
        self.horizontalLayout_6 = QHBoxLayout(self.widget_PreviewInfo)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, 0, -1, 0)
        self.label_PreviewInfo = QLabel(self.widget_PreviewInfo)
        self.label_PreviewInfo.setObjectName(u"label_PreviewInfo")
        sizePolicy4.setHeightForWidth(self.label_PreviewInfo.sizePolicy().hasHeightForWidth())
        self.label_PreviewInfo.setSizePolicy(sizePolicy4)

        self.horizontalLayout_6.addWidget(self.label_PreviewInfo)

        self.Button_RefreshPreview = QPushButton(self.widget_PreviewInfo)
        self.Button_RefreshPreview.setObjectName(u"Button_RefreshPreview")
        sizePolicy1.setHeightForWidth(self.Button_RefreshPreview.sizePolicy().hasHeightForWidth())
        self.Button_RefreshPreview.setSizePolicy(sizePolicy1)
        self.Button_RefreshPreview.setMinimumSize(QSize(0, 25))
        self.Button_RefreshPreview.setIconSize(QSize(16, 16))

        self.horizontalLayout_6.addWidget(self.Button_RefreshPreview)


        self.verticalLayout_2.addWidget(self.widget_PreviewInfo)

        self.scrollArea = QScrollArea(self.frame_PreviewArea)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 697, 325))
        self.horizontalLayout_5 = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.PreviewImg = QGraphicsView(self.scrollAreaWidgetContents)
        self.PreviewImg.setObjectName(u"PreviewImg")
        self.PreviewImg.setSizeIncrement(QSize(0, 0))
        self.PreviewImg.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.horizontalLayout_5.addWidget(self.PreviewImg)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_2.addWidget(self.scrollArea)


        self.verticalLayout.addWidget(self.frame_PreviewArea)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget_Layer.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u9b54\u88c1\u6587\u672c\u6846", None))
        self.menu_setting.setText(QCoreApplication.translate("MainWindow", u"\u8bbe\u7f6e", None))
        self.menu_style.setText(QCoreApplication.translate("MainWindow", u"\u6837\u5f0f", None))
        self.menu_about.setText(QCoreApplication.translate("MainWindow", u"\u5173\u4e8e", None))
        self.label_StyleSelect.setText(QCoreApplication.translate("MainWindow", u"\u6837\u5f0f\u9009\u62e9", None))
        self.checkBox_AutoPaste.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52a8\u7c98\u8d34", None))
        self.checkBox_AutoSend.setText(QCoreApplication.translate("MainWindow", u"\u81ea\u52a8\u53d1\u9001", None))
        self.checkBox_EmoMatch.setText(QCoreApplication.translate("MainWindow", u"\u60c5\u611f\u5339\u914d", None))
        self.groupBox_BgLayerCfg.setTitle(QCoreApplication.translate("MainWindow", u"\u80cc\u666f\u914d\u7f6e", None))
        self.label_bgColor.setText(QCoreApplication.translate("MainWindow", u"\u6307\u5b9a\u989c\u8272", None))
        self.label_bgSelect.setText(QCoreApplication.translate("MainWindow", u"\u6307\u5b9a\u80cc\u666f", None))
        self.checkBox_randomBg.setText(QCoreApplication.translate("MainWindow", u"\u968f\u673a\u80cc\u666f", None))
        self.tabWidget_Layer.setTabText(self.tabWidget_Layer.indexOf(self.tab_bg1), QCoreApplication.translate("MainWindow", u"\u80cc\u666f", None))
        self.label_PreviewInfo.setText(QCoreApplication.translate("MainWindow", u"\u9884\u89c8\u4fe1\u606f", None))
        self.Button_RefreshPreview.setText(QCoreApplication.translate("MainWindow", u"\u5237\u65b0", None))
    # retranslateUi

