"""
定时调度器模块
负责管理倒计时和触发关机前的自动化操作
"""
import threading
from typing import Callable, Optional
from datetime import datetime, timedelta


class ShutdownScheduler:
    """定时关机调度器"""
    
    def __init__(self):
        self._timer: Optional[threading.Timer] = None
        self._countdown_timer: Optional[threading.Timer] = None
        self._remaining_seconds: int = 0
        self._is_running: bool = False
        self._on_tick_callback: Optional[Callable[[int], None]] = None
        self._on_complete_callback: Optional[Callable[[], None]] = None
        self._on_warning_callback: Optional[Callable[[int], None]] = None
        self._warning_seconds: int = 30  # 最后30秒提醒
        self._lock = threading.Lock()
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    @property
    def remaining_seconds(self) -> int:
        """剩余秒数"""
        return self._remaining_seconds
    
    def set_on_tick(self, callback: Callable[[int], None]):
        """设置每秒回调，参数为剩余秒数"""
        self._on_tick_callback = callback
    
    def set_on_complete(self, callback: Callable[[], None]):
        """设置完成回调"""
        self._on_complete_callback = callback
    
    def set_on_warning(self, callback: Callable[[int], None]):
        """设置警告回调，进入最后N秒时触发"""
        self._on_warning_callback = callback
    
    def set_warning_seconds(self, seconds: int):
        """设置提前警告秒数"""
        self._warning_seconds = seconds
    
    def start(self, seconds: int):
        """
        启动倒计时
        
        Args:
            seconds: 倒计时秒数
        """
        if self._is_running:
            self.cancel()
        
        with self._lock:
            self._remaining_seconds = seconds
            self._is_running = True
        
        self._start_countdown_tick()
    
    def _start_countdown_tick(self):
        """启动倒计时计时器"""
        if not self._is_running:
            return
        
        # 先在锁内获取状态和更新剩余时间
        on_complete = None
        on_tick = None
        on_warning = None
        remaining = 0
        warning_seconds = 0
        should_complete = False
        
        with self._lock:
            if self._remaining_seconds <= 0:
                self._is_running = False
                on_complete = self._on_complete_callback
                should_complete = True
            else:
                remaining = self._remaining_seconds
                on_tick = self._on_tick_callback
                on_warning = self._on_warning_callback
                warning_seconds = self._warning_seconds
                self._remaining_seconds -= 1
        
        # 在锁外执行回调，避免死锁
        if should_complete:
            if on_complete:
                try:
                    on_complete()
                except Exception as e:
                    print(f"on_complete callback error: {e}")
            return
        
        # 触发每秒回调
        if on_tick:
            try:
                on_tick(remaining)
            except Exception as e:
                print(f"on_tick callback error: {e}")
        
        # 检查是否进入警告时间
        if remaining == warning_seconds and on_warning:
            try:
                on_warning(remaining)
            except Exception as e:
                print(f"on_warning callback error: {e}")
        
        # 设置下一秒的定时器
        if self._is_running:
            self._countdown_timer = threading.Timer(1.0, self._start_countdown_tick)
            self._countdown_timer.daemon = True
            self._countdown_timer.start()
    
    def cancel(self):
        """取消倒计时"""
        with self._lock:
            self._is_running = False
            self._remaining_seconds = 0
            
            if self._countdown_timer:
                self._countdown_timer.cancel()
                self._countdown_timer = None
            
            if self._timer:
                self._timer.cancel()
                self._timer = None
    
    def pause(self):
        """暂停倒计时（保留剩余时间）"""
        if self._countdown_timer:
            self._countdown_timer.cancel()
            self._countdown_timer = None
        self._is_running = False
    
    def resume(self):
        """恢复倒计时"""
        if self._remaining_seconds > 0 and not self._is_running:
            self._is_running = True
            self._start_countdown_tick()
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """
        格式化时间显示
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间字符串 HH:MM:SS
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def calculate_seconds(hours: int = 0, minutes: int = 0, seconds: int = 0) -> int:
        """
        计算总秒数
        
        Args:
            hours: 小时
            minutes: 分钟
            seconds: 秒
            
        Returns:
            总秒数
        """
        return hours * 3600 + minutes * 60 + seconds
