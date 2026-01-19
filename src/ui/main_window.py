"""
PyQt5 主窗口界面
包含倒计时设置、操作序列编辑器、控制按钮等
"""
import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QComboBox, QLineEdit, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QFileDialog, QMenu, QAction,
    QCheckBox, QDoubleSpinBox, QFrame, QSplitter, QStatusBar,
    QSystemTrayIcon, QStyle
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QPoint
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QCursor
from pynput import keyboard as pynput_keyboard

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.scheduler import ShutdownScheduler
from src.core.shutdown import ShutdownController
from src.models.action import (
    Action, ActionType, ActionSequence,
    create_mouse_click, create_mouse_double_click, create_mouse_right_click,
    create_mouse_move, create_mouse_scroll, create_keyboard_type,
    create_keyboard_press, create_keyboard_hotkey, create_delay
)
from src.automation.executor import ActionExecutor
from src.automation.mouse_control import MouseController


class MousePositionCapture(QDialog):
    """鼠标位置捕获对话框"""
    
    position_captured = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("捕获鼠标位置")
        self.setModal(True)
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        
        self.info_label = QLabel("按下 F2 键捕获当前鼠标位置（无需前台）\n按 ESC 取消")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(self.info_label)
        
        self.position_label = QLabel("当前位置: (-, -)")
        self.position_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.position_label)
        
        # 定时更新鼠标位置
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(50)
        
        self.captured_x = 0
        self.captured_y = 0
        self._hotkey_listener = None
        self._start_global_hotkey_listener()
    
    def update_position(self):
        """更新鼠标位置显示"""
        try:
            x, y = MouseController.get_position()
            self.position_label.setText(f"当前位置: ({x}, {y})")
            self.captured_x = x
            self.captured_y = y
        except:
            pass

    def _start_global_hotkey_listener(self):
        """启动全局热键监听（F2/ESC）"""
        def on_press(key):
            if key == pynput_keyboard.Key.f2:
                QTimer.singleShot(0, self._capture_from_hotkey)
            elif key == pynput_keyboard.Key.esc:
                QTimer.singleShot(0, self.reject)

        self._hotkey_listener = pynput_keyboard.Listener(on_press=on_press)
        self._hotkey_listener.daemon = True
        self._hotkey_listener.start()

    def _stop_global_hotkey_listener(self):
        """停止全局热键监听"""
        if self._hotkey_listener:
            self._hotkey_listener.stop()
            self._hotkey_listener = None

    def _capture_from_hotkey(self):
        """从全局热键触发捕获"""
        self.position_captured.emit(self.captured_x, self.captured_y)
        self.accept()
    
    def keyPressEvent(self, event):
        """按键事件"""
        if event.key() == Qt.Key_F2:
            self.position_captured.emit(self.captured_x, self.captured_y)
            self.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.timer.stop()
        self._stop_global_hotkey_listener()
        super().closeEvent(event)


class ActionEditDialog(QDialog):
    """操作编辑对话框"""
    
    def __init__(self, action: Action = None, parent=None):
        super().__init__(parent)
        self.action = action
        self.setWindowTitle("编辑操作" if action else "添加操作")
        self.setModal(True)
        self.resize(400, 300)
        
        self.setup_ui()
        
        if action:
            self.load_action(action)
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 操作类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("操作类型:"))
        self.type_combo = QComboBox()
        for action_type in ActionType:
            self.type_combo.addItem(action_type.get_display_name(), action_type)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # 参数区域
        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        layout.addWidget(self.params_widget)
        
        # 初始化参数控件
        self.setup_params_widgets()
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.on_type_changed(0)
    
    def setup_params_widgets(self):
        """创建所有可能的参数控件"""
        # 鼠标坐标
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 9999)
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 9999)
        
        # 捕获位置按钮
        self.capture_btn = QPushButton("捕获位置 (F2)")
        self.capture_btn.clicked.connect(self.capture_position)
        
        # 鼠标按钮
        self.button_combo = QComboBox()
        self.button_combo.addItems(["left", "right", "middle"])
        
        # 持续时间
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.0, 10.0)
        self.duration_spin.setSingleStep(0.1)
        self.duration_spin.setValue(0.25)
        
        # 滚动量
        self.scroll_spin = QSpinBox()
        self.scroll_spin.setRange(-100, 100)
        
        # 文本输入
        self.text_edit = QLineEdit()
        
        # 按键输入
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("如: enter, tab, f1, ctrl")
        
        # 组合键输入
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("如: ctrl+c, alt+tab")
        
        # 延迟时间
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 3600.0)
        self.delay_spin.setSingleStep(0.5)
        self.delay_spin.setValue(1.0)
        
        # 按键次数
        self.presses_spin = QSpinBox()
        self.presses_spin.setRange(1, 100)
        self.presses_spin.setValue(1)
    
    def clear_params_layout(self):
        """清空参数布局"""
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
    
    def on_type_changed(self, index):
        """操作类型改变时更新参数界面"""
        self.clear_params_layout()
        
        action_type = self.type_combo.currentData()
        
        if action_type in [ActionType.MOUSE_CLICK, ActionType.MOUSE_DOUBLE_CLICK,
                           ActionType.MOUSE_RIGHT_CLICK, ActionType.MOUSE_MOVE,
                           ActionType.MOUSE_DRAG]:
            coord_widget = QWidget()
            coord_layout = QHBoxLayout(coord_widget)
            coord_layout.setContentsMargins(0, 0, 0, 0)
            coord_layout.addWidget(QLabel("X:"))
            coord_layout.addWidget(self.x_spin)
            coord_layout.addWidget(QLabel("Y:"))
            coord_layout.addWidget(self.y_spin)
            coord_layout.addWidget(self.capture_btn)
            self.params_layout.addRow("坐标:", coord_widget)
            
            if action_type == ActionType.MOUSE_CLICK:
                self.params_layout.addRow("鼠标按键:", self.button_combo)
            
            if action_type in [ActionType.MOUSE_MOVE, ActionType.MOUSE_DRAG]:
                self.params_layout.addRow("持续时间(秒):", self.duration_spin)
        
        elif action_type == ActionType.MOUSE_SCROLL:
            coord_widget = QWidget()
            coord_layout = QHBoxLayout(coord_widget)
            coord_layout.setContentsMargins(0, 0, 0, 0)
            coord_layout.addWidget(QLabel("X:"))
            coord_layout.addWidget(self.x_spin)
            coord_layout.addWidget(QLabel("Y:"))
            coord_layout.addWidget(self.y_spin)
            coord_layout.addWidget(self.capture_btn)
            self.params_layout.addRow("位置(可选):", coord_widget)
            self.params_layout.addRow("滚动量(正向上):", self.scroll_spin)
        
        elif action_type == ActionType.KEYBOARD_TYPE:
            self.params_layout.addRow("输入文本:", self.text_edit)
        
        elif action_type == ActionType.KEYBOARD_PRESS:
            self.params_layout.addRow("按键:", self.key_edit)
            self.params_layout.addRow("按键次数:", self.presses_spin)
        
        elif action_type == ActionType.KEYBOARD_HOTKEY:
            self.params_layout.addRow("组合键:", self.hotkey_edit)
        
        elif action_type == ActionType.DELAY:
            self.params_layout.addRow("延迟时间(秒):", self.delay_spin)
    
    def capture_position(self):
        """捕获鼠标位置"""
        dialog = MousePositionCapture(self)
        dialog.position_captured.connect(self.on_position_captured)
        dialog.exec_()
    
    def on_position_captured(self, x, y):
        """位置捕获回调"""
        self.x_spin.setValue(x)
        self.y_spin.setValue(y)
    
    def load_action(self, action: Action):
        """加载现有操作"""
        # 设置类型
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == action.action_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        params = action.params
        
        if action.action_type in [ActionType.MOUSE_CLICK, ActionType.MOUSE_DOUBLE_CLICK,
                                   ActionType.MOUSE_RIGHT_CLICK, ActionType.MOUSE_MOVE,
                                   ActionType.MOUSE_DRAG]:
            self.x_spin.setValue(params.get('x', 0))
            self.y_spin.setValue(params.get('y', 0))
            if 'button' in params:
                index = self.button_combo.findText(params['button'])
                if index >= 0:
                    self.button_combo.setCurrentIndex(index)
            if 'duration' in params:
                self.duration_spin.setValue(params['duration'])
        
        elif action.action_type == ActionType.MOUSE_SCROLL:
            self.x_spin.setValue(params.get('x', 0) or 0)
            self.y_spin.setValue(params.get('y', 0) or 0)
            self.scroll_spin.setValue(params.get('amount', 0))
        
        elif action.action_type == ActionType.KEYBOARD_TYPE:
            self.text_edit.setText(params.get('text', ''))
        
        elif action.action_type == ActionType.KEYBOARD_PRESS:
            self.key_edit.setText(params.get('key', ''))
            self.presses_spin.setValue(params.get('presses', 1))
        
        elif action.action_type == ActionType.KEYBOARD_HOTKEY:
            keys = params.get('keys', [])
            self.hotkey_edit.setText('+'.join(keys))
        
        elif action.action_type == ActionType.DELAY:
            self.delay_spin.setValue(params.get('seconds', 1.0))
    
    def get_action(self) -> Action:
        """获取编辑后的操作"""
        action_type = self.type_combo.currentData()
        params = {}
        
        if action_type in [ActionType.MOUSE_CLICK, ActionType.MOUSE_DOUBLE_CLICK,
                           ActionType.MOUSE_RIGHT_CLICK, ActionType.MOUSE_MOVE,
                           ActionType.MOUSE_DRAG]:
            params['x'] = self.x_spin.value()
            params['y'] = self.y_spin.value()
            if action_type == ActionType.MOUSE_CLICK:
                params['button'] = self.button_combo.currentText()
            if action_type in [ActionType.MOUSE_MOVE, ActionType.MOUSE_DRAG]:
                params['duration'] = self.duration_spin.value()
        
        elif action_type == ActionType.MOUSE_SCROLL:
            x = self.x_spin.value()
            y = self.y_spin.value()
            params['x'] = x if x > 0 else None
            params['y'] = y if y > 0 else None
            params['amount'] = self.scroll_spin.value()
        
        elif action_type == ActionType.KEYBOARD_TYPE:
            params['text'] = self.text_edit.text()
        
        elif action_type == ActionType.KEYBOARD_PRESS:
            params['key'] = self.key_edit.text()
            params['presses'] = self.presses_spin.value()
        
        elif action_type == ActionType.KEYBOARD_HOTKEY:
            keys_text = self.hotkey_edit.text()
            params['keys'] = [k.strip() for k in keys_text.split('+') if k.strip()]
        
        elif action_type == ActionType.DELAY:
            params['seconds'] = self.delay_spin.value()
        
        if self.action:
            self.action.action_type = action_type
            self.action.params = params
            self.action.update_description()
            return self.action
        else:
            return Action(action_type=action_type, params=params)


class WarningDialog(QDialog):
    """关机警告对话框"""
    
    cancelled = pyqtSignal()
    
    def __init__(self, seconds: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚠️ 关机警告")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(400, 200)
        
        self.remaining = seconds
        
        layout = QVBoxLayout(self)
        
        # 警告图标和文字
        warning_label = QLabel("⚠️ 系统即将关机！")
        warning_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #ff6b6b;")
        layout.addWidget(warning_label)
        
        # 倒计时显示
        self.countdown_label = QLabel(f"剩余 {seconds} 秒")
        self.countdown_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.countdown_label)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消关机")
        self.cancel_btn.setFont(QFont("Microsoft YaHei", 12))
        self.cancel_btn.setMinimumHeight(50)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #ee5a5a;
            }
        """)
        self.cancel_btn.clicked.connect(self.on_cancel)
        layout.addWidget(self.cancel_btn)
        
        # 倒计时更新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
    
    def update_countdown(self):
        """更新倒计时"""
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.accept()
        else:
            self.countdown_label.setText(f"剩余 {self.remaining} 秒")
    
    def on_cancel(self):
        """取消关机"""
        self.timer.stop()
        self.cancelled.emit()
        self.reject()
    
    def update_remaining(self, seconds: int):
        """更新剩余时间"""
        self.remaining = seconds
        self.countdown_label.setText(f"剩余 {seconds} 秒")


class ExecutionThread(QThread):
    """操作执行线程"""
    
    action_started = pyqtSignal(str, int)  # action_id, index
    action_completed = pyqtSignal(str, int)  # action_id, index
    sequence_completed = pyqtSignal()
    error_occurred = pyqtSignal(str, str)  # error_msg, action_id
    
    def __init__(self, sequence: ActionSequence, parent=None):
        super().__init__(parent)
        self.sequence = sequence
        self.executor = ActionExecutor()
    
    def run(self):
        """执行操作序列"""
        def on_start(action, index):
            self.action_started.emit(action.id, index)
        
        def on_complete(action, index):
            self.action_completed.emit(action.id, index)
        
        def on_error(e, action):
            self.error_occurred.emit(str(e), action.id)
        
        self.executor.set_on_action_start(on_start)
        self.executor.set_on_action_complete(on_complete)
        self.executor.set_on_error(on_error)
        
        self.executor.execute_sequence(self.sequence)
        self.sequence_completed.emit()
    
    def stop(self):
        """停止执行"""
        self.executor.stop()


class MainWindow(QMainWindow):
    """主窗口"""
    countdown_tick = pyqtSignal(int)
    countdown_warning = pyqtSignal(int)
    countdown_complete = pyqtSignal()
    
    # 设置文件路径
    SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "settings.json")
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TaskOff - 定时关机自动化工具")
        self.setMinimumSize(800, 600)
        
        # 初始化组件
        self.scheduler = ShutdownScheduler()
        self.sequence = ActionSequence()
        self.execution_thread = None
        self.warning_dialog = None
        self._system_shutdown_scheduled = False
        
        self.setup_ui()
        self.setup_scheduler()
        self.setup_tray()
        
        # 加载保存的设置
        self.load_settings()

        # 线程安全的UI更新信号
        self.countdown_tick.connect(self._update_countdown_display)
        self.countdown_warning.connect(self._show_warning_dialog)
        self.countdown_complete.connect(self._execute_shutdown)
        
        # 启动UI更新定时器
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_ui_state)
        self.ui_timer.start(100)
    
    def setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("TaskOff 定时关机工具")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 主内容区域
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：倒计时设置和控制
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 倒计时设置组
        countdown_group = QGroupBox("倒计时设置")
        countdown_layout = QVBoxLayout(countdown_group)
        
        # 时间设置
        time_layout = QHBoxLayout()
        
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setSuffix(" 小时")
        time_layout.addWidget(self.hours_spin)
        
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setSuffix(" 分钟")
        self.minutes_spin.setValue(30)
        time_layout.addWidget(self.minutes_spin)
        
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(0, 59)
        self.seconds_spin.setSuffix(" 秒")
        time_layout.addWidget(self.seconds_spin)
        
        countdown_layout.addLayout(time_layout)
        
        # 快捷按钮
        quick_layout = QHBoxLayout()
        for mins, label in [(5, "5分钟"), (15, "15分钟"), (30, "30分钟"), (60, "1小时")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, m=mins: self.set_quick_time(m))
            quick_layout.addWidget(btn)
        countdown_layout.addLayout(quick_layout)
        
        left_layout.addWidget(countdown_group)
        
        # 倒计时显示
        display_group = QGroupBox("当前状态")
        display_layout = QVBoxLayout(display_group)
        
        self.countdown_display = QLabel("00:00:00")
        self.countdown_display.setFont(QFont("Consolas", 48, QFont.Bold))
        self.countdown_display.setAlignment(Qt.AlignCenter)
        self.countdown_display.setStyleSheet("color: #4CAF50;")
        display_layout.addWidget(self.countdown_display)
        
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Microsoft YaHei", 12))
        display_layout.addWidget(self.status_label)
        
        left_layout.addWidget(display_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ 开始")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setFont(QFont("Microsoft YaHei", 12))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_btn.clicked.connect(self.start_countdown)
        control_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("■ 取消")
        self.cancel_btn.setMinimumHeight(50)
        self.cancel_btn.setFont(QFont("Microsoft YaHei", 12))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_countdown)
        self.cancel_btn.setEnabled(False)
        control_layout.addWidget(self.cancel_btn)
        
        left_layout.addLayout(control_layout)
        
        # 关机选项
        options_group = QGroupBox("关机选项")
        options_layout = QVBoxLayout(options_group)
        
        self.force_check = QCheckBox("强制关闭应用程序")
        options_layout.addWidget(self.force_check)
        
        self.run_actions_check = QCheckBox("关机前执行操作序列")
        self.run_actions_check.setChecked(True)
        options_layout.addWidget(self.run_actions_check)
        
        self.warning_check = QCheckBox("最后30秒弹窗提醒")
        self.warning_check.setChecked(True)
        options_layout.addWidget(self.warning_check)
        
        left_layout.addWidget(options_group)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # 右侧：操作序列编辑器
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        actions_group = QGroupBox("自动化操作序列")
        actions_layout = QVBoxLayout(actions_group)
        
        # 操作列表
        self.actions_list = QListWidget()
        self.actions_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.actions_list.customContextMenuRequested.connect(self.show_action_menu)
        self.actions_list.itemDoubleClicked.connect(self.edit_action)
        actions_layout.addWidget(self.actions_list)
        
        # 操作按钮
        action_btns_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.clicked.connect(self.add_action)
        action_btns_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ 编辑")
        self.edit_btn.clicked.connect(self.edit_selected_action)
        action_btns_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ 删除")
        self.delete_btn.clicked.connect(self.delete_action)
        action_btns_layout.addWidget(self.delete_btn)
        
        self.move_up_btn = QPushButton("⬆️")
        self.move_up_btn.clicked.connect(self.move_action_up)
        action_btns_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("⬇️")
        self.move_down_btn.clicked.connect(self.move_action_down)
        action_btns_layout.addWidget(self.move_down_btn)
        
        actions_layout.addLayout(action_btns_layout)
        
        # 序列操作按钮
        sequence_btns_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🎬 测试运行")
        self.test_btn.clicked.connect(self.test_sequence)
        sequence_btns_layout.addWidget(self.test_btn)
        
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_sequence)
        sequence_btns_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("📂 加载")
        self.load_btn.clicked.connect(self.load_sequence)
        sequence_btns_layout.addWidget(self.load_btn)
        
        self.clear_btn = QPushButton("🧹 清空")
        self.clear_btn.clicked.connect(self.clear_sequence)
        sequence_btns_layout.addWidget(self.clear_btn)
        
        actions_layout.addLayout(sequence_btns_layout)
        
        right_layout.addWidget(actions_group)
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([400, 400])
        
        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
    
    def setup_scheduler(self):
        """设置调度器回调"""
        self.scheduler.set_on_tick(self.on_countdown_tick)
        self.scheduler.set_on_complete(self.on_countdown_complete)
        self.scheduler.set_on_warning(self.on_warning)
    
    def setup_tray(self):
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        cancel_action = tray_menu.addAction("取消关机")
        cancel_action.triggered.connect(self.cancel_countdown)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def set_quick_time(self, minutes: int):
        """设置快捷时间"""
        self.hours_spin.setValue(minutes // 60)
        self.minutes_spin.setValue(minutes % 60)
        self.seconds_spin.setValue(0)
    
    def start_countdown(self):
        """开始倒计时"""
        total_seconds = ShutdownScheduler.calculate_seconds(
            self.hours_spin.value(),
            self.minutes_spin.value(),
            self.seconds_spin.value()
        )
        
        if total_seconds <= 0:
            QMessageBox.warning(self, "警告", "请设置有效的倒计时时间")
            return
        
        self.scheduler.start(total_seconds)
        self._update_countdown_display(total_seconds)
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("倒计时进行中...")
        self.statusBar.showMessage(f"已开始 {ShutdownScheduler.format_time(total_seconds)} 倒计时")
    
    def cancel_countdown(self):
        """取消倒计时"""
        self.scheduler.cancel()
        if self._system_shutdown_scheduled:
            ShutdownController.cancel_shutdown()
            self._system_shutdown_scheduled = False
        
        if self.warning_dialog:
            self.warning_dialog.reject()
            self.warning_dialog = None
        
        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.stop()
        
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.countdown_display.setText("00:00:00")
        self.countdown_display.setStyleSheet("color: #4CAF50;")
        self.status_label.setText("已取消")
        self.statusBar.showMessage("倒计时已取消")
    
    def on_countdown_tick(self, remaining: int):
        """倒计时每秒回调"""
        # 线程安全地通知主线程更新UI
        self.countdown_tick.emit(remaining)
    
    def _update_countdown_display(self, remaining: int):
        """更新倒计时显示"""
        self.countdown_display.setText(ShutdownScheduler.format_time(remaining))
        
        # 最后30秒变红
        if remaining <= 30:
            self.countdown_display.setStyleSheet("color: #f44336;")
        elif remaining <= 60:
            self.countdown_display.setStyleSheet("color: #ff9800;")
        else:
            self.countdown_display.setStyleSheet("color: #4CAF50;")
        
        # 更新托盘提示
        self.tray_icon.setToolTip(f"TaskOff - 剩余 {ShutdownScheduler.format_time(remaining)}")
        
        # 更新警告对话框
        if self.warning_dialog and self.warning_dialog.isVisible():
            self.warning_dialog.update_remaining(remaining)
    
    def on_warning(self, remaining: int):
        """进入警告时间回调"""
        self.countdown_warning.emit(remaining)
    
    def _show_warning_dialog(self, remaining: int):
        """显示警告对话框"""
        if not self.warning_check.isChecked():
            return
        self.warning_dialog = WarningDialog(remaining, self)
        self.warning_dialog.cancelled.connect(self.cancel_countdown)
        self.warning_dialog.show()
        self.activateWindow()
        self.raise_()
    
    def on_countdown_complete(self):
        """倒计时完成回调"""
        self.countdown_complete.emit()
    
    def _execute_shutdown(self):
        """执行关机"""
        self.status_label.setText("正在执行...")
        
        # 先执行自动化操作
        if self.run_actions_check.isChecked() and len(self.sequence.actions) > 0:
            self.statusBar.showMessage("正在执行自动化操作...")
            self.execution_thread = ExecutionThread(self.sequence, self)
            self.execution_thread.sequence_completed.connect(self._do_shutdown)
            self.execution_thread.start()
        else:
            self._do_shutdown()
    
    def _do_shutdown(self):
        """执行关机命令"""
        self.statusBar.showMessage("正在关机...")
        ShutdownController.shutdown(
            delay=0,
            force=self.force_check.isChecked(),
            message="TaskOff 定时关机"
        )
    
    def update_ui_state(self):
        """更新UI状态"""
        has_selection = len(self.actions_list.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.move_up_btn.setEnabled(has_selection)
        self.move_down_btn.setEnabled(has_selection)
    
    def refresh_actions_list(self):
        """刷新操作列表"""
        self.actions_list.clear()
        for i, action in enumerate(self.sequence.actions):
            item = QListWidgetItem(f"{i+1}. [{action.action_type.get_display_name()}] {action.description}")
            item.setData(Qt.UserRole, action.id)
            if not action.enabled:
                item.setForeground(QColor(150, 150, 150))
            self.actions_list.addItem(item)
    
    def add_action(self):
        """添加操作"""
        dialog = ActionEditDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            action = dialog.get_action()
            self.sequence.add_action(action)
            self.refresh_actions_list()
            self.statusBar.showMessage(f"已添加操作: {action.description}")
    
    def edit_action(self, item: QListWidgetItem):
        """编辑操作（双击）"""
        action_id = item.data(Qt.UserRole)
        action = self.sequence.get_action(action_id)
        if action:
            dialog = ActionEditDialog(action, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                dialog.get_action()  # 更新action
                self.refresh_actions_list()
    
    def edit_selected_action(self):
        """编辑选中的操作"""
        items = self.actions_list.selectedItems()
        if items:
            self.edit_action(items[0])
    
    def delete_action(self):
        """删除操作"""
        items = self.actions_list.selectedItems()
        if items:
            action_id = items[0].data(Qt.UserRole)
            self.sequence.remove_action(action_id)
            self.refresh_actions_list()
            self.statusBar.showMessage("已删除操作")
    
    def move_action_up(self):
        """上移操作"""
        current_row = self.actions_list.currentRow()
        if current_row > 0:
            self.sequence.move_action(current_row, current_row - 1)
            self.refresh_actions_list()
            self.actions_list.setCurrentRow(current_row - 1)
    
    def move_action_down(self):
        """下移操作"""
        current_row = self.actions_list.currentRow()
        if current_row < len(self.sequence.actions) - 1:
            self.sequence.move_action(current_row, current_row + 1)
            self.refresh_actions_list()
            self.actions_list.setCurrentRow(current_row + 1)
    
    def show_action_menu(self, pos: QPoint):
        """显示操作右键菜单"""
        item = self.actions_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            
            edit_action = menu.addAction("编辑")
            edit_action.triggered.connect(lambda: self.edit_action(item))
            
            toggle_action = menu.addAction("启用/禁用")
            toggle_action.triggered.connect(lambda: self.toggle_action(item))
            
            menu.addSeparator()
            
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(self.delete_action)
            
            menu.exec_(self.actions_list.mapToGlobal(pos))
    
    def toggle_action(self, item: QListWidgetItem):
        """切换操作启用状态"""
        action_id = item.data(Qt.UserRole)
        action = self.sequence.get_action(action_id)
        if action:
            action.enabled = not action.enabled
            self.refresh_actions_list()
    
    def test_sequence(self):
        """测试运行操作序列"""
        if len(self.sequence.actions) == 0:
            QMessageBox.information(self, "提示", "操作序列为空")
            return
        
        reply = QMessageBox.question(
            self, "确认", 
            "将在3秒后开始测试运行操作序列，请确保窗口已准备好。\n\n继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.statusBar.showMessage("3秒后开始测试...")
            QTimer.singleShot(3000, self._run_test)
    
    def _run_test(self):
        """执行测试"""
        self.statusBar.showMessage("正在测试运行...")
        self.execution_thread = ExecutionThread(self.sequence, self)
        self.execution_thread.action_started.connect(
            lambda id, idx: self.statusBar.showMessage(f"执行操作 {idx+1}/{len(self.sequence.actions)}")
        )
        self.execution_thread.sequence_completed.connect(
            lambda: self.statusBar.showMessage("测试完成")
        )
        self.execution_thread.error_occurred.connect(
            lambda err, id: QMessageBox.warning(self, "错误", f"操作执行失败: {err}")
        )
        self.execution_thread.start()
    
    def save_sequence(self):
        """保存操作序列"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存操作序列", "", "JSON文件 (*.json)"
        )
        if filepath:
            try:
                self.sequence.save_to_file(filepath)
                self.statusBar.showMessage(f"已保存到: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def load_sequence(self):
        """加载操作序列"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "加载操作序列", "", "JSON文件 (*.json)"
        )
        if filepath:
            try:
                self.sequence = ActionSequence.load_from_file(filepath)
                self.refresh_actions_list()
                self.statusBar.showMessage(f"已加载: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")
    
    def clear_sequence(self):
        """清空操作序列"""
        if len(self.sequence.actions) > 0:
            reply = QMessageBox.question(
                self, "确认", "确定要清空所有操作吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.sequence.clear()
                self.refresh_actions_list()
                self.statusBar.showMessage("已清空操作序列")
    
    def on_tray_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
            self.raise_()
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.scheduler.is_running:
            reply = QMessageBox.question(
                self, "确认",
                "倒计时正在进行中，确定要关闭吗？\n\n选择\"是\"将取消倒计时并关闭程序\n选择\"否\"将最小化到系统托盘",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.cancel_countdown()
                self.save_settings()
                event.accept()
            elif reply == QMessageBox.No:
                event.ignore()
                self.hide()
            else:
                event.ignore()
        else:
            self.save_settings()
            event.accept()
    
    def quit_app(self):
        """退出应用"""
        self.cancel_countdown()
        self.save_settings()
        self.tray_icon.hide()
        QApplication.quit()
    
    def save_settings(self):
        """保存设置到文件"""
        try:
            settings = {
                'countdown': {
                    'hours': self.hours_spin.value(),
                    'minutes': self.minutes_spin.value(),
                    'seconds': self.seconds_spin.value(),
                },
                'options': {
                    'force_close': self.force_check.isChecked(),
                    'run_actions': self.run_actions_check.isChecked(),
                    'warning_popup': self.warning_check.isChecked(),
                },
                'window': {
                    'width': self.width(),
                    'height': self.height(),
                    'x': self.x(),
                    'y': self.y(),
                }
            }
            with open(self.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def load_settings(self):
        """从文件加载设置"""
        try:
            if not os.path.exists(self.SETTINGS_FILE):
                return
            
            with open(self.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 加载倒计时设置
            countdown = settings.get('countdown', {})
            self.hours_spin.setValue(countdown.get('hours', 0))
            self.minutes_spin.setValue(countdown.get('minutes', 30))
            self.seconds_spin.setValue(countdown.get('seconds', 0))
            
            # 加载选项设置
            options = settings.get('options', {})
            self.force_check.setChecked(options.get('force_close', False))
            self.run_actions_check.setChecked(options.get('run_actions', True))
            self.warning_check.setChecked(options.get('warning_popup', True))
            
            # 加载窗口位置和大小
            window = settings.get('window', {})
            if window:
                self.resize(window.get('width', 800), window.get('height', 600))
                # 确保窗口在屏幕范围内
                x = window.get('x', 100)
                y = window.get('y', 100)
                screen = QApplication.primaryScreen().geometry()
                if 0 <= x < screen.width() - 100 and 0 <= y < screen.height() - 100:
                    self.move(x, y)
            
            self.statusBar.showMessage("已加载上次的设置")
        except Exception as e:
            print(f"加载设置失败: {e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用信息
    app.setApplicationName("TaskOff")
    app.setApplicationDisplayName("TaskOff - 定时关机自动化工具")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
