"""
鼠标控制模块
使用pyautogui实现鼠标操作
"""
import pyautogui
from typing import Tuple, Optional
import time


# 配置pyautogui的安全设置
pyautogui.FAILSAFE = True  # 移动鼠标到屏幕角落可以中断
pyautogui.PAUSE = 0.1  # 每个操作后的默认暂停时间


class MouseController:
    """鼠标控制器"""
    
    @staticmethod
    def get_position() -> Tuple[int, int]:
        """
        获取当前鼠标位置
        
        Returns:
            (x, y) 坐标元组
        """
        return pyautogui.position()
    
    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """
        获取屏幕分辨率
        
        Returns:
            (width, height) 元组
        """
        return pyautogui.size()
    
    @staticmethod
    def move_to(x: int, y: int, duration: float = 0.25):
        """
        移动鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动持续时间（秒）
        """
        pyautogui.moveTo(x, y, duration=duration)
    
    @staticmethod
    def move_relative(x_offset: int, y_offset: int, duration: float = 0.25):
        """
        相对当前位置移动鼠标
        
        Args:
            x_offset: X方向偏移量
            y_offset: Y方向偏移量
            duration: 移动持续时间（秒）
        """
        pyautogui.moveRel(x_offset, y_offset, duration=duration)
    
    @staticmethod
    def click(x: Optional[int] = None, y: Optional[int] = None, 
              clicks: int = 1, interval: float = 0.0, button: str = 'left'):
        """
        点击鼠标
        
        Args:
            x: 点击位置X坐标（None表示当前位置）
            y: 点击位置Y坐标（None表示当前位置）
            clicks: 点击次数
            interval: 多次点击之间的间隔（秒）
            button: 鼠标按键 ('left', 'right', 'middle')
        """
        pyautogui.click(x=x, y=y, clicks=clicks, interval=interval, button=button)
    
    @staticmethod
    def double_click(x: Optional[int] = None, y: Optional[int] = None, 
                     interval: float = 0.0, button: str = 'left'):
        """
        双击鼠标
        
        Args:
            x: 点击位置X坐标
            y: 点击位置Y坐标
            interval: 两次点击之间的间隔
            button: 鼠标按键
        """
        pyautogui.doubleClick(x=x, y=y, interval=interval, button=button)
    
    @staticmethod
    def right_click(x: Optional[int] = None, y: Optional[int] = None):
        """
        右键点击
        
        Args:
            x: 点击位置X坐标
            y: 点击位置Y坐标
        """
        pyautogui.rightClick(x=x, y=y)
    
    @staticmethod
    def drag_to(x: int, y: int, duration: float = 0.5, button: str = 'left'):
        """
        拖拽到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 拖拽持续时间
            button: 使用的鼠标按键
        """
        pyautogui.dragTo(x, y, duration=duration, button=button)
    
    @staticmethod
    def drag_relative(x_offset: int, y_offset: int, duration: float = 0.5, 
                      button: str = 'left'):
        """
        相对拖拽
        
        Args:
            x_offset: X方向偏移量
            y_offset: Y方向偏移量
            duration: 拖拽持续时间
            button: 使用的鼠标按键
        """
        pyautogui.dragRel(x_offset, y_offset, duration=duration, button=button)
    
    @staticmethod
    def scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None):
        """
        滚动鼠标滚轮
        
        Args:
            clicks: 滚动量（正数向上，负数向下）
            x: 滚动位置X坐标
            y: 滚动位置Y坐标
        """
        pyautogui.scroll(clicks, x=x, y=y)
    
    @staticmethod
    def mouse_down(x: Optional[int] = None, y: Optional[int] = None, 
                   button: str = 'left'):
        """
        按下鼠标按键
        
        Args:
            x: 位置X坐标
            y: 位置Y坐标
            button: 鼠标按键
        """
        pyautogui.mouseDown(x=x, y=y, button=button)
    
    @staticmethod
    def mouse_up(x: Optional[int] = None, y: Optional[int] = None, 
                 button: str = 'left'):
        """
        释放鼠标按键
        
        Args:
            x: 位置X坐标
            y: 位置Y坐标
            button: 鼠标按键
        """
        pyautogui.mouseUp(x=x, y=y, button=button)
