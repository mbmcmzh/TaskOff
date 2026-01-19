"""
关机控制模块
负责执行Windows关机命令
"""
import subprocess
import os
from typing import Optional


class ShutdownController:
    """Windows关机控制器"""
    
    @staticmethod
    def shutdown(delay: int = 0, force: bool = False, message: Optional[str] = None) -> bool:
        """
        执行关机命令
        
        Args:
            delay: 延迟秒数（Windows shutdown命令的/t参数）
            force: 是否强制关闭应用程序
            message: 关机提示消息
            
        Returns:
            是否成功执行命令
        """
        try:
            cmd = ["shutdown", "/s", f"/t", str(delay)]
            
            if force:
                cmd.append("/f")
            
            if message:
                cmd.extend(["/c", message])
            
            # 使用CREATE_NO_WINDOW避免弹出命令行窗口
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run(cmd, startupinfo=startupinfo, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"关机命令执行失败: {e}")
            return False
        except Exception as e:
            print(f"关机时发生错误: {e}")
            return False
    
    @staticmethod
    def restart(delay: int = 0, force: bool = False, message: Optional[str] = None) -> bool:
        """
        执行重启命令
        
        Args:
            delay: 延迟秒数
            force: 是否强制关闭应用程序
            message: 重启提示消息
            
        Returns:
            是否成功执行命令
        """
        try:
            cmd = ["shutdown", "/r", f"/t", str(delay)]
            
            if force:
                cmd.append("/f")
            
            if message:
                cmd.extend(["/c", message])
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run(cmd, startupinfo=startupinfo, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"重启命令执行失败: {e}")
            return False
        except Exception as e:
            print(f"重启时发生错误: {e}")
            return False
    
    @staticmethod
    def cancel_shutdown() -> bool:
        """
        取消已计划的关机/重启
        
        Returns:
            是否成功取消
        """
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run(["shutdown", "/a"], startupinfo=startupinfo, check=True)
            return True
        except subprocess.CalledProcessError:
            # 可能没有计划的关机任务
            return False
        except Exception as e:
            print(f"取消关机时发生错误: {e}")
            return False
    
    @staticmethod
    def sleep() -> bool:
        """
        使计算机进入睡眠状态
        
        Returns:
            是否成功执行
        """
        try:
            # 使用rundll32调用睡眠功能
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run(
                ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"],
                startupinfo=startupinfo,
                check=True
            )
            return True
        except Exception as e:
            print(f"睡眠时发生错误: {e}")
            return False
    
    @staticmethod
    def hibernate() -> bool:
        """
        使计算机进入休眠状态
        
        Returns:
            是否成功执行
        """
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run(["shutdown", "/h"], startupinfo=startupinfo, check=True)
            return True
        except Exception as e:
            print(f"休眠时发生错误: {e}")
            return False
    
    @staticmethod
    def logoff() -> bool:
        """
        注销当前用户
        
        Returns:
            是否成功执行
        """
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            subprocess.run(["shutdown", "/l"], startupinfo=startupinfo, check=True)
            return True
        except Exception as e:
            print(f"注销时发生错误: {e}")
            return False
