"""
TaskOff - Windows定时关机自动化工具

功能:
- 设置倒计时关机
- 配置关机前自动化操作序列（鼠标点击、键盘输入等）
- 可视化UI界面管理
- 系统托盘支持
- 关机前警告提醒

使用方法:
    python main.py

打包为exe:
    pyinstaller --onefile --windowed --name TaskOff main.py
"""

import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(__file__))

from src.ui.main_window import main

if __name__ == "__main__":
    main()
