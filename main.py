# main.py - U盘自动化测试系统主入口
import tkinter as tk
from tkinter import messagebox
import ctypes
import os
import sys

# 导入页面模块
from pages.device_selection import DeviceSelectionPage
from pages.test_setup import TestSetupPage


# ================== 权限检查：确保以管理员身份运行 ==================
def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """若非管理员，则重新启动程序并请求提权"""
    if is_admin():
        return True
    script = os.path.abspath(sys.argv[0])
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, script, os.getcwd(), 1
        )
        if int(ret) > 32:
            print("✅ 已发送管理员权限请求")
            sys.exit(0)
        else:
            messagebox.showerror("错误", "无法请求管理员权限，请手动右键以管理员身份运行。")
            sys.exit(1)
    except Exception as e:
        messagebox.showerror("提权失败", f"请求管理员权限时出错：\n{str(e)}")
        sys.exit(1)


if not is_admin():
    run_as_admin()
    sys.exit()


# ================== 主应用控制器 ==================
class USBTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("U盘自动化测试系统")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # 存储选中的U盘信息
        self.selected_usb = None  # 格式: {"drive": "D:", "path": "D:\\", "total_space_gb": xx, ...}

        # 主容器
        self.container = tk.Frame(root)
        self.container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # 页面字典
        self.pages = {}

        # 创建所有页面
        self.create_pages()

        # 默认显示设备选择页
        self.show_page("DeviceSelectionPage")

    def create_pages(self):
        """动态导入并创建所有页面"""
        page_classes = {
            "DeviceSelectionPage": DeviceSelectionPage,
            "TestSetupPage": TestSetupPage,
        }

        for page_name, PageClass in page_classes.items():
            try:
                page = PageClass(parent=self.container, controller=self)
                self.pages[page_name] = page
                page.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            except Exception as e:
                messagebox.showerror("初始化失败", f"无法创建页面 {page_name}: {str(e)}")
                self.root.destroy()
                return

    def show_page(self, page_name):
        """切换到指定页面"""
        if page_name not in self.pages:
            messagebox.showerror("页面错误", f"未找到页面：{page_name}")
            return

        # 隐藏所有页面
        for page in self.pages.values():
            page.grid_remove()

        # 显示目标页面
        self.pages[page_name].grid()

        # 如果页面有 on_show 方法，则调用（用于刷新数据）
        if hasattr(self.pages[page_name], "on_show"):
            self.pages[page_name].on_show()

    def set_selected_usb(self, usb_info):
        """从设备选择页传入选中的U盘信息"""
        self.selected_usb = usb_info
        print(f"【主控制器】已设置选中设备: {usb_info.get('drive')} ({usb_info.get('model', 'Unknown')})")

    def get_selected_usb(self):
        """供其他页面获取当前选中的U盘"""
        return self.selected_usb


# ================== 程序启动 ==================
if __name__ == "__main__":
    root = tk.Tk()
    app = USBTestApp(root)
    root.mainloop()