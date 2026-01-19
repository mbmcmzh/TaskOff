"""
键盘控制模块
使用pyautogui实现键盘操作
"""
import pyautogui
import pyperclip
from typing import List, Union
import time


class KeyboardController:
    """键盘控制器"""
    
    # 常用特殊键映射
    SPECIAL_KEYS = {
        'enter': 'enter',
        'return': 'return',
        'tab': 'tab',
        'space': 'space',
        'backspace': 'backspace',
        'delete': 'delete',
        'escape': 'escape',
        'esc': 'escape',
        'up': 'up',
        'down': 'down',
        'left': 'left',
        'right': 'right',
        'home': 'home',
        'end': 'end',
        'pageup': 'pageup',
        'pagedown': 'pagedown',
        'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
        'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
        'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
        'ctrl': 'ctrl',
        'control': 'ctrl',
        'alt': 'alt',
        'shift': 'shift',
        'win': 'win',
        'windows': 'win',
        'command': 'command',
        'capslock': 'capslock',
        'numlock': 'numlock',
        'printscreen': 'printscreen',
        'insert': 'insert',
    }
    
    @staticmethod
    def type_text(text: str, interval: float = 0.0):
        """
        输入文本
        
        Args:
            text: 要输入的文本
            interval: 每个字符之间的间隔（秒）
        """
        pyautogui.typewrite(text, interval=interval)
    
    @staticmethod
    def type_unicode(text: str, interval: float = 0.0):
        """
        输入Unicode文本（支持中文等）
        使用剪贴板方式输入，支持中文、emoji等Unicode字符
        
        Args:
            text: 要输入的文本
            interval: 每个字符之间的间隔（秒）
        """
        # 保存原剪贴板内容
        original_clipboard = pyperclip.paste()
        
        try:
            if interval > 0:
                # 如果有间隔，逐字符输入
                for char in text:
                    pyperclip.copy(char)
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(interval)
            else:
                # 一次性输入全部文本
                pyperclip.copy(text)
                pyautogui.hotkey('ctrl', 'v')
        finally:
            # 恢复原剪贴板内容
            pyperclip.copy(original_clipboard)
    
    @staticmethod
    def press_key(key: str, presses: int = 1, interval: float = 0.0):
        """
        按下并释放按键
        
        Args:
            key: 按键名称
            presses: 按键次数
            interval: 多次按键之间的间隔
        """
        key = KeyboardController.SPECIAL_KEYS.get(key.lower(), key.lower())
        pyautogui.press(key, presses=presses, interval=interval)
    
    @staticmethod
    def key_down(key: str):
        """
        按下按键（不释放）
        
        Args:
            key: 按键名称
        """
        key = KeyboardController.SPECIAL_KEYS.get(key.lower(), key.lower())
        pyautogui.keyDown(key)
    
    @staticmethod
    def key_up(key: str):
        """
        释放按键
        
        Args:
            key: 按键名称
        """
        key = KeyboardController.SPECIAL_KEYS.get(key.lower(), key.lower())
        pyautogui.keyUp(key)
    
    @staticmethod
    def hotkey(*keys: str, interval: float = 0.0):
        """
        按下组合键
        
        Args:
            *keys: 按键序列，如 'ctrl', 'c' 表示 Ctrl+C
            interval: 按键之间的间隔
        """
        mapped_keys = [KeyboardController.SPECIAL_KEYS.get(k.lower(), k.lower()) 
                       for k in keys]
        pyautogui.hotkey(*mapped_keys, interval=interval)
    
    @staticmethod
    def ctrl_c():
        """复制快捷键"""
        pyautogui.hotkey('ctrl', 'c')
    
    @staticmethod
    def ctrl_v():
        """粘贴快捷键"""
        pyautogui.hotkey('ctrl', 'v')
    
    @staticmethod
    def ctrl_x():
        """剪切快捷键"""
        pyautogui.hotkey('ctrl', 'x')
    
    @staticmethod
    def ctrl_z():
        """撤销快捷键"""
        pyautogui.hotkey('ctrl', 'z')
    
    @staticmethod
    def ctrl_a():
        """全选快捷键"""
        pyautogui.hotkey('ctrl', 'a')
    
    @staticmethod
    def ctrl_s():
        """保存快捷键"""
        pyautogui.hotkey('ctrl', 's')
    
    @staticmethod
    def alt_tab():
        """切换窗口"""
        pyautogui.hotkey('alt', 'tab')
    
    @staticmethod
    def alt_f4():
        """关闭窗口"""
        pyautogui.hotkey('alt', 'f4')
    
    @staticmethod
    def enter():
        """按回车键"""
        pyautogui.press('enter')
    
    @staticmethod
    def escape():
        """按ESC键"""
        pyautogui.press('escape')
    
    @staticmethod
    def tab():
        """按Tab键"""
        pyautogui.press('tab')
    
    @staticmethod
    def backspace(count: int = 1):
        """
        按退格键
        
        Args:
            count: 按键次数
        """
        pyautogui.press('backspace', presses=count)
    
    @staticmethod
    def delete(count: int = 1):
        """
        按删除键
        
        Args:
            count: 按键次数
        """
        pyautogui.press('delete', presses=count)
