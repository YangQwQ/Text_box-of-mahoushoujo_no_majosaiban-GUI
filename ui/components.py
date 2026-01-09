from PySide6.QtCore import (QCoreApplication, QMetaObject, QSize, Qt)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class CharacterComponent(QWidget):
    """角色组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
    
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"CharacterComponent")
        Form.resize(779, 65)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 0, 9, 9)
        
        # 简单视图
        self.widget_simple = QWidget(Form)
        self.widget_simple.setObjectName(u"widget_simple")
        sizePolicy.setHeightForWidth(self.widget_simple.sizePolicy().hasHeightForWidth())
        self.widget_simple.setSizePolicy(sizePolicy)
        self.widget_simple.setMinimumSize(QSize(0, 40))
        
        self.horizontalLayout = QHBoxLayout(self.widget_simple)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.label_type = QLabel(self.widget_simple)
        self.label_type.setObjectName(u"label_type")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_type.sizePolicy().hasHeightForWidth())
        self.label_type.setSizePolicy(sizePolicy1)
        self.label_type.setMinimumSize(QSize(80, 30))
        
        self.horizontalLayout.addWidget(self.label_type)
        
        self.label_name = QLabel(self.widget_simple)
        self.label_name.setObjectName(u"label_name")
        self.label_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout.addWidget(self.label_name)
        
        self.horizontalSpacer = QSpacerItem(40, 30, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)
        
        self.checkbox_enable = QCheckBox(self.widget_simple)
        self.checkbox_enable.setObjectName(u"checkbox_enable")
        self.checkbox_enable.setMinimumSize(QSize(0, 30))
        self.checkbox_enable.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.checkbox_enable)
        
        self.button_edit = QPushButton(self.widget_simple)
        self.button_edit.setObjectName(u"button_edit")
        self.button_edit.setMinimumSize(QSize(0, 30))
        self.button_edit.setMaximumSize(QSize(100, 16777215))
        
        self.horizontalLayout.addWidget(self.button_edit)
        
        self.button_move_up = QPushButton(self.widget_simple)
        self.button_move_up.setObjectName(u"button_move_up")
        self.button_move_up.setMinimumSize(QSize(0, 30))
        self.button_move_up.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_up)
        
        self.button_move_down = QPushButton(self.widget_simple)
        self.button_move_down.setObjectName(u"button_move_down")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.button_move_down.sizePolicy().hasHeightForWidth())
        self.button_move_down.setSizePolicy(sizePolicy2)
        self.button_move_down.setMinimumSize(QSize(30, 30))
        self.button_move_down.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_down)
        
        self.verticalLayout.addWidget(self.widget_simple)
        
        # 详细视图
        self.widget_detail = QWidget(Form)
        self.widget_detail.setObjectName(u"widget_detail")
        self.widget_detail.setEnabled(True)
        sizePolicy.setHeightForWidth(self.widget_detail.sizePolicy().hasHeightForWidth())
        self.widget_detail.setSizePolicy(sizePolicy)
        self.widget_detail.setMinimumSize(QSize(0, 0))
        self.widget_detail.setAcceptDrops(False)
        
        self.verticalLayout_detail = QVBoxLayout(self.widget_detail)
        self.verticalLayout_detail.setObjectName(u"verticalLayout_detail")
        self.verticalLayout_detail.setContentsMargins(0, 0, 0, 0)
        
        # 第一行：组件名称
        self.widget_line1 = QWidget(self.widget_detail)
        self.widget_line1.setObjectName(u"widget_line1")
        
        self.horizontalLayout_line1 = QHBoxLayout(self.widget_line1)
        self.horizontalLayout_line1.setObjectName(u"horizontalLayout_line1")
        self.horizontalLayout_line1.setContentsMargins(0, 0, 0, 0)
        
        self.label_component_name = QLabel(self.widget_line1)
        self.label_component_name.setObjectName(u"label_component_name")
        
        self.horizontalLayout_line1.addWidget(self.label_component_name)
        
        self.edit_component_name = QLineEdit(self.widget_line1)
        self.edit_component_name.setObjectName(u"edit_component_name")
        self.edit_component_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.edit_component_name)
        
        self.button_delete = QPushButton(self.widget_line1)
        self.button_delete.setObjectName(u"button_delete")
        self.button_delete.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.button_delete)
        
        self.verticalLayout_detail.addWidget(self.widget_line1)
        
        # 第二行：角色选择
        self.widget_line2 = QWidget(self.widget_detail)
        self.widget_line2.setObjectName(u"widget_line2")
        
        self.horizontalLayout_line2 = QHBoxLayout(self.widget_line2)
        self.horizontalLayout_line2.setObjectName(u"horizontalLayout_line2")
        self.horizontalLayout_line2.setContentsMargins(0, 0, 0, 0)
        
        self.label_character_select = QLabel(self.widget_line2)
        self.label_character_select.setObjectName(u"label_character_select")
        sizePolicy1.setHeightForWidth(self.label_character_select.sizePolicy().hasHeightForWidth())
        self.label_character_select.setSizePolicy(sizePolicy1)
        self.label_character_select.setMinimumSize(QSize(40, 0))
        
        self.horizontalLayout_line2.addWidget(self.label_character_select)
        
        self.combo_character = QComboBox(self.widget_line2)
        self.combo_character.setObjectName(u"combo_character")
        sizePolicy2.setHeightForWidth(self.combo_character.sizePolicy().hasHeightForWidth())
        self.combo_character.setSizePolicy(sizePolicy2)
        self.combo_character.setMinimumSize(QSize(60, 30))
        
        self.horizontalLayout_line2.addWidget(self.combo_character)
        
        self.label_poise = QLabel(self.widget_line2)
        self.label_poise.setObjectName(u"label_poise")
        sizePolicy1.setHeightForWidth(self.label_poise.sizePolicy().hasHeightForWidth())
        self.label_poise.setSizePolicy(sizePolicy1)
        self.label_poise.setMinimumSize(QSize(40, 0))
        self.label_poise.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line2.addWidget(self.label_poise)
        
        self.combo_poise = QComboBox(self.widget_line2)
        self.combo_poise.setObjectName(u"combo_poise")
        self.combo_poise.setMinimumSize(QSize(60, 30))
        
        self.horizontalLayout_line2.addWidget(self.combo_poise)
        
        self.label_clothes = QLabel(self.widget_line2)
        self.label_clothes.setObjectName(u"label_clothes")
        sizePolicy1.setHeightForWidth(self.label_clothes.sizePolicy().hasHeightForWidth())
        self.label_clothes.setSizePolicy(sizePolicy1)
        self.label_clothes.setMinimumSize(QSize(40, 0))
        self.label_clothes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalLayout_line2.addWidget(self.label_clothes)

        self.combo_clothes = QComboBox(self.widget_line2)
        self.combo_clothes.setObjectName(u"combo_clothes")
        self.combo_clothes.setMinimumSize(QSize(60, 30))
        self.horizontalLayout_line2.addWidget(self.combo_clothes)

        self.label_action = QLabel(self.widget_line2)
        self.label_action.setObjectName(u"label_action")
        sizePolicy1.setHeightForWidth(self.label_action.sizePolicy().hasHeightForWidth())
        self.label_action.setSizePolicy(sizePolicy1)
        self.label_action.setMinimumSize(QSize(40, 0))
        self.label_action.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line2.addWidget(self.label_action)
        
        self.combo_action = QComboBox(self.widget_line2)
        self.combo_action.setObjectName(u"combo_action")
        self.combo_action.setMinimumSize(QSize(60, 30))
        
        self.horizontalLayout_line2.addWidget(self.combo_action)
        
        # 重新分配拉伸比例（动态宽度）
        self.horizontalLayout_line2.setStretch(0, 1)   # label_character_select
        self.horizontalLayout_line2.setStretch(1, 5)   # combo_character
        self.horizontalLayout_line2.setStretch(2, 1)   # label_poise
        self.horizontalLayout_line2.setStretch(3, 2)   # combo_poise
        self.horizontalLayout_line2.setStretch(4, 1)   # label_clothes
        self.horizontalLayout_line2.setStretch(5, 2)   # combo_clothes
        self.horizontalLayout_line2.setStretch(6, 1)   # label_action
        self.horizontalLayout_line2.setStretch(7, 2)   # combo_action

        self.verticalLayout_detail.addWidget(self.widget_line2)
        
        # 第三行：表情设置
        self.widget_line3 = QWidget(self.widget_detail)
        self.widget_line3.setObjectName(u"widget_line3")
        
        self.horizontalLayout_line3 = QHBoxLayout(self.widget_line3)
        self.horizontalLayout_line3.setObjectName(u"horizontalLayout_line3")
        self.horizontalLayout_line3.setContentsMargins(0, 0, 0, 0)
        
        self.checkbox_fixed_emotion = QCheckBox(self.widget_line3)
        self.checkbox_fixed_emotion.setObjectName(u"checkbox_fixed_emotion")
        self.checkbox_fixed_emotion.setMinimumSize(QSize(150, 0))
        
        self.horizontalLayout_line3.addWidget(self.checkbox_fixed_emotion)
        
        self.label_emotion_select = QLabel(self.widget_line3)
        self.label_emotion_select.setObjectName(u"label_emotion_select")
        sizePolicy1.setHeightForWidth(self.label_emotion_select.sizePolicy().hasHeightForWidth())
        self.label_emotion_select.setSizePolicy(sizePolicy1)
        self.label_emotion_select.setMinimumSize(QSize(40, 0))
        self.label_emotion_select.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line3.addWidget(self.label_emotion_select)
        
        self.combo_emotion = QComboBox(self.widget_line3)
        self.combo_emotion.setObjectName(u"combo_emotion")
        self.combo_emotion.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line3.addWidget(self.combo_emotion)
        
        self.verticalLayout_detail.addWidget(self.widget_line3)
        
        # 第四行：位置和缩放
        self.widget_line4 = QWidget(self.widget_detail)
        self.widget_line4.setObjectName(u"widget_line4")
        
        self.horizontalLayout_line4 = QHBoxLayout(self.widget_line4)
        self.horizontalLayout_line4.setObjectName(u"horizontalLayout_line4")
        self.horizontalLayout_line4.setContentsMargins(0, 0, 0, 0)
        
        self.label_offset_x = QLabel(self.widget_line4)
        self.label_offset_x.setObjectName(u"label_offset_x")
        self.horizontalLayout_line4.addWidget(self.label_offset_x)
        
        self.edit_offset_x = QLineEdit(self.widget_line4)
        self.edit_offset_x.setObjectName(u"edit_offset_x")
        self.edit_offset_x.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line4.addWidget(self.edit_offset_x)
        
        self.label_offset_y = QLabel(self.widget_line4)
        self.label_offset_y.setObjectName(u"label_offset_y")
        self.horizontalLayout_line4.addWidget(self.label_offset_y)
        
        self.edit_offset_y = QLineEdit(self.widget_line4)
        self.edit_offset_y.setObjectName(u"edit_offset_y")
        self.edit_offset_y.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line4.addWidget(self.edit_offset_y)
        
        self.label_scale = QLabel(self.widget_line4)
        self.label_scale.setObjectName(u"label_scale")
        self.horizontalLayout_line4.addWidget(self.label_scale)
        
        self.edit_scale = QLineEdit(self.widget_line4)
        self.edit_scale.setObjectName(u"edit_scale")
        self.edit_scale.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line4.addWidget(self.edit_scale)
        
        self.label_align_mode = QLabel(self.widget_line4)
        self.label_align_mode.setObjectName(u"label_align_mode")
        self.horizontalLayout_line4.addWidget(self.label_align_mode)
        
        self.combo_align = QComboBox(self.widget_line4)
        self.combo_align.setObjectName(u"combo_align")
        self.combo_align.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line4.addWidget(self.combo_align)
        
        # 设置拉伸比例
        for i in range(8):
            self.horizontalLayout_line4.setStretch(i, 1)
        
        self.verticalLayout_detail.addWidget(self.widget_line4)
        
        self.verticalLayout.addWidget(self.widget_detail)
        
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
    
    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("CharacterComponent", u"角色组件", None))
        self.label_type.setText(QCoreApplication.translate("CharacterComponent", u"角色", None))
        self.label_name.setText(QCoreApplication.translate("CharacterComponent", u"未命名", None))
        self.checkbox_enable.setText(QCoreApplication.translate("CharacterComponent", u"启用", None))
        self.button_edit.setText(QCoreApplication.translate("CharacterComponent", u"展开", None))
        self.button_move_up.setText(QCoreApplication.translate("CharacterComponent", u"▲", None))
        self.button_move_down.setText(QCoreApplication.translate("CharacterComponent", u"▼", None))
        self.label_component_name.setText(QCoreApplication.translate("CharacterComponent", u"组件名称", None))
        self.button_delete.setText(QCoreApplication.translate("CharacterComponent", u"删除组件", None))
        self.label_character_select.setText(QCoreApplication.translate("CharacterComponent", u"角色选择", None))
        self.label_poise.setText(QCoreApplication.translate("CharacterComponent", u"姿态", None))
        self.label_clothes.setText(QCoreApplication.translate("CharacterComponent", u"服装", None))
        self.label_action.setText(QCoreApplication.translate("CharacterComponent", u"动作", None))
        self.checkbox_fixed_emotion.setText(QCoreApplication.translate("CharacterComponent", u"使用固定表情", None))
        # self.label_emotion_filter.setText(QCoreApplication.translate("CharacterComponent", u"表情筛选", None))
        self.label_emotion_select.setText(QCoreApplication.translate("CharacterComponent", u"表情选择", None))
        self.label_offset_x.setText(QCoreApplication.translate("CharacterComponent", u"X偏移", None))
        self.label_offset_y.setText(QCoreApplication.translate("CharacterComponent", u"Y偏移", None))
        self.label_scale.setText(QCoreApplication.translate("CharacterComponent", u"缩放", None))
        self.label_align_mode.setText(QCoreApplication.translate("CharacterComponent", u"对齐方式", None))


class BackgroundComponent(QWidget):
    """背景组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
    
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"BackgroundComponent")
        Form.resize(779, 65)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMaximumSize(QSize(16777215, 650))
        
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 0, 9, 9)
        
        # 简单视图
        self.widget_simple = QWidget(Form)
        self.widget_simple.setObjectName(u"widget_simple")
        sizePolicy.setHeightForWidth(self.widget_simple.sizePolicy().hasHeightForWidth())
        self.widget_simple.setSizePolicy(sizePolicy)
        self.widget_simple.setMinimumSize(QSize(0, 40))
        
        self.horizontalLayout = QHBoxLayout(self.widget_simple)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.label_type = QLabel(self.widget_simple)
        self.label_type.setObjectName(u"label_type")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_type.sizePolicy().hasHeightForWidth())
        self.label_type.setSizePolicy(sizePolicy1)
        self.label_type.setMinimumSize(QSize(80, 30))
        
        self.horizontalLayout.addWidget(self.label_type)
        
        self.label_name = QLabel(self.widget_simple)
        self.label_name.setObjectName(u"label_name")
        self.label_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout.addWidget(self.label_name)
        
        self.horizontalSpacer = QSpacerItem(40, 30, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)
        
        self.checkbox_enable = QCheckBox(self.widget_simple)
        self.checkbox_enable.setObjectName(u"checkbox_enable")
        self.checkbox_enable.setMinimumSize(QSize(0, 30))
        self.checkbox_enable.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.checkbox_enable)
        
        self.button_edit = QPushButton(self.widget_simple)
        self.button_edit.setObjectName(u"button_edit")
        self.button_edit.setMinimumSize(QSize(0, 30))
        self.button_edit.setMaximumSize(QSize(100, 16777215))
        
        self.horizontalLayout.addWidget(self.button_edit)
        
        self.button_move_up = QPushButton(self.widget_simple)
        self.button_move_up.setObjectName(u"button_move_up")
        self.button_move_up.setMinimumSize(QSize(0, 30))
        self.button_move_up.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_up)
        
        self.button_move_down = QPushButton(self.widget_simple)
        self.button_move_down.setObjectName(u"button_move_down")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.button_move_down.sizePolicy().hasHeightForWidth())
        self.button_move_down.setSizePolicy(sizePolicy2)
        self.button_move_down.setMinimumSize(QSize(30, 30))
        self.button_move_down.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_down)
        
        self.verticalLayout.addWidget(self.widget_simple)
        
        # 详细视图
        self.widget_detail = QWidget(Form)
        self.widget_detail.setObjectName(u"widget_detail")
        self.widget_detail.setEnabled(True)
        sizePolicy.setHeightForWidth(self.widget_detail.sizePolicy().hasHeightForWidth())
        self.widget_detail.setSizePolicy(sizePolicy)
        self.widget_detail.setMinimumSize(QSize(40, 0))
        self.widget_detail.setAcceptDrops(False)
        
        self.verticalLayout_detail = QVBoxLayout(self.widget_detail)
        self.verticalLayout_detail.setObjectName(u"verticalLayout_detail")
        self.verticalLayout_detail.setContentsMargins(0, 0, 0, 0)
        
        # 第一行：组件名称
        self.widget_line1 = QWidget(self.widget_detail)
        self.widget_line1.setObjectName(u"widget_line1")
        
        self.horizontalLayout_line1 = QHBoxLayout(self.widget_line1)
        self.horizontalLayout_line1.setObjectName(u"horizontalLayout_line1")
        self.horizontalLayout_line1.setContentsMargins(0, 0, 0, 0)
        
        self.label_component_name = QLabel(self.widget_line1)
        self.label_component_name.setObjectName(u"label_component_name")
        
        self.horizontalLayout_line1.addWidget(self.label_component_name)
        
        self.edit_component_name = QLineEdit(self.widget_line1)
        self.edit_component_name.setObjectName(u"edit_component_name")
        self.edit_component_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.edit_component_name)
        
        self.button_delete = QPushButton(self.widget_line1)
        self.button_delete.setObjectName(u"button_delete")
        self.button_delete.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.button_delete)
        
        self.verticalLayout_detail.addWidget(self.widget_line1)
        
        # 第二行：背景设置
        self.widget_line2 = QWidget(self.widget_detail)
        self.widget_line2.setObjectName(u"widget_line2")
        
        self.horizontalLayout_line2 = QHBoxLayout(self.widget_line2)
        self.horizontalLayout_line2.setObjectName(u"horizontalLayout_line2")
        self.horizontalLayout_line2.setContentsMargins(0, 0, 0, 0)
        
        self.checkbox_fixed_background = QCheckBox(self.widget_line2)
        self.checkbox_fixed_background.setObjectName(u"checkbox_fixed_background")
        self.checkbox_fixed_background.setMinimumSize(QSize(100, 0))
        
        self.horizontalLayout_line2.addWidget(self.checkbox_fixed_background)
        
        self.label_background_select = QLabel(self.widget_line2)
        self.label_background_select.setObjectName(u"label_background_select")
        sizePolicy1.setHeightForWidth(self.label_background_select.sizePolicy().hasHeightForWidth())
        self.label_background_select.setSizePolicy(sizePolicy1)
        self.label_background_select.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line2.addWidget(self.label_background_select)
        
        self.combo_background = QComboBox(self.widget_line2)
        self.combo_background.setObjectName(u"combo_background")
        sizePolicy2.setHeightForWidth(self.combo_background.sizePolicy().hasHeightForWidth())
        self.combo_background.setSizePolicy(sizePolicy2)
        self.combo_background.setMinimumSize(QSize(100, 30))
        
        self.horizontalLayout_line2.addWidget(self.combo_background)
        
        self.label_fill_mode = QLabel(self.widget_line2)
        self.label_fill_mode.setObjectName(u"label_fill_mode")
        sizePolicy1.setHeightForWidth(self.label_fill_mode.sizePolicy().hasHeightForWidth())
        self.label_fill_mode.setSizePolicy(sizePolicy1)
        self.label_fill_mode.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line2.addWidget(self.label_fill_mode)
        
        self.combo_fill_mode = QComboBox(self.widget_line2)
        self.combo_fill_mode.setObjectName(u"combo_fill_mode")
        self.combo_fill_mode.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line2.addWidget(self.combo_fill_mode)
        
        self.verticalLayout_detail.addWidget(self.widget_line2)
        
        # 第三行：位置和缩放
        self.widget_line3 = QWidget(self.widget_detail)
        self.widget_line3.setObjectName(u"widget_line3")
        
        self.horizontalLayout_line3 = QHBoxLayout(self.widget_line3)
        self.horizontalLayout_line3.setObjectName(u"horizontalLayout_line3")
        self.horizontalLayout_line3.setContentsMargins(0, 0, 0, 0)
        
        self.label_offset_x = QLabel(self.widget_line3)
        self.label_offset_x.setObjectName(u"label_offset_x")
        self.horizontalLayout_line3.addWidget(self.label_offset_x)
        
        self.edit_offset_x = QLineEdit(self.widget_line3)
        self.edit_offset_x.setObjectName(u"edit_offset_x")
        self.edit_offset_x.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_offset_x)
        
        self.label_offset_y = QLabel(self.widget_line3)
        self.label_offset_y.setObjectName(u"label_offset_y")
        self.horizontalLayout_line3.addWidget(self.label_offset_y)
        
        self.edit_offset_y = QLineEdit(self.widget_line3)
        self.edit_offset_y.setObjectName(u"edit_offset_y")
        self.edit_offset_y.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_offset_y)
        
        self.label_scale = QLabel(self.widget_line3)
        self.label_scale.setObjectName(u"label_scale")
        self.horizontalLayout_line3.addWidget(self.label_scale)
        
        self.edit_scale = QLineEdit(self.widget_line3)
        self.edit_scale.setObjectName(u"edit_scale")
        self.edit_scale.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_scale)
        
        self.label_align_mode = QLabel(self.widget_line3)
        self.label_align_mode.setObjectName(u"label_align_mode")
        self.horizontalLayout_line3.addWidget(self.label_align_mode)
        
        self.combo_align = QComboBox(self.widget_line3)
        self.combo_align.setObjectName(u"combo_align")
        self.combo_align.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.combo_align)
        
        # 设置拉伸比例
        for i in range(8):
            self.horizontalLayout_line3.setStretch(i, 1)
        
        self.verticalLayout_detail.addWidget(self.widget_line3)
        
        self.verticalLayout.addWidget(self.widget_detail)
        
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
    
    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("BackgroundComponent", u"背景组件", None))
        self.label_type.setText(QCoreApplication.translate("BackgroundComponent", u"背景", None))
        self.label_name.setText(QCoreApplication.translate("BackgroundComponent", u"未命名", None))
        self.checkbox_enable.setText(QCoreApplication.translate("BackgroundComponent", u"启用", None))
        self.button_edit.setText(QCoreApplication.translate("BackgroundComponent", u"展开", None))
        self.button_move_up.setText(QCoreApplication.translate("BackgroundComponent", u"▲", None))
        self.button_move_down.setText(QCoreApplication.translate("BackgroundComponent", u"▼", None))
        self.label_component_name.setText(QCoreApplication.translate("BackgroundComponent", u"组件名称", None))
        self.button_delete.setText(QCoreApplication.translate("BackgroundComponent", u"删除组件", None))
        self.checkbox_fixed_background.setText(QCoreApplication.translate("BackgroundComponent", u"使用固定背景", None))
        self.label_background_select.setText(QCoreApplication.translate("BackgroundComponent", u"背景选择", None))
        self.label_fill_mode.setText(QCoreApplication.translate("BackgroundComponent", u"填充方式", None))
        self.label_offset_x.setText(QCoreApplication.translate("BackgroundComponent", u"X偏移", None))
        self.label_offset_y.setText(QCoreApplication.translate("BackgroundComponent", u"Y偏移", None))
        self.label_scale.setText(QCoreApplication.translate("BackgroundComponent", u"缩放", None))
        self.label_align_mode.setText(QCoreApplication.translate("BackgroundComponent", u"对齐方式", None))


class ImageComponent(QWidget):
    """图片组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
    
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"ImageComponent")
        Form.resize(779, 65)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 0, 9, 9)
        
        # 简单视图
        self.widget_simple = QWidget(Form)
        self.widget_simple.setObjectName(u"widget_simple")
        sizePolicy.setHeightForWidth(self.widget_simple.sizePolicy().hasHeightForWidth())
        self.widget_simple.setSizePolicy(sizePolicy)
        self.widget_simple.setMinimumSize(QSize(0, 40))
        
        self.horizontalLayout = QHBoxLayout(self.widget_simple)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.label_type = QLabel(self.widget_simple)
        self.label_type.setObjectName(u"label_type")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_type.sizePolicy().hasHeightForWidth())
        self.label_type.setSizePolicy(sizePolicy1)
        self.label_type.setMinimumSize(QSize(80, 30))
        
        self.horizontalLayout.addWidget(self.label_type)
        
        self.label_name = QLabel(self.widget_simple)
        self.label_name.setObjectName(u"label_name")
        self.label_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout.addWidget(self.label_name)
        
        self.horizontalSpacer = QSpacerItem(40, 30, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)
        
        self.checkbox_enable = QCheckBox(self.widget_simple)
        self.checkbox_enable.setObjectName(u"checkbox_enable")
        self.checkbox_enable.setMinimumSize(QSize(0, 30))
        self.checkbox_enable.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.checkbox_enable)
        
        self.button_edit = QPushButton(self.widget_simple)
        self.button_edit.setObjectName(u"button_edit")
        self.button_edit.setMinimumSize(QSize(0, 30))
        self.button_edit.setMaximumSize(QSize(100, 16777215))
        
        self.horizontalLayout.addWidget(self.button_edit)
        
        self.button_move_up = QPushButton(self.widget_simple)
        self.button_move_up.setObjectName(u"button_move_up")
        self.button_move_up.setMinimumSize(QSize(0, 30))
        self.button_move_up.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_up)
        
        self.button_move_down = QPushButton(self.widget_simple)
        self.button_move_down.setObjectName(u"button_move_down")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.button_move_down.sizePolicy().hasHeightForWidth())
        self.button_move_down.setSizePolicy(sizePolicy2)
        self.button_move_down.setMinimumSize(QSize(30, 30))
        self.button_move_down.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_down)
        
        self.verticalLayout.addWidget(self.widget_simple)
        
        # 详细视图
        self.widget_detail = QWidget(Form)
        self.widget_detail.setObjectName(u"widget_detail")
        self.widget_detail.setEnabled(True)
        sizePolicy.setHeightForWidth(self.widget_detail.sizePolicy().hasHeightForWidth())
        self.widget_detail.setSizePolicy(sizePolicy)
        self.widget_detail.setMinimumSize(QSize(0, 0))
        self.widget_detail.setAcceptDrops(False)
        
        self.verticalLayout_detail = QVBoxLayout(self.widget_detail)
        self.verticalLayout_detail.setObjectName(u"verticalLayout_detail")
        self.verticalLayout_detail.setContentsMargins(0, 0, 0, 0)
        
        # 第一行：组件名称
        self.widget_line1 = QWidget(self.widget_detail)
        self.widget_line1.setObjectName(u"widget_line1")
        
        self.horizontalLayout_line1 = QHBoxLayout(self.widget_line1)
        self.horizontalLayout_line1.setObjectName(u"horizontalLayout_line1")
        self.horizontalLayout_line1.setContentsMargins(0, 0, 0, 0)
        
        self.label_component_name = QLabel(self.widget_line1)
        self.label_component_name.setObjectName(u"label_component_name")
        
        self.horizontalLayout_line1.addWidget(self.label_component_name)
        
        self.edit_component_name = QLineEdit(self.widget_line1)
        self.edit_component_name.setObjectName(u"edit_component_name")
        self.edit_component_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.edit_component_name)
        
        self.button_delete = QPushButton(self.widget_line1)
        self.button_delete.setObjectName(u"button_delete")
        self.button_delete.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.button_delete)
        
        self.verticalLayout_detail.addWidget(self.widget_line1)
        
        # 第二行：图片设置
        self.widget_line2 = QWidget(self.widget_detail)
        self.widget_line2.setObjectName(u"widget_line2")
        
        self.horizontalLayout_line2 = QHBoxLayout(self.widget_line2)
        self.horizontalLayout_line2.setObjectName(u"horizontalLayout_line2")
        self.horizontalLayout_line2.setContentsMargins(0, 0, 0, 0)
        
        self.label_image_select = QLabel(self.widget_line2)
        self.label_image_select.setObjectName(u"label_image_select")
        sizePolicy1.setHeightForWidth(self.label_image_select.sizePolicy().hasHeightForWidth())
        self.label_image_select.setSizePolicy(sizePolicy1)
        self.label_image_select.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line2.addWidget(self.label_image_select)
        
        self.combo_image = QComboBox(self.widget_line2)
        self.combo_image.setObjectName(u"combo_image")
        sizePolicy2.setHeightForWidth(self.combo_image.sizePolicy().hasHeightForWidth())
        self.combo_image.setSizePolicy(sizePolicy2)
        self.combo_image.setMinimumSize(QSize(200, 30))
        
        self.horizontalLayout_line2.addWidget(self.combo_image)
        
        self.label_fill_mode = QLabel(self.widget_line2)
        self.label_fill_mode.setObjectName(u"label_fill_mode")
        sizePolicy1.setHeightForWidth(self.label_fill_mode.sizePolicy().hasHeightForWidth())
        self.label_fill_mode.setSizePolicy(sizePolicy1)
        self.label_fill_mode.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line2.addWidget(self.label_fill_mode)
        
        self.combo_fill_mode = QComboBox(self.widget_line2)
        self.combo_fill_mode.setObjectName(u"combo_fill_mode")
        self.combo_fill_mode.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line2.addWidget(self.combo_fill_mode)
        
        self.verticalLayout_detail.addWidget(self.widget_line2)
        
        # 第三行：位置和缩放
        self.widget_line3 = QWidget(self.widget_detail)
        self.widget_line3.setObjectName(u"widget_line3")
        
        self.horizontalLayout_line3 = QHBoxLayout(self.widget_line3)
        self.horizontalLayout_line3.setObjectName(u"horizontalLayout_line3")
        self.horizontalLayout_line3.setContentsMargins(0, 0, 0, 0)
        
        self.label_offset_x = QLabel(self.widget_line3)
        self.label_offset_x.setObjectName(u"label_offset_x")
        self.horizontalLayout_line3.addWidget(self.label_offset_x)
        
        self.edit_offset_x = QLineEdit(self.widget_line3)
        self.edit_offset_x.setObjectName(u"edit_offset_x")
        self.edit_offset_x.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_offset_x)
        
        self.label_offset_y = QLabel(self.widget_line3)
        self.label_offset_y.setObjectName(u"label_offset_y")
        self.horizontalLayout_line3.addWidget(self.label_offset_y)
        
        self.edit_offset_y = QLineEdit(self.widget_line3)
        self.edit_offset_y.setObjectName(u"edit_offset_y")
        self.edit_offset_y.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_offset_y)
        
        self.label_scale = QLabel(self.widget_line3)
        self.label_scale.setObjectName(u"label_scale")
        self.horizontalLayout_line3.addWidget(self.label_scale)
        
        self.edit_scale = QLineEdit(self.widget_line3)
        self.edit_scale.setObjectName(u"edit_scale")
        self.edit_scale.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_scale)
        
        self.label_align_mode = QLabel(self.widget_line3)
        self.label_align_mode.setObjectName(u"label_align_mode")
        self.horizontalLayout_line3.addWidget(self.label_align_mode)
        
        self.combo_align = QComboBox(self.widget_line3)
        self.combo_align.setObjectName(u"combo_align")
        self.combo_align.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.combo_align)
        
        # 设置拉伸比例
        for i in range(8):
            self.horizontalLayout_line3.setStretch(i, 1)
        
        self.verticalLayout_detail.addWidget(self.widget_line3)
        
        self.verticalLayout.addWidget(self.widget_detail)
        
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
    
    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("ImageComponent", u"图片组件", None))
        self.label_type.setText(QCoreApplication.translate("ImageComponent", u"图片", None))
        self.label_name.setText(QCoreApplication.translate("ImageComponent", u"未命名", None))
        self.checkbox_enable.setText(QCoreApplication.translate("ImageComponent", u"启用", None))
        self.button_edit.setText(QCoreApplication.translate("ImageComponent", u"展开", None))
        self.button_move_up.setText(QCoreApplication.translate("ImageComponent", u"▲", None))
        self.button_move_down.setText(QCoreApplication.translate("ImageComponent", u"▼", None))
        self.label_component_name.setText(QCoreApplication.translate("ImageComponent", u"组件名称", None))
        self.button_delete.setText(QCoreApplication.translate("ImageComponent", u"删除组件", None))
        self.label_image_select.setText(QCoreApplication.translate("ImageComponent", u"图片选择", None))
        self.label_fill_mode.setText(QCoreApplication.translate("ImageComponent", u"填充方式", None))
        self.label_offset_x.setText(QCoreApplication.translate("ImageComponent", u"X偏移", None))
        self.label_offset_y.setText(QCoreApplication.translate("ImageComponent", u"Y偏移", None))
        self.label_scale.setText(QCoreApplication.translate("ImageComponent", u"缩放", None))
        self.label_align_mode.setText(QCoreApplication.translate("ImageComponent", u"对齐方式", None))


class NameboxComponent(QWidget):
    """名字框组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
    
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"NameboxComponent")
        Form.resize(781, 65)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 0, 9, 9)
        
        # 简单视图
        self.widget_simple = QWidget(Form)
        self.widget_simple.setObjectName(u"widget_simple")
        sizePolicy.setHeightForWidth(self.widget_simple.sizePolicy().hasHeightForWidth())
        self.widget_simple.setSizePolicy(sizePolicy)
        self.widget_simple.setMinimumSize(QSize(0, 40))
        
        self.horizontalLayout = QHBoxLayout(self.widget_simple)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.label_type = QLabel(self.widget_simple)
        self.label_type.setObjectName(u"label_type")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_type.sizePolicy().hasHeightForWidth())
        self.label_type.setSizePolicy(sizePolicy1)
        self.label_type.setMinimumSize(QSize(80, 30))
        
        self.horizontalLayout.addWidget(self.label_type)
        
        self.label_name = QLabel(self.widget_simple)
        self.label_name.setObjectName(u"label_name")
        self.label_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout.addWidget(self.label_name)
        
        self.horizontalSpacer = QSpacerItem(40, 30, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)
        
        self.checkbox_enable = QCheckBox(self.widget_simple)
        self.checkbox_enable.setObjectName(u"checkbox_enable")
        self.checkbox_enable.setMinimumSize(QSize(0, 30))
        self.checkbox_enable.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.checkbox_enable)
        
        self.button_edit = QPushButton(self.widget_simple)
        self.button_edit.setObjectName(u"button_edit")
        self.button_edit.setMinimumSize(QSize(0, 30))
        self.button_edit.setMaximumSize(QSize(100, 16777215))
        
        self.horizontalLayout.addWidget(self.button_edit)
        
        self.button_move_up = QPushButton(self.widget_simple)
        self.button_move_up.setObjectName(u"button_move_up")
        self.button_move_up.setMinimumSize(QSize(0, 30))
        self.button_move_up.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_up)
        
        self.button_move_down = QPushButton(self.widget_simple)
        self.button_move_down.setObjectName(u"button_move_down")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.button_move_down.sizePolicy().hasHeightForWidth())
        self.button_move_down.setSizePolicy(sizePolicy2)
        self.button_move_down.setMinimumSize(QSize(30, 30))
        self.button_move_down.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_down)
        
        self.verticalLayout.addWidget(self.widget_simple)
        
        # 详细视图
        self.widget_detail = QWidget(Form)
        self.widget_detail.setObjectName(u"widget_detail")
        self.widget_detail.setEnabled(True)
        sizePolicy.setHeightForWidth(self.widget_detail.sizePolicy().hasHeightForWidth())
        self.widget_detail.setSizePolicy(sizePolicy)
        self.widget_detail.setMinimumSize(QSize(0, 0))
        self.widget_detail.setAcceptDrops(False)
        
        self.verticalLayout_detail = QVBoxLayout(self.widget_detail)
        self.verticalLayout_detail.setObjectName(u"verticalLayout_detail")
        self.verticalLayout_detail.setContentsMargins(0, 0, 0, 0)
        
        # 第一行：组件名称
        self.widget_line1 = QWidget(self.widget_detail)
        self.widget_line1.setObjectName(u"widget_line1")
        
        self.horizontalLayout_line1 = QHBoxLayout(self.widget_line1)
        self.horizontalLayout_line1.setObjectName(u"horizontalLayout_line1")
        self.horizontalLayout_line1.setContentsMargins(0, 0, 0, 0)
        
        self.label_component_name = QLabel(self.widget_line1)
        self.label_component_name.setObjectName(u"label_component_name")
        
        self.horizontalLayout_line1.addWidget(self.label_component_name)
        
        self.edit_component_name = QLineEdit(self.widget_line1)
        self.edit_component_name.setObjectName(u"edit_component_name")
        self.edit_component_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.edit_component_name)
        
        self.button_delete = QPushButton(self.widget_line1)
        self.button_delete.setObjectName(u"button_delete")
        self.button_delete.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.button_delete)
        
        self.verticalLayout_detail.addWidget(self.widget_line1)
        
        # 第二行：图片设置
        self.widget_line2 = QWidget(self.widget_detail)
        self.widget_line2.setObjectName(u"widget_line2")
        
        self.horizontalLayout_line2 = QHBoxLayout(self.widget_line2)
        self.horizontalLayout_line2.setObjectName(u"horizontalLayout_line2")
        self.horizontalLayout_line2.setContentsMargins(0, 0, 0, 0)
        
        self.label_image_select = QLabel(self.widget_line2)
        self.label_image_select.setObjectName(u"label_image_select")
        sizePolicy1.setHeightForWidth(self.label_image_select.sizePolicy().hasHeightForWidth())
        self.label_image_select.setSizePolicy(sizePolicy1)
        self.label_image_select.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line2.addWidget(self.label_image_select)
        
        self.combo_image = QComboBox(self.widget_line2)
        self.combo_image.setObjectName(u"combo_image")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.combo_image.sizePolicy().hasHeightForWidth())
        self.combo_image.setSizePolicy(sizePolicy3)
        self.combo_image.setMinimumSize(QSize(200, 30))
        
        self.horizontalLayout_line2.addWidget(self.combo_image)
        
        self.verticalLayout_detail.addWidget(self.widget_line2)
        
        # 第三行：位置和缩放
        self.widget_line3 = QWidget(self.widget_detail)
        self.widget_line3.setObjectName(u"widget_line3")
        
        self.horizontalLayout_line3 = QHBoxLayout(self.widget_line3)
        self.horizontalLayout_line3.setObjectName(u"horizontalLayout_line3")
        self.horizontalLayout_line3.setContentsMargins(0, 0, 0, 0)
        
        self.label_offset_x = QLabel(self.widget_line3)
        self.label_offset_x.setObjectName(u"label_offset_x")
        self.horizontalLayout_line3.addWidget(self.label_offset_x)
        
        self.edit_offset_x = QLineEdit(self.widget_line3)
        self.edit_offset_x.setObjectName(u"edit_offset_x")
        self.edit_offset_x.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_offset_x)
        
        self.label_offset_y = QLabel(self.widget_line3)
        self.label_offset_y.setObjectName(u"label_offset_y")
        self.horizontalLayout_line3.addWidget(self.label_offset_y)
        
        self.edit_offset_y = QLineEdit(self.widget_line3)
        self.edit_offset_y.setObjectName(u"edit_offset_y")
        self.edit_offset_y.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_offset_y)
        
        self.label_scale = QLabel(self.widget_line3)
        self.label_scale.setObjectName(u"label_scale")
        self.horizontalLayout_line3.addWidget(self.label_scale)
        
        self.edit_scale = QLineEdit(self.widget_line3)
        self.edit_scale.setObjectName(u"edit_scale")
        self.edit_scale.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.edit_scale)
        
        self.label_align_mode = QLabel(self.widget_line3)
        self.label_align_mode.setObjectName(u"label_align_mode")
        self.horizontalLayout_line3.addWidget(self.label_align_mode)
        
        self.combo_align = QComboBox(self.widget_line3)
        self.combo_align.setObjectName(u"combo_align")
        self.combo_align.setMinimumSize(QSize(0, 30))
        self.horizontalLayout_line3.addWidget(self.combo_align)
        
        # 设置拉伸比例
        for i in range(8):
            self.horizontalLayout_line3.setStretch(i, 1)
        
        self.verticalLayout_detail.addWidget(self.widget_line3)
        
        self.verticalLayout.addWidget(self.widget_detail)
        
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
    
    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("NameboxComponent", u"名字框组件", None))
        self.label_type.setText(QCoreApplication.translate("NameboxComponent", u"名字框", None))
        self.label_name.setText(QCoreApplication.translate("NameboxComponent", u"未命名", None))
        self.checkbox_enable.setText(QCoreApplication.translate("NameboxComponent", u"启用", None))
        self.button_edit.setText(QCoreApplication.translate("NameboxComponent", u"展开", None))
        self.button_move_up.setText(QCoreApplication.translate("NameboxComponent", u"▲", None))
        self.button_move_down.setText(QCoreApplication.translate("NameboxComponent", u"▼", None))
        self.label_component_name.setText(QCoreApplication.translate("NameboxComponent", u"组件名称", None))
        self.button_delete.setText(QCoreApplication.translate("NameboxComponent", u"删除组件", None))
        self.label_image_select.setText(QCoreApplication.translate("NameboxComponent", u"图片选择", None))
        self.label_offset_x.setText(QCoreApplication.translate("NameboxComponent", u"X偏移", None))
        self.label_offset_y.setText(QCoreApplication.translate("NameboxComponent", u"Y偏移", None))
        self.label_scale.setText(QCoreApplication.translate("NameboxComponent", u"缩放", None))
        self.label_align_mode.setText(QCoreApplication.translate("NameboxComponent", u"对齐方式", None))


class TextComponent(QWidget):
    """文本组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
    
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"TextComponent")
        Form.resize(781, 65)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 0, 9, 9)
        
        # 简单视图
        self.widget_simple = QWidget(Form)
        self.widget_simple.setObjectName(u"widget_simple")
        sizePolicy.setHeightForWidth(self.widget_simple.sizePolicy().hasHeightForWidth())
        self.widget_simple.setSizePolicy(sizePolicy)
        self.widget_simple.setMinimumSize(QSize(0, 40))
        
        self.horizontalLayout = QHBoxLayout(self.widget_simple)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        
        self.label_type = QLabel(self.widget_simple)
        self.label_type.setObjectName(u"label_type")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_type.sizePolicy().hasHeightForWidth())
        self.label_type.setSizePolicy(sizePolicy1)
        self.label_type.setMinimumSize(QSize(80, 30))
        
        self.horizontalLayout.addWidget(self.label_type)
        
        self.label_name = QLabel(self.widget_simple)
        self.label_name.setObjectName(u"label_name")
        self.label_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout.addWidget(self.label_name)
        
        self.horizontalSpacer = QSpacerItem(40, 30, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(self.horizontalSpacer)
        
        self.checkbox_enable = QCheckBox(self.widget_simple)
        self.checkbox_enable.setObjectName(u"checkbox_enable")
        self.checkbox_enable.setMinimumSize(QSize(0, 30))
        self.checkbox_enable.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.checkbox_enable)
        
        self.button_edit = QPushButton(self.widget_simple)
        self.button_edit.setObjectName(u"button_edit")
        self.button_edit.setMinimumSize(QSize(0, 30))
        self.button_edit.setMaximumSize(QSize(100, 16777215))
        
        self.horizontalLayout.addWidget(self.button_edit)
        
        self.button_move_up = QPushButton(self.widget_simple)
        self.button_move_up.setObjectName(u"button_move_up")
        self.button_move_up.setMinimumSize(QSize(0, 30))
        self.button_move_up.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_up)
        
        self.button_move_down = QPushButton(self.widget_simple)
        self.button_move_down.setObjectName(u"button_move_down")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.button_move_down.sizePolicy().hasHeightForWidth())
        self.button_move_down.setSizePolicy(sizePolicy2)
        self.button_move_down.setMinimumSize(QSize(30, 30))
        self.button_move_down.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout.addWidget(self.button_move_down)
        
        self.verticalLayout.addWidget(self.widget_simple)
        
        # 详细视图
        self.widget_detail = QWidget(Form)
        self.widget_detail.setObjectName(u"widget_detail")
        self.widget_detail.setEnabled(True)
        sizePolicy.setHeightForWidth(self.widget_detail.sizePolicy().hasHeightForWidth())
        self.widget_detail.setSizePolicy(sizePolicy)
        self.widget_detail.setMinimumSize(QSize(0, 0))
        self.widget_detail.setAcceptDrops(False)
        
        self.verticalLayout_detail = QVBoxLayout(self.widget_detail)
        self.verticalLayout_detail.setObjectName(u"verticalLayout_detail")
        self.verticalLayout_detail.setContentsMargins(0, 0, 0, 0)
        
        # 第一行：组件名称
        self.widget_line1 = QWidget(self.widget_detail)
        self.widget_line1.setObjectName(u"widget_line1")
        
        self.horizontalLayout_line1 = QHBoxLayout(self.widget_line1)
        self.horizontalLayout_line1.setObjectName(u"horizontalLayout_line1")
        self.horizontalLayout_line1.setContentsMargins(0, 0, 0, 0)
        
        self.label_component_name = QLabel(self.widget_line1)
        self.label_component_name.setObjectName(u"label_component_name")
        self.label_component_name.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line1.addWidget(self.label_component_name)
        
        self.edit_component_name = QLineEdit(self.widget_line1)
        self.edit_component_name.setObjectName(u"edit_component_name")
        self.edit_component_name.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.edit_component_name)
        
        self.button_delete = QPushButton(self.widget_line1)
        self.button_delete.setObjectName(u"button_delete")
        self.button_delete.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line1.addWidget(self.button_delete)
        
        self.verticalLayout_detail.addWidget(self.widget_line1)
        
        # 第二行：文本内容
        self.widget_line2 = QWidget(self.widget_detail)
        self.widget_line2.setObjectName(u"widget_line2")
        
        self.horizontalLayout_line2 = QHBoxLayout(self.widget_line2)
        self.horizontalLayout_line2.setObjectName(u"horizontalLayout_line2")
        self.horizontalLayout_line2.setContentsMargins(0, 0, 0, 0)
        
        self.label_text_content = QLabel(self.widget_line2)
        self.label_text_content.setObjectName(u"label_text_content")
        sizePolicy1.setHeightForWidth(self.label_text_content.sizePolicy().hasHeightForWidth())
        self.label_text_content.setSizePolicy(sizePolicy1)
        self.label_text_content.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line2.addWidget(self.label_text_content)
        
        self.edit_text_content = QLineEdit(self.widget_line2)
        self.edit_text_content.setObjectName(u"edit_text_content")
        self.edit_text_content.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line2.addWidget(self.edit_text_content)
        
        self.label_line_width = QLabel(self.widget_line2)
        self.label_line_width.setObjectName(u"label_line_width")
        self.label_line_width.setMinimumSize(QSize(40, 0))
        self.label_line_width.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line2.addWidget(self.label_line_width)
        
        self.edit_line_width = QLineEdit(self.widget_line2)
        self.edit_line_width.setObjectName(u"edit_line_width")
        sizePolicy2.setHeightForWidth(self.edit_line_width.sizePolicy().hasHeightForWidth())
        self.edit_line_width.setSizePolicy(sizePolicy2)
        self.edit_line_width.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line2.addWidget(self.edit_line_width)
        
        self.verticalLayout_detail.addWidget(self.widget_line2)
        
        # 第三行：字体设置
        self.widget_line3 = QWidget(self.widget_detail)
        self.widget_line3.setObjectName(u"widget_line3")
        
        self.horizontalLayout_line3 = QHBoxLayout(self.widget_line3)
        self.horizontalLayout_line3.setObjectName(u"horizontalLayout_line3")
        self.horizontalLayout_line3.setContentsMargins(0, 0, 9, 0)
        
        self.label_font = QLabel(self.widget_line3)
        self.label_font.setObjectName(u"label_font")
        sizePolicy1.setHeightForWidth(self.label_font.sizePolicy().hasHeightForWidth())
        self.label_font.setSizePolicy(sizePolicy1)
        self.label_font.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line3.addWidget(self.label_font)
        
        self.combo_font = QComboBox(self.widget_line3)
        self.combo_font.setObjectName(u"combo_font")
        self.combo_font.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line3.addWidget(self.combo_font)
        
        self.label_text_size = QLabel(self.widget_line3)
        self.label_text_size.setObjectName(u"label_text_size")
        self.label_text_size.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line3.addWidget(self.label_text_size)
        
        self.edit_text_size = QLineEdit(self.widget_line3)
        self.edit_text_size.setObjectName(u"edit_text_size")
        sizePolicy2.setHeightForWidth(self.edit_text_size.sizePolicy().hasHeightForWidth())
        self.edit_text_size.setSizePolicy(sizePolicy2)
        self.edit_text_size.setMinimumSize(QSize(60, 30))
        self.edit_text_size.setMaximumSize(QSize(50, 16777215))
        
        self.horizontalLayout_line3.addWidget(self.edit_text_size)
        
        self.label_text_color = QLabel(self.widget_line3)
        self.label_text_color.setObjectName(u"label_text_color")
        self.label_text_color.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line3.addWidget(self.label_text_color)
        
        self.edit_text_color = QLineEdit(self.widget_line3)
        self.edit_text_color.setObjectName(u"edit_text_color")
        sizePolicy2.setHeightForWidth(self.edit_text_color.sizePolicy().hasHeightForWidth())
        self.edit_text_color.setSizePolicy(sizePolicy2)
        self.edit_text_color.setMinimumSize(QSize(50, 30))
        
        self.horizontalLayout_line3.addWidget(self.edit_text_color)
        
        self.verticalLayout_detail.addWidget(self.widget_line3)
        
        # 第四行：阴影设置
        self.widget_line4 = QWidget(self.widget_detail)
        self.widget_line4.setObjectName(u"widget_line4")
        
        self.horizontalLayout_line4 = QHBoxLayout(self.widget_line4)
        self.horizontalLayout_line4.setObjectName(u"horizontalLayout_line4")
        self.horizontalLayout_line4.setContentsMargins(0, 0, 0, 0)
        
        self.label_shadow_color = QLabel(self.widget_line4)
        self.label_shadow_color.setObjectName(u"label_shadow_color")
        sizePolicy1.setHeightForWidth(self.label_shadow_color.sizePolicy().hasHeightForWidth())
        self.label_shadow_color.setSizePolicy(sizePolicy1)
        self.label_shadow_color.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line4.addWidget(self.label_shadow_color)
        
        self.edit_shadow_color = QLineEdit(self.widget_line4)
        self.edit_shadow_color.setObjectName(u"edit_shadow_color")
        self.edit_shadow_color.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line4.addWidget(self.edit_shadow_color)
        
        self.label_shadow_x = QLabel(self.widget_line4)
        self.label_shadow_x.setObjectName(u"label_shadow_x")
        self.label_shadow_x.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line4.addWidget(self.label_shadow_x)
        
        self.edit_shadow_x = QLineEdit(self.widget_line4)
        self.edit_shadow_x.setObjectName(u"edit_shadow_x")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # sizePolicy4.setHorizontalStretch(150)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.edit_shadow_x.sizePolicy().hasHeightForWidth())
        self.edit_shadow_x.setSizePolicy(sizePolicy4)
        self.edit_shadow_x.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line4.addWidget(self.edit_shadow_x)
        
        self.label_shadow_y = QLabel(self.widget_line4)
        self.label_shadow_y.setObjectName(u"label_shadow_y")
        self.label_shadow_y.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line4.addWidget(self.label_shadow_y)
        
        self.edit_shadow_y = QLineEdit(self.widget_line4)
        self.edit_shadow_y.setObjectName(u"edit_shadow_y")
        sizePolicy2.setHeightForWidth(self.edit_shadow_y.sizePolicy().hasHeightForWidth())
        self.edit_shadow_y.setSizePolicy(sizePolicy2)
        self.edit_shadow_y.setMinimumSize(QSize(50, 30))
        
        self.horizontalLayout_line4.addWidget(self.edit_shadow_y)
        
        # 设置拉伸比例
        for i in range(5):
            self.horizontalLayout_line4.setStretch(i, 1)
        
        self.verticalLayout_detail.addWidget(self.widget_line4)
        
        # 第五行：位置和对齐
        self.widget_line5 = QWidget(self.widget_detail)
        self.widget_line5.setObjectName(u"widget_line5")
        
        self.horizontalLayout_line5 = QHBoxLayout(self.widget_line5)
        self.horizontalLayout_line5.setObjectName(u"horizontalLayout_line5")
        self.horizontalLayout_line5.setContentsMargins(0, 0, 0, 0)
        
        self.label_offset_x = QLabel(self.widget_line5)
        self.label_offset_x.setObjectName(u"label_offset_x")
        sizePolicy1.setHeightForWidth(self.label_offset_x.sizePolicy().hasHeightForWidth())
        self.label_offset_x.setSizePolicy(sizePolicy1)
        self.label_offset_x.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_line5.addWidget(self.label_offset_x)
        
        self.edit_offset_x = QLineEdit(self.widget_line5)
        self.edit_offset_x.setObjectName(u"edit_offset_x")
        self.edit_offset_x.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line5.addWidget(self.edit_offset_x)
        
        self.label_offset_y = QLabel(self.widget_line5)
        self.label_offset_y.setObjectName(u"label_offset_y")
        self.label_offset_y.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line5.addWidget(self.label_offset_y)
        
        self.edit_offset_y = QLineEdit(self.widget_line5)
        self.edit_offset_y.setObjectName(u"edit_offset_y")
        sizePolicy4.setHeightForWidth(self.edit_offset_y.sizePolicy().hasHeightForWidth())
        self.edit_offset_y.setSizePolicy(sizePolicy4)
        self.edit_offset_y.setMinimumSize(QSize(0, 30))
        
        self.horizontalLayout_line5.addWidget(self.edit_offset_y)
        
        self.label_align_mode = QLabel(self.widget_line5)
        self.label_align_mode.setObjectName(u"label_align_mode")
        self.label_align_mode.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_line5.addWidget(self.label_align_mode)
        
        self.combo_align = QComboBox(self.widget_line5)
        self.combo_align.setObjectName(u"combo_align")
        sizePolicy2.setHeightForWidth(self.combo_align.sizePolicy().hasHeightForWidth())
        self.combo_align.setSizePolicy(sizePolicy2)
        self.combo_align.setMinimumSize(QSize(50, 30))
        
        self.horizontalLayout_line5.addWidget(self.combo_align)
        
        # 设置拉伸比例
        for i in range(6):
            self.horizontalLayout_line5.setStretch(i, 1)
        
        self.verticalLayout_detail.addWidget(self.widget_line5)
        
        self.verticalLayout.addWidget(self.widget_detail)
        
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
    
    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("TextComponent", u"文本组件", None))
        self.label_type.setText(QCoreApplication.translate("TextComponent", u"文本", None))
        self.label_name.setText(QCoreApplication.translate("TextComponent", u"未命名", None))
        self.checkbox_enable.setText(QCoreApplication.translate("TextComponent", u"启用", None))
        self.button_edit.setText(QCoreApplication.translate("TextComponent", u"展开", None))
        self.button_move_up.setText(QCoreApplication.translate("TextComponent", u"▲", None))
        self.button_move_down.setText(QCoreApplication.translate("TextComponent", u"▼", None))
        self.label_component_name.setText(QCoreApplication.translate("TextComponent", u"组件名称", None))
        self.button_delete.setText(QCoreApplication.translate("TextComponent", u"删除组件", None))
        self.label_text_content.setText(QCoreApplication.translate("TextComponent", u"文本内容", None))
        self.label_line_width.setText(QCoreApplication.translate("TextComponent", u"行宽", None))
        self.label_font.setText(QCoreApplication.translate("TextComponent", u"字体", None))
        self.label_text_size.setText(QCoreApplication.translate("TextComponent", u"字号", None))
        self.label_text_color.setText(QCoreApplication.translate("TextComponent", u"文字颜色", None))
        self.label_shadow_color.setText(QCoreApplication.translate("TextComponent", u"阴影颜色", None))
        self.label_shadow_x.setText(QCoreApplication.translate("TextComponent", u"阴影X", None))
        self.label_shadow_y.setText(QCoreApplication.translate("TextComponent", u"阴影Y", None))
        self.label_offset_x.setText(QCoreApplication.translate("TextComponent", u"X偏移", None))
        self.label_offset_y.setText(QCoreApplication.translate("TextComponent", u"Y偏移", None))
        self.label_align_mode.setText(QCoreApplication.translate("TextComponent", u"对齐方式", None))


class Ui_CharaCfg(object):
    """角色配置UI（用于主界面标签页）"""
    
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(695, 153)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QSize(0, 153))
        
        # 外层Frame，模仿主页背景标签页的结构
        self.frame_CharaCfg = QFrame(Form)
        self.frame_CharaCfg.setObjectName(u"frame_CharaCfg")
        self.frame_CharaCfg.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_CharaCfg.setFrameShadow(QFrame.Shadow.Raised)
        
        self.verticalLayout = QVBoxLayout(self.frame_CharaCfg)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        
        # 角色选择组
        self.groupBox_character = QGroupBox(self.frame_CharaCfg)
        self.groupBox_character.setObjectName(u"groupBox_character")
        
        self.horizontalLayout_group1 = QHBoxLayout(self.groupBox_character)
        self.horizontalLayout_group1.setObjectName(u"horizontalLayout_group1")
        self.horizontalLayout_group1.setContentsMargins(20, 0, 20, 5)
        
        self.label_character_select = QLabel(self.groupBox_character)
        self.label_character_select.setObjectName(u"label_character_select")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_character_select.sizePolicy().hasHeightForWidth())
        self.label_character_select.setSizePolicy(sizePolicy1)
        self.label_character_select.setMinimumSize(QSize(60, 0))
        
        self.horizontalLayout_group1.addWidget(self.label_character_select)
        
        self.combo_character_select = QComboBox(self.groupBox_character)
        self.combo_character_select.setObjectName(u"combo_character_select")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(1)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.combo_character_select.sizePolicy().hasHeightForWidth())
        self.combo_character_select.setSizePolicy(sizePolicy2)
        self.combo_character_select.setMinimumSize(QSize(100, 30))
        
        self.horizontalLayout_group1.addWidget(self.combo_character_select)
        
        self.label_poise_select = QLabel(self.groupBox_character)
        self.label_poise_select.setObjectName(u"label_poise_select")
        sizePolicy2.setHeightForWidth(self.label_poise_select.sizePolicy().hasHeightForWidth())
        self.label_poise_select.setSizePolicy(sizePolicy2)
        self.label_poise_select.setMinimumSize(QSize(0, 0))
        self.label_poise_select.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_group1.addWidget(self.label_poise_select)
        
        self.combo_poise_select = QComboBox(self.groupBox_character)
        self.combo_poise_select.setObjectName(u"combo_poise_select")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(1)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.combo_poise_select.sizePolicy().hasHeightForWidth())
        self.combo_poise_select.setSizePolicy(sizePolicy2)
        self.combo_poise_select.setMinimumSize(QSize(50, 30))

        self.horizontalLayout_group1.addWidget(self.combo_poise_select)
        
        self.label_clothes_select = QLabel(self.groupBox_character)
        self.label_clothes_select.setObjectName(u"label_clothes_select")
        sizePolicy2.setHeightForWidth(self.label_clothes_select.sizePolicy().hasHeightForWidth())
        self.label_clothes_select.setSizePolicy(sizePolicy2)
        self.label_clothes_select.setMinimumSize(QSize(0, 0))
        self.label_clothes_select.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.horizontalLayout_group1.addWidget(self.label_clothes_select)

        self.combo_clothes_select = QComboBox(self.groupBox_character)
        self.combo_clothes_select.setObjectName(u"combo_clothes_select")
        sizePolicy2.setHeightForWidth(self.combo_clothes_select.sizePolicy().hasHeightForWidth())
        self.combo_clothes_select.setSizePolicy(sizePolicy2)
        self.combo_clothes_select.setMinimumSize(QSize(50, 30))
        self.horizontalLayout_group1.addWidget(self.combo_clothes_select)

        self.label_action_select = QLabel(self.groupBox_character)
        self.label_action_select.setObjectName(u"label_action_select")
        sizePolicy2.setHeightForWidth(self.label_action_select.sizePolicy().hasHeightForWidth())
        self.label_action_select.setSizePolicy(sizePolicy2)
        self.label_action_select.setMinimumSize(QSize(0, 0))
        self.label_action_select.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_group1.addWidget(self.label_action_select)
        
        self.combo_action_select = QComboBox(self.groupBox_character)
        self.combo_action_select.setObjectName(u"combo_action_select")
        sizePolicy2.setHeightForWidth(self.combo_action_select.sizePolicy().hasHeightForWidth())
        self.combo_action_select.setSizePolicy(sizePolicy2)
        self.combo_action_select.setMinimumSize(QSize(50, 30))
        
        self.horizontalLayout_group1.addWidget(self.combo_action_select)
        
        # 设置拉伸比例
        self.horizontalLayout_group1.setStretch(0, 1)   # label_character_select
        self.horizontalLayout_group1.setStretch(1, 3)   # combo_character_select
        self.horizontalLayout_group1.setStretch(2, 1)   # label_poise_select
        self.horizontalLayout_group1.setStretch(3, 2)   # combo_poise_select
        self.horizontalLayout_group1.setStretch(4, 1)   # label_clothes_select
        self.horizontalLayout_group1.setStretch(5, 2)   # combo_clothes_select
        self.horizontalLayout_group1.setStretch(6, 1)   # label_action_select
        self.horizontalLayout_group1.setStretch(7, 2)   # combo_action_select
        
        self.verticalLayout.addWidget(self.groupBox_character)
        
        # 表情配置组
        self.groupBox_emotion = QGroupBox(self.frame_CharaCfg)
        self.groupBox_emotion.setObjectName(u"groupBox_emotion")
        
        self.horizontalLayout_group2 = QHBoxLayout(self.groupBox_emotion)
        self.horizontalLayout_group2.setObjectName(u"horizontalLayout_group2")
        self.horizontalLayout_group2.setContentsMargins(20, 0, 20, 5)
        
        self.checkbox_random_emotion = QCheckBox(self.groupBox_emotion)
        self.checkbox_random_emotion.setObjectName(u"checkbox_random_emotion")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(2)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.checkbox_random_emotion.sizePolicy().hasHeightForWidth())
        self.checkbox_random_emotion.setSizePolicy(sizePolicy4)
        self.checkbox_random_emotion.setMinimumSize(QSize(35, 0))
        
        self.horizontalLayout_group2.addWidget(self.checkbox_random_emotion)
        
        self.label_emotion_filter = QLabel(self.groupBox_emotion)
        self.label_emotion_filter.setObjectName(u"label_emotion_filter")
        sizePolicy1.setHeightForWidth(self.label_emotion_filter.sizePolicy().hasHeightForWidth())
        self.label_emotion_filter.setSizePolicy(sizePolicy1)
        self.label_emotion_filter.setMinimumSize(QSize(100, 0))
        self.label_emotion_filter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_group2.addWidget(self.label_emotion_filter)
        
        self.combo_emotion_filter = QComboBox(self.groupBox_emotion)
        self.combo_emotion_filter.setObjectName(u"combo_emotion_filter")
        sizePolicy3.setHeightForWidth(self.combo_emotion_filter.sizePolicy().hasHeightForWidth())
        self.combo_emotion_filter.setSizePolicy(sizePolicy3)
        
        self.horizontalLayout_group2.addWidget(self.combo_emotion_filter)
        
        self.label_emotion_select = QLabel(self.groupBox_emotion)
        self.label_emotion_select.setObjectName(u"label_emotion_select")
        sizePolicy1.setHeightForWidth(self.label_emotion_select.sizePolicy().hasHeightForWidth())
        self.label_emotion_select.setSizePolicy(sizePolicy1)
        self.label_emotion_select.setMinimumSize(QSize(100, 0))
        self.label_emotion_select.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.horizontalLayout_group2.addWidget(self.label_emotion_select)
        
        self.combo_emotion_select = QComboBox(self.groupBox_emotion)
        self.combo_emotion_select.setObjectName(u"combo_emotion_select")
        sizePolicy3.setHeightForWidth(self.combo_emotion_select.sizePolicy().hasHeightForWidth())
        self.combo_emotion_select.setSizePolicy(sizePolicy3)
        
        self.horizontalLayout_group2.addWidget(self.combo_emotion_select)
        
        # 设置拉伸比例
        self.horizontalLayout_group2.setStretch(0, 2)  # checkbox_random_emotion
        self.horizontalLayout_group2.setStretch(1, 0)  # label_emotion_filter
        self.horizontalLayout_group2.setStretch(2, 1)  # combo_emotion_filter
        self.horizontalLayout_group2.setStretch(3, 0)  # label_emotion_select
        self.horizontalLayout_group2.setStretch(4, 1)  # combo_emotion_select
        
        self.verticalLayout.addWidget(self.groupBox_emotion)
        
        # 设置外层Frame的布局
        self.verticalLayout_main = QVBoxLayout(Form)
        self.verticalLayout_main.setObjectName(u"verticalLayout_main")
        self.verticalLayout_main.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_main.addWidget(self.frame_CharaCfg)
        
        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
    
    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.groupBox_character.setTitle(QCoreApplication.translate("Form", u"角色配置", None))
        self.label_character_select.setText(QCoreApplication.translate("Form", u"选择角色", None))
        self.label_poise_select.setText(QCoreApplication.translate("Form", u"姿态选择", None))
        self.label_clothes_select.setText(QCoreApplication.translate("Form", u"服装选择", None))
        self.label_action_select.setText(QCoreApplication.translate("Form", u"动作选择", None))
        self.groupBox_emotion.setTitle(QCoreApplication.translate("Form", u"表情配置", None))
        self.checkbox_random_emotion.setText(QCoreApplication.translate("Form", u"随机表情", None))
        self.label_emotion_filter.setText(QCoreApplication.translate("Form", u"表情筛选", None))
        self.label_emotion_select.setText(QCoreApplication.translate("Form", u"表情选择", None))