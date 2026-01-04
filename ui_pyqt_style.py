# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'StyleVzIHXc.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialogButtonBox, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QSpacerItem, QTabWidget,
    QToolButton, QVBoxLayout, QWidget)

class Ui_StyleWindow(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(710, 744)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_2 = QVBoxLayout(self.tab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.scrollArea_2 = QScrollArea(self.tab)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 666, 647))
        self.verticalLayout_7 = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.widget_5 = QWidget(self.scrollAreaWidgetContents_2)
        self.widget_5.setObjectName(u"widget_5")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_5.sizePolicy().hasHeightForWidth())
        self.widget_5.setSizePolicy(sizePolicy)
        self.widget_5.setMaximumSize(QSize(16777215, 100))
        self.horizontalLayout_7 = QHBoxLayout(self.widget_5)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, -1, 0, -1)
        self.groupBox_style = QGroupBox(self.widget_5)
        self.groupBox_style.setObjectName(u"groupBox_style")
        self.groupBox_style.setMaximumSize(QSize(16777215, 70))
        self.horizontalLayout_8 = QHBoxLayout(self.groupBox_style)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(20, -1, 20, -1)
        self.label_styleSelect = QLabel(self.groupBox_style)
        self.label_styleSelect.setObjectName(u"label_styleSelect")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_styleSelect.sizePolicy().hasHeightForWidth())
        self.label_styleSelect.setSizePolicy(sizePolicy1)
        self.label_styleSelect.setMinimumSize(QSize(50, 0))

        self.horizontalLayout_8.addWidget(self.label_styleSelect)

        self.comboBox_style = QComboBox(self.groupBox_style)
        self.comboBox_style.setObjectName(u"comboBox_style")
        self.comboBox_style.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_8.addWidget(self.comboBox_style)


        self.horizontalLayout_7.addWidget(self.groupBox_style)

        self.groupBox_imgProportion = QGroupBox(self.widget_5)
        self.groupBox_imgProportion.setObjectName(u"groupBox_imgProportion")
        self.groupBox_imgProportion.setMaximumSize(QSize(16777215, 70))
        self.horizontalLayout_2 = QHBoxLayout(self.groupBox_imgProportion)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, -1, -1, -1)
        self.radioButton_1 = QRadioButton(self.groupBox_imgProportion)
        self.radioButton_1.setObjectName(u"radioButton_1")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.radioButton_1.sizePolicy().hasHeightForWidth())
        self.radioButton_1.setSizePolicy(sizePolicy2)
        self.radioButton_1.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_2.addWidget(self.radioButton_1)

        self.radioButton_2 = QRadioButton(self.groupBox_imgProportion)
        self.radioButton_2.setObjectName(u"radioButton_2")
        sizePolicy2.setHeightForWidth(self.radioButton_2.sizePolicy().hasHeightForWidth())
        self.radioButton_2.setSizePolicy(sizePolicy2)
        self.radioButton_2.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_2.addWidget(self.radioButton_2)

        self.radioButton_3 = QRadioButton(self.groupBox_imgProportion)
        self.radioButton_3.setObjectName(u"radioButton_3")
        sizePolicy2.setHeightForWidth(self.radioButton_3.sizePolicy().hasHeightForWidth())
        self.radioButton_3.setSizePolicy(sizePolicy2)
        self.radioButton_3.setMinimumSize(QSize(80, 0))

        self.horizontalLayout_2.addWidget(self.radioButton_3)


        self.horizontalLayout_7.addWidget(self.groupBox_imgProportion)

        self.horizontalLayout_7.setStretch(0, 1)
        self.horizontalLayout_7.setStretch(1, 2)

        self.verticalLayout_7.addWidget(self.widget_5)

        self.groupBox_text = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_text.setObjectName(u"groupBox_text")
        sizePolicy.setHeightForWidth(self.groupBox_text.sizePolicy().hasHeightForWidth())
        self.groupBox_text.setSizePolicy(sizePolicy)
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_text)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.widget_line1 = QWidget(self.groupBox_text)
        self.widget_line1.setObjectName(u"widget_line1")
        self.horizontalLayout_6 = QHBoxLayout(self.widget_line1)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_9 = QLabel(self.widget_line1)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_6.addWidget(self.label_9)

        self.label_10 = QLabel(self.widget_line1)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_6.addWidget(self.label_10)

        self.lineEdit_textX = QLineEdit(self.widget_line1)
        self.lineEdit_textX.setObjectName(u"lineEdit_textX")
        self.lineEdit_textX.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_6.addWidget(self.lineEdit_textX)

        self.label_11 = QLabel(self.widget_line1)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_6.addWidget(self.label_11)

        self.lineEdit_textY = QLineEdit(self.widget_line1)
        self.lineEdit_textY.setObjectName(u"lineEdit_textY")
        self.lineEdit_textY.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_6.addWidget(self.lineEdit_textY)

        self.label_12 = QLabel(self.widget_line1)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_6.addWidget(self.label_12)

        self.lineEdit_textW = QLineEdit(self.widget_line1)
        self.lineEdit_textW.setObjectName(u"lineEdit_textW")
        self.lineEdit_textW.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_6.addWidget(self.lineEdit_textW)

        self.label_13 = QLabel(self.widget_line1)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_6.addWidget(self.label_13)

        self.lineEdit_textH = QLineEdit(self.widget_line1)
        self.lineEdit_textH.setObjectName(u"lineEdit_textH")
        self.lineEdit_textH.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_6.addWidget(self.lineEdit_textH)

        self.label_14 = QLabel(self.widget_line1)
        self.label_14.setObjectName(u"label_14")

        self.horizontalLayout_6.addWidget(self.label_14)

        self.comboBox_align = QComboBox(self.widget_line1)
        self.comboBox_align.setObjectName(u"comboBox_align")
        self.comboBox_align.setMinimumSize(QSize(120, 30))

        self.horizontalLayout_6.addWidget(self.comboBox_align)


        self.verticalLayout_5.addWidget(self.widget_line1)

        self.widget_line2 = QWidget(self.groupBox_text)
        self.widget_line2.setObjectName(u"widget_line2")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_line2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label = QLabel(self.widget_line2)
        self.label.setObjectName(u"label")

        self.horizontalLayout_3.addWidget(self.label)

        self.comboBox_textFont = QComboBox(self.widget_line2)
        self.comboBox_textFont.setObjectName(u"comboBox_textFont")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.comboBox_textFont.sizePolicy().hasHeightForWidth())
        self.comboBox_textFont.setSizePolicy(sizePolicy3)
        self.comboBox_textFont.setMinimumSize(QSize(0, 30))
        self.comboBox_textFont.setMaximumSize(QSize(250, 16777215))

        self.horizontalLayout_3.addWidget(self.comboBox_textFont)

        self.label_2 = QLabel(self.widget_line2)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_3.addWidget(self.label_2)

        self.lineEdit_fontSize = QLineEdit(self.widget_line2)
        self.lineEdit_fontSize.setObjectName(u"lineEdit_fontSize")
        sizePolicy2.setHeightForWidth(self.lineEdit_fontSize.sizePolicy().hasHeightForWidth())
        self.lineEdit_fontSize.setSizePolicy(sizePolicy2)
        self.lineEdit_fontSize.setMinimumSize(QSize(0, 30))
        self.lineEdit_fontSize.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_3.addWidget(self.lineEdit_fontSize)

        self.label_3 = QLabel(self.widget_line2)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_3.addWidget(self.label_3)

        self.lineEdit_textColor = QLineEdit(self.widget_line2)
        self.lineEdit_textColor.setObjectName(u"lineEdit_textColor")
        self.lineEdit_textColor.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_3.addWidget(self.lineEdit_textColor)

        self.label_textColorPreview = QLabel(self.widget_line2)
        self.label_textColorPreview.setObjectName(u"label_textColorPreview")
        sizePolicy2.setHeightForWidth(self.label_textColorPreview.sizePolicy().hasHeightForWidth())
        self.label_textColorPreview.setSizePolicy(sizePolicy2)
        self.label_textColorPreview.setMinimumSize(QSize(35, 35))

        self.horizontalLayout_3.addWidget(self.label_textColorPreview)


        self.verticalLayout_5.addWidget(self.widget_line2)

        self.widget_line3 = QWidget(self.groupBox_text)
        self.widget_line3.setObjectName(u"widget_line3")
        self.horizontalLayout_4 = QHBoxLayout(self.widget_line3)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_5 = QLabel(self.widget_line3)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_4.addWidget(self.label_5)

        self.lineEdit_shadowColor = QLineEdit(self.widget_line3)
        self.lineEdit_shadowColor.setObjectName(u"lineEdit_shadowColor")
        self.lineEdit_shadowColor.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_4.addWidget(self.lineEdit_shadowColor)

        self.label_shadowColorPreview = QLabel(self.widget_line3)
        self.label_shadowColorPreview.setObjectName(u"label_shadowColorPreview")
        sizePolicy2.setHeightForWidth(self.label_shadowColorPreview.sizePolicy().hasHeightForWidth())
        self.label_shadowColorPreview.setSizePolicy(sizePolicy2)
        self.label_shadowColorPreview.setMinimumSize(QSize(35, 35))

        self.horizontalLayout_4.addWidget(self.label_shadowColorPreview)

        self.label_24 = QLabel(self.widget_line3)
        self.label_24.setObjectName(u"label_24")

        self.horizontalLayout_4.addWidget(self.label_24)

        self.lineEdit_shadowX = QLineEdit(self.widget_line3)
        self.lineEdit_shadowX.setObjectName(u"lineEdit_shadowX")
        self.lineEdit_shadowX.setMinimumSize(QSize(0, 30))
        self.lineEdit_shadowX.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_4.addWidget(self.lineEdit_shadowX)

        self.label_25 = QLabel(self.widget_line3)
        self.label_25.setObjectName(u"label_25")

        self.horizontalLayout_4.addWidget(self.label_25)

        self.lineEdit_shadowY = QLineEdit(self.widget_line3)
        self.lineEdit_shadowY.setObjectName(u"lineEdit_shadowY")
        self.lineEdit_shadowY.setMinimumSize(QSize(0, 30))
        self.lineEdit_shadowY.setMaximumSize(QSize(100, 16777215))

        self.horizontalLayout_4.addWidget(self.lineEdit_shadowY)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.verticalLayout_5.addWidget(self.widget_line3)

        self.widget_line4 = QWidget(self.groupBox_text)
        self.widget_line4.setObjectName(u"widget_line4")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_line4)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.checkBox_useCharaColor = QCheckBox(self.widget_line4)
        self.checkBox_useCharaColor.setObjectName(u"checkBox_useCharaColor")

        self.horizontalLayout_5.addWidget(self.checkBox_useCharaColor)

        self.label_7 = QLabel(self.widget_line4)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_5.addWidget(self.label_7)

        self.lineEdit_bracketColor = QLineEdit(self.widget_line4)
        self.lineEdit_bracketColor.setObjectName(u"lineEdit_bracketColor")
        self.lineEdit_bracketColor.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_5.addWidget(self.lineEdit_bracketColor)

        self.label_bracketColorPreview = QLabel(self.widget_line4)
        self.label_bracketColorPreview.setObjectName(u"label_bracketColorPreview")
        sizePolicy2.setHeightForWidth(self.label_bracketColorPreview.sizePolicy().hasHeightForWidth())
        self.label_bracketColorPreview.setSizePolicy(sizePolicy2)
        self.label_bracketColorPreview.setMinimumSize(QSize(35, 35))

        self.horizontalLayout_5.addWidget(self.label_bracketColorPreview)

        self.pushButton_previewTextArea = QPushButton(self.widget_line4)
        self.pushButton_previewTextArea.setObjectName(u"pushButton_previewTextArea")
        self.pushButton_previewTextArea.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_5.addWidget(self.pushButton_previewTextArea)


        self.verticalLayout_5.addWidget(self.widget_line4)


        self.verticalLayout_7.addWidget(self.groupBox_text)

        self.groupBox_image = QGroupBox(self.scrollAreaWidgetContents_2)
        self.groupBox_image.setObjectName(u"groupBox_image")
        sizePolicy.setHeightForWidth(self.groupBox_image.sizePolicy().hasHeightForWidth())
        self.groupBox_image.setSizePolicy(sizePolicy)
        self.verticalLayout_8 = QVBoxLayout(self.groupBox_image)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.widget_line1_2 = QWidget(self.groupBox_image)
        self.widget_line1_2.setObjectName(u"widget_line1_2")
        self.horizontalLayout_9 = QHBoxLayout(self.widget_line1_2)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_condition = QLabel(self.widget_line1_2)
        self.label_condition.setObjectName(u"label_condition")

        self.horizontalLayout_9.addWidget(self.label_condition)

        self.radioButton_alway = QRadioButton(self.widget_line1_2)
        self.radioButton_alway.setObjectName(u"radioButton_alway")

        self.horizontalLayout_9.addWidget(self.radioButton_alway)

        self.radioButton_mixed = QRadioButton(self.widget_line1_2)
        self.radioButton_mixed.setObjectName(u"radioButton_mixed")

        self.horizontalLayout_9.addWidget(self.radioButton_mixed)

        self.radioButton_off = QRadioButton(self.widget_line1_2)
        self.radioButton_off.setObjectName(u"radioButton_off")

        self.horizontalLayout_9.addWidget(self.radioButton_off)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer)


        self.verticalLayout_8.addWidget(self.widget_line1_2)

        self.widget_line2_2 = QWidget(self.groupBox_image)
        self.widget_line2_2.setObjectName(u"widget_line2_2")
        self.horizontalLayout_10 = QHBoxLayout(self.widget_line2_2)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_17 = QLabel(self.widget_line2_2)
        self.label_17.setObjectName(u"label_17")

        self.horizontalLayout_10.addWidget(self.label_17)

        self.label_18 = QLabel(self.widget_line2_2)
        self.label_18.setObjectName(u"label_18")

        self.horizontalLayout_10.addWidget(self.label_18)

        self.lineEdit_imgX = QLineEdit(self.widget_line2_2)
        self.lineEdit_imgX.setObjectName(u"lineEdit_imgX")
        self.lineEdit_imgX.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_10.addWidget(self.lineEdit_imgX)

        self.label_19 = QLabel(self.widget_line2_2)
        self.label_19.setObjectName(u"label_19")

        self.horizontalLayout_10.addWidget(self.label_19)

        self.lineEdit_imgY = QLineEdit(self.widget_line2_2)
        self.lineEdit_imgY.setObjectName(u"lineEdit_imgY")
        self.lineEdit_imgY.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_10.addWidget(self.lineEdit_imgY)

        self.label_20 = QLabel(self.widget_line2_2)
        self.label_20.setObjectName(u"label_20")

        self.horizontalLayout_10.addWidget(self.label_20)

        self.lineEdit_imgW = QLineEdit(self.widget_line2_2)
        self.lineEdit_imgW.setObjectName(u"lineEdit_imgW")
        self.lineEdit_imgW.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_10.addWidget(self.lineEdit_imgW)

        self.label_21 = QLabel(self.widget_line2_2)
        self.label_21.setObjectName(u"label_21")

        self.horizontalLayout_10.addWidget(self.label_21)

        self.lineEdit_imgH = QLineEdit(self.widget_line2_2)
        self.lineEdit_imgH.setObjectName(u"lineEdit_imgH")
        self.lineEdit_imgH.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_10.addWidget(self.lineEdit_imgH)

        self.label_22 = QLabel(self.widget_line2_2)
        self.label_22.setObjectName(u"label_22")

        self.horizontalLayout_10.addWidget(self.label_22)

        self.comboBox_imgAlign = QComboBox(self.widget_line2_2)
        self.comboBox_imgAlign.setObjectName(u"comboBox_imgAlign")
        self.comboBox_imgAlign.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_10.addWidget(self.comboBox_imgAlign)


        self.verticalLayout_8.addWidget(self.widget_line2_2)

        self.widget_line3_2 = QWidget(self.groupBox_image)
        self.widget_line3_2.setObjectName(u"widget_line3_2")
        self.horizontalLayout_11 = QHBoxLayout(self.widget_line3_2)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_23 = QLabel(self.widget_line3_2)
        self.label_23.setObjectName(u"label_23")

        self.horizontalLayout_11.addWidget(self.label_23)

        self.comboBox_imgFillMode = QComboBox(self.widget_line3_2)
        self.comboBox_imgFillMode.setObjectName(u"comboBox_imgFillMode")
        self.comboBox_imgFillMode.setMinimumSize(QSize(120, 30))

        self.horizontalLayout_11.addWidget(self.comboBox_imgFillMode)

        self.horizontalSpacer_3 = QSpacerItem(338, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_3)

        self.pushButton_previewImgArea = QPushButton(self.widget_line3_2)
        self.pushButton_previewImgArea.setObjectName(u"pushButton_previewImgArea")
        self.pushButton_previewImgArea.setMinimumSize(QSize(0, 30))

        self.horizontalLayout_11.addWidget(self.pushButton_previewImgArea)


        self.verticalLayout_8.addWidget(self.widget_line3_2)


        self.verticalLayout_7.addWidget(self.groupBox_image)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_7.addItem(self.verticalSpacer_2)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout_2.addWidget(self.scrollArea_2)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_4 = QVBoxLayout(self.tab_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupBox = QGroupBox(self.tab_2)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.verticalLayout_3 = QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scrollArea = QScrollArea(self.groupBox)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setAutoFillBackground(False)
        self.scrollArea.setFrameShape(QFrame.Shape.Panel)
        self.scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 646, 555))
        self.verticalLayout_6 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)


        self.verticalLayout_4.addWidget(self.groupBox)

        self.frame = QFrame(self.tab_2)
        self.frame.setObjectName(u"frame")
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QSize(0, 40))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(40, -1, 40, -1)
        self.pushButton_2 = QPushButton(self.frame)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy2.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy2)
        self.pushButton_2.setMinimumSize(QSize(80, 30))

        self.horizontalLayout.addWidget(self.pushButton_2)

        self.horizontalSpacer_2 = QSpacerItem(150, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.toolButton = QToolButton(self.frame)
        self.toolButton.setObjectName(u"toolButton")
        self.toolButton.setMinimumSize(QSize(80, 30))
        self.toolButton.setCheckable(False)
        self.toolButton.setChecked(False)
        self.toolButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.toolButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.toolButton.setAutoRaise(True)

        self.horizontalLayout.addWidget(self.toolButton)


        self.verticalLayout_4.addWidget(self.frame)

        self.tabWidget.addTab(self.tab_2, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(Form)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Apply|QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.pushButton_2, self.tabWidget)

        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox_style.setTitle(QCoreApplication.translate("Form", u"\u6837\u5f0f\u914d\u7f6e\u6587\u4ef6", None))
        self.label_styleSelect.setText(QCoreApplication.translate("Form", u"\u5f53\u524d\u6837\u5f0f", None))
        self.groupBox_imgProportion.setTitle(QCoreApplication.translate("Form", u"\u56fe\u50cf\u6bd4\u4f8b", None))
        self.radioButton_1.setText(QCoreApplication.translate("Form", u"3\uff1a1", None))
        self.radioButton_2.setText(QCoreApplication.translate("Form", u"5\uff1a4", None))
        self.radioButton_3.setText(QCoreApplication.translate("Form", u"16\uff1a9", None))
        self.groupBox_text.setTitle(QCoreApplication.translate("Form", u"\u751f\u6210\u6587\u672c\u8bbe\u7f6e", None))
        self.label_9.setText(QCoreApplication.translate("Form", u"\u6587\u672c\u533a\u57df", None))
        self.label_10.setText(QCoreApplication.translate("Form", u"X", None))
        self.label_11.setText(QCoreApplication.translate("Form", u"Y", None))
        self.label_12.setText(QCoreApplication.translate("Form", u"\u5bbd", None))
        self.label_13.setText(QCoreApplication.translate("Form", u"\u9ad8", None))
        self.label_14.setText(QCoreApplication.translate("Form", u"\u5bf9\u9f50\u65b9\u5f0f", None))
        self.label.setText(QCoreApplication.translate("Form", u"\u6587\u672c\u5b57\u4f53", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"\u5b57\u53f7", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"\u6587\u672c\u989c\u8272", None))
        self.label_textColorPreview.setText("")
        self.label_5.setText(QCoreApplication.translate("Form", u"\u9634\u5f71\u989c\u8272", None))
        self.label_shadowColorPreview.setText("")
        self.label_24.setText(QCoreApplication.translate("Form", u"\u9634\u5f71X", None))
        self.label_25.setText(QCoreApplication.translate("Form", u"\u9634\u5f71Y", None))
        self.checkBox_useCharaColor.setText(QCoreApplication.translate("Form", u"\u4f7f\u7528\u89d2\u8272\u989c\u8272\u4f5c\u4e3a\u5f3a\u8c03\u8272", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"\u5f3a\u8c03\u989c\u8272", None))
        self.label_bracketColorPreview.setText("")
        self.pushButton_previewTextArea.setText(QCoreApplication.translate("Form", u"\u9884\u89c8\u533a\u57df", None))
        self.groupBox_image.setTitle(QCoreApplication.translate("Form", u"\u7c98\u8d34\u56fe\u50cf\u8bbe\u7f6e", None))
        self.label_condition.setText(QCoreApplication.translate("Form", u"\u751f\u6548\u60c5\u51b5", None))
        self.radioButton_alway.setText(QCoreApplication.translate("Form", u"\u59cb\u7ec8", None))
        self.radioButton_mixed.setText(QCoreApplication.translate("Form", u"\u6df7\u5408\u5185\u5bb9", None))
        self.radioButton_off.setText(QCoreApplication.translate("Form", u"\u5173\u95ed", None))
        self.label_17.setText(QCoreApplication.translate("Form", u"\u6587\u672c\u533a\u57df", None))
        self.label_18.setText(QCoreApplication.translate("Form", u"X", None))
        self.label_19.setText(QCoreApplication.translate("Form", u"Y", None))
        self.label_20.setText(QCoreApplication.translate("Form", u"\u5bbd", None))
        self.label_21.setText(QCoreApplication.translate("Form", u"\u9ad8", None))
        self.label_22.setText(QCoreApplication.translate("Form", u"\u5bf9\u9f50\u65b9\u5f0f", None))
        self.label_23.setText(QCoreApplication.translate("Form", u"\u586b\u5145\u65b9\u5f0f", None))
        self.pushButton_previewImgArea.setText(QCoreApplication.translate("Form", u"\u9884\u89c8\u533a\u57df", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Form", u"\u5e38\u89c4\u6837\u5f0f", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", u"\u7ec4\u4ef6\u7f16\u8f91", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"\u91cd\u7f6e\u7ec4\u4ef6", None))
        self.toolButton.setText(QCoreApplication.translate("Form", u"\u6dfb\u52a0\u7ec4\u4ef6", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("Form", u"\u56fe\u5c42\u7f16\u8f91", None))
    # retranslateUi

