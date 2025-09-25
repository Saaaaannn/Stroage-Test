# utils/logger.py
import tkinter as tk
import logging
from datetime import datetime


class Logger:
    """
    自定义日志记录器，用于在GUI中显示日志信息。
    """

    def __init__(self, text_widget=None):
        self.text_widget = text_widget

        # 配置日志格式
        self.formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)

        # 获取或创建logger
        self.logger = logging.getLogger(f"GUI_Logger_{id(self)}")
        self.logger.setLevel(logging.INFO)

        # 避免重复添加处理器
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            if self.text_widget:
                gui_handler = self.TextHandler(self.text_widget)
                gui_handler.setFormatter(self.formatter)
                self.logger.addHandler(gui_handler)

    class TextHandler(logging.Handler):
        """自定义日志处理器，将日志输出到tk.Text组件"""

        def __init__(self, text_widget):
            super().__init__()
            self.text_widget = text_widget

        def emit(self, record):
            msg = self.format(record)
            # 确保在主线程中更新GUI
            self.text_widget.after(0, self.append_message, msg)

        def append_message(self, msg):
            try:
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, msg + '\n')
                self.text_widget.see(tk.END)  # 自动滚动到底部
                self.text_widget.config(state=tk.DISABLED)
            except tk.TclError:
                pass  # 避免窗口关闭后报错

    def log_message(self, message, level="INFO"):
        """
        记录日志消息。

        Args:
            message (str): 日志消息内容。
            level (str): 日志级别 ("INFO", "WARNING", "ERROR")。
        """
        level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(level, message)