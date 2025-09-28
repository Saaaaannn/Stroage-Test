# pages/test_setup.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Dict, Optional

# 导入测试模块
from tests.compatibility_test import CompatibilityTest
from tests.integrity_test import IntegrityTest
from tests.performance_test import PerformanceTest
from tests.stress_test import StressTest
from tests.stability_test import StabilityTest

# 导入日志工具
from utils.logger import Logger
from utils.test_cleaner import TestCleaner


class TestSetupPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger: Optional[Logger] = None
        self.device_label: Optional[ttk.Label] = None
        self.selected_tests: Dict[str, tk.BooleanVar] = {}  # 存储测试项选择状态
        self.is_testing: bool = False  # 防止重复启动

        self.create_widgets()

    def create_widgets(self):
        """创建页面控件"""
        # 主容器：左右 PanedWindow 布局
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 左侧：测试设置 ---
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)

        # 标题
        title_label = ttk.Label(left_frame, text="测试设置", font=("微软雅黑", 14, "bold"))
        title_label.pack(pady=10)

        # 设备信息标签
        self.device_label = ttk.Label(left_frame, text="正在加载设备信息...", foreground="blue")
        self.device_label.pack(pady=(0, 20))

        # 测试项目选择
        options_frame = ttk.LabelFrame(left_frame, text="选择测试项目")
        options_frame.pack(fill=tk.X, padx=10, pady=10)

        self.test_options = [
            "数据兼容性测试",
            "数据完整性测试",
            "性能测试",
            "压力测试",
            "稳定性测试"
        ]

        for option in self.test_options:
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(options_frame, text=option, variable=var)
            chk.pack(anchor=tk.W, padx=8, pady=2)
            self.selected_tests[option] = var

        # 按钮区域
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(pady=20)

        self.back_btn = ttk.Button(btn_frame, text="返回", command=self.back_to_device_selection)
        self.back_btn.pack(side=tk.LEFT, padx=5)

        self.start_btn = ttk.Button(btn_frame, text="开始测试", command=self.start_tests)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加退出按钮
        self.exit_btn = ttk.Button(btn_frame, text="退出", command=self.exit_application)
        self.exit_btn.pack(side=tk.LEFT, padx=5)

        # --- 右侧：日志显示 ---
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)

        log_title = ttk.Label(right_frame, text="实时测试日志", font=("微软雅黑", 10))
        log_title.pack(pady=(5, 0))

        # 日志文本框
        self.log_text = tk.Text(right_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # 初始化日志器（传入 Text 控件）
        self.logger = Logger(self.log_text)

    def safe_log(self, message: str, level: str = "INFO") -> None:
        """安全的日志记录方法，避免None类型警告"""
        if self.logger:
            self.logger.log_message(message, level)

    def on_show(self):
        """页面显示时更新设备信息"""
        if not self.device_label:
            return
            
        usb_info = self.controller.get_selected_usb()
        if usb_info:
            info_text = f"已选设备: {usb_info['model']} ({usb_info['size_gb']:.2f} GB)"
            self.device_label.config(text=info_text)
        else:
            self.device_label.config(text="⚠️ 未选择设备", foreground="red")

    def back_to_device_selection(self):
        """返回设备选择页"""
        if self.is_testing:
            if not messagebox.askyesno("确认", "测试正在进行，确定要返回吗？"):
                return
        self.controller.show_page("DeviceSelectionPage")

    def start_tests(self):
        """启动测试（在子线程中运行，避免阻塞 UI）"""
        if self.is_testing:
            messagebox.showwarning("提示", "测试已在进行中，请勿重复点击。")
            return

        usb_info = self.controller.get_selected_usb()
        if not usb_info:
            messagebox.showerror("错误", "未选择U盘设备！")
            return

        selected_names = [name for name, var in self.selected_tests.items() if var.get()]
        if not selected_names:
            messagebox.showwarning("警告", "请至少选择一个测试项目！")
            return

        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # 记录日志 - 添加空值检查
        if self.logger:
            self.logger.log_message(f"开始测试设备: {usb_info['model']}", "INFO")
            self.logger.log_message(f"测试项目: {', '.join(selected_names)}", "INFO")
            self.logger.log_message("-" * 50, "INFO")

        # 启动测试线程
        self.is_testing = True
        thread = threading.Thread(
            target=self.run_all_tests,
            args=(usb_info, selected_names),
            daemon=True  # 主线程退出时自动结束
        )
        thread.start()

    def run_all_tests(self, usb_info, selected_names):
        """在子线程中运行所有测试"""
        try:
            test_classes = {
                "数据兼容性测试": CompatibilityTest,
                "数据完整性测试": IntegrityTest,
                "性能测试": PerformanceTest,
                "压力测试": StressTest,
                "稳定性测试": StabilityTest,
            }

            all_passed = True
            for name in selected_names:
                cls = test_classes.get(name)
                if cls:
                    self.safe_log(f"--- 开始: {name} ---", "INFO")
                    try:
                        test = cls(usb_info, self.logger)
                        if test.run():
                            self.safe_log(f"✅ {name} 通过", "INFO")
                        else:
                            self.safe_log(f"❌ {name} 失败", "ERROR")
                            all_passed = False
                    except Exception as e:
                        self.safe_log(f"❌ {name} 执行异常: {e}", "ERROR")
                        all_passed = False

            final = "🎉 所有测试通过！" if all_passed else "⚠️ 部分测试失败"
            self.safe_log("-" * 50, "INFO")
            self.safe_log(f"测试完成: {final}", "INFO")
            
            # 执行全局清理
            self.safe_log("-" * 50, "INFO")
            self.safe_log("开始全局清理...", "INFO")
            try:
                cleaner = TestCleaner(usb_info, self.logger)
                cleanup_success = cleaner.complete_cleanup()
                if cleanup_success:
                    self.safe_log("🎉 全局清理完成！U盘已恢复清洁状态", "INFO")
                else:
                    self.safe_log("⚠️ 全局清理部分失败，请手动检查U盘", "WARNING")
            except Exception as e:
                self.safe_log(f"❌ 全局清理出错: {e}", "ERROR")

            # 弹窗必须在主线程执行
            self.log_text.after(0, lambda: messagebox.showinfo("测试结果", final))

        except Exception as e:
            error_msg = f"测试过程发生未知错误: {e}"
            self.safe_log(error_msg, "ERROR")
            self.log_text.after(0, lambda: messagebox.showerror("错误", error_msg))

        finally:
            self.is_testing = False

    def exit_application(self):
        """安全退出应用程序"""
        if self.is_testing:
            if not messagebox.askyesno("确认", "测试正在进行，确定要退出吗？"):
                return
        
        try:
            # 销毁窗口并退出程序
            self.controller.root.quit()
            self.controller.root.destroy()
        except Exception as e:
            print(f"退出时出错: {e}")
        finally:
            # 强制退出
            import sys
            sys.exit(0)