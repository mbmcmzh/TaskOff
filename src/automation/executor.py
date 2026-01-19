"""
操作执行器模块
负责执行自动化操作序列
"""
import time
from typing import Callable, Optional
from ..models.action import Action, ActionType, ActionSequence
from .mouse_control import MouseController
from .keyboard_control import KeyboardController


class ActionExecutor:
    """操作执行器"""
    
    def __init__(self):
        self._mouse = MouseController()
        self._keyboard = KeyboardController()
        self._is_running = False
        self._on_action_start: Optional[Callable[[Action, int], None]] = None
        self._on_action_complete: Optional[Callable[[Action, int], None]] = None
        self._on_sequence_complete: Optional[Callable[[], None]] = None
        self._on_error: Optional[Callable[[Exception, Action], None]] = None
    
    def set_on_action_start(self, callback: Callable[[Action, int], None]):
        """设置操作开始回调，参数为(action, index)"""
        self._on_action_start = callback
    
    def set_on_action_complete(self, callback: Callable[[Action, int], None]):
        """设置操作完成回调，参数为(action, index)"""
        self._on_action_complete = callback
    
    def set_on_sequence_complete(self, callback: Callable[[], None]):
        """设置序列完成回调"""
        self._on_sequence_complete = callback
    
    def set_on_error(self, callback: Callable[[Exception, Action], None]):
        """设置错误回调"""
        self._on_error = callback
    
    def execute_action(self, action: Action) -> bool:
        """
        执行单个操作
        
        Args:
            action: 要执行的操作
            
        Returns:
            是否成功执行
        """
        if not action.enabled:
            return True
        
        try:
            params = action.params
            
            if action.action_type == ActionType.MOUSE_CLICK:
                self._mouse.click(
                    x=params.get('x'),
                    y=params.get('y'),
                    button=params.get('button', 'left')
                )
            
            elif action.action_type == ActionType.MOUSE_DOUBLE_CLICK:
                self._mouse.double_click(
                    x=params.get('x'),
                    y=params.get('y')
                )
            
            elif action.action_type == ActionType.MOUSE_RIGHT_CLICK:
                self._mouse.right_click(
                    x=params.get('x'),
                    y=params.get('y')
                )
            
            elif action.action_type == ActionType.MOUSE_MOVE:
                self._mouse.move_to(
                    x=params.get('x', 0),
                    y=params.get('y', 0),
                    duration=params.get('duration', 0.25)
                )
            
            elif action.action_type == ActionType.MOUSE_DRAG:
                self._mouse.drag_to(
                    x=params.get('x', 0),
                    y=params.get('y', 0),
                    duration=params.get('duration', 0.5)
                )
            
            elif action.action_type == ActionType.MOUSE_SCROLL:
                self._mouse.scroll(
                    clicks=params.get('amount', 0),
                    x=params.get('x'),
                    y=params.get('y')
                )
            
            elif action.action_type == ActionType.KEYBOARD_TYPE:
                text = params.get('text', '')
                interval = params.get('interval', 0.0)
                # 检查是否包含非ASCII字符（如中文）
                if any(ord(c) > 127 for c in text):
                    self._keyboard.type_unicode(text, interval)
                else:
                    self._keyboard.type_text(text, interval)
            
            elif action.action_type == ActionType.KEYBOARD_PRESS:
                self._keyboard.press_key(
                    key=params.get('key', ''),
                    presses=params.get('presses', 1)
                )
            
            elif action.action_type == ActionType.KEYBOARD_HOTKEY:
                keys = params.get('keys', [])
                self._keyboard.hotkey(*keys)
            
            elif action.action_type == ActionType.DELAY:
                seconds = params.get('seconds', 0)
                time.sleep(seconds)
            
            return True
        
        except Exception as e:
            if self._on_error:
                self._on_error(e, action)
            return False
    
    def execute_sequence(self, sequence: ActionSequence) -> bool:
        """
        执行操作序列
        
        Args:
            sequence: 操作序列
            
        Returns:
            是否全部成功执行
        """
        self._is_running = True
        success = True
        
        for index, action in enumerate(sequence.actions):
            if not self._is_running:
                success = False
                break
            
            if self._on_action_start:
                self._on_action_start(action, index)
            
            result = self.execute_action(action)
            
            if self._on_action_complete:
                self._on_action_complete(action, index)
            
            if not result:
                success = False
        
        self._is_running = False
        
        if self._on_sequence_complete:
            self._on_sequence_complete()
        
        return success
    
    def stop(self):
        """停止执行"""
        self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """是否正在执行"""
        return self._is_running
