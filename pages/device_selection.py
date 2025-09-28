import tkinter as tk
from tkinter import ttk, messagebox
import wmi  # 用于获取U盘硬件信息
import ctypes
import string


class DeviceSelectionPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_device = None  # 存储选中的U盘信息
        self.usb_drives = []        # 存储所有检测到的U盘

        self.setup_ui()
        self.refresh_devices()

    def setup_ui(self):
        """构建UI界面"""
        # 标题
        title_label = tk.Label(
            self,
            text="U盘自动化测试系统",
            font=("微软雅黑", 16, "bold")
        )
        title_label.pack(pady=15)

        subtitle_label = tk.Label(
            self,
            text="请选择要测试的U盘设备",
            font=("微软雅黑", 10)
        )
        subtitle_label.pack(pady=5)

        # 设备列表框架
        frame = ttk.Frame(self)
        frame.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)

        # 表格：显示U盘型号、容量、状态
        self.tree = ttk.Treeview(
            frame,
            columns=("Model", "Size", "Status"),
            show="headings",
            height=10
        )
        self.tree.heading("Model", text="U盘型号")
        self.tree.heading("Size", text="容量 (GB)")
        self.tree.heading("Status", text="状态")

        self.tree.column("Model", width=300, anchor="w")
        self.tree.column("Size", width=120, anchor="center")
        self.tree.column("Status", width=120, anchor="center")

        # 滚动条
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # 按钮区域
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)

        self.refresh_btn = ttk.Button(btn_frame, text="刷新设备", command=self.refresh_devices)
        self.refresh_btn.grid(row=0, column=0, padx=10)

        self.start_btn = ttk.Button(btn_frame, text="开始测试", state="disabled", command=self.start_test)
        self.start_btn.grid(row=0, column=1, padx=10)

        self.exit_btn = ttk.Button(btn_frame, text="退出", command=self.exit_application)
        self.exit_btn.grid(row=0, column=2, padx=10)

    def get_usb_drives(self):
        """使用WMI扫描所有U盘设备"""
        try:
            c = wmi.WMI()
            disk_drives = c.Win32_DiskDrive()
            usb_drives = []

            for disk in disk_drives:
                # 判断是否为USB可移动磁盘
                if (disk.MediaType and "removable" in disk.MediaType.lower()) and \
                   (disk.InterfaceType and disk.InterfaceType.lower() == "usb"):

                    model = disk.Model.strip() if disk.Model else "Unknown"
                    size_gb = 0
                    if disk.Size:
                        try:
                            size_gb = int(disk.Size) / (1024 ** 3)
                        except (ValueError, TypeError):
                            size_gb = 0

                    status = disk.Status if disk.Status else "Unknown"

                    usb_drives.append({
                        "model": model,
                        "size_gb": round(size_gb, 2),
                        "status": status,
                        "device_id": disk.DeviceID  # 用于后续关联盘符（可选）
                    })

            return usb_drives
        except Exception as e:
            messagebox.showerror("扫描错误", f"无法访问WMI服务：\n{str(e)}")
            return []

    def refresh_devices(self):
        """刷新设备列表"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 重新扫描
        self.usb_drives = self.get_usb_drives()

        if self.usb_drives:
            for drive in self.usb_drives:
                self.tree.insert("", "end", values=(
                    drive["model"],
                    f"{drive['size_gb']:.2f}",
                    drive["status"]
                ))
        else:
            self.tree.insert("", "end", values=("未检测到U盘设备", "", ""))
            self.start_btn.config(state="disabled")

    def get_actual_usb_drive(self):
        """获取真实U盘盘符和路径"""
        try:
            print("正在扫描可移动设备...")
            found_drives = []
            
            # 获取所有可移动磁盘
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                
                # 检查是否为可移动设备（类型2）
                if drive_type == 2:  # DRIVE_REMOVABLE
                    try:
                        # 检查磁盘是否可访问
                        import os
                        if os.path.exists(drive_path):
                            # 获取磁盘信息
                            import shutil
                            usage = shutil.disk_usage(drive_path)
                            free_gb = usage.free / (1024**3)
                            total_gb = usage.total / (1024**3)
                            
                            drive_info = {
                                "drive": f"{letter}:",
                                "path": drive_path,
                                "free_gb": free_gb,
                                "total_gb": total_gb
                            }
                            found_drives.append(drive_info)
                            # 移除个人设备信息框，静默收集信息
                    except Exception as e:
                        print(f"检查磁盘 {letter}: 时出错: {e}")
                        continue
            
            if not found_drives:
                messagebox.showerror("错误", "未检测到任何可移动设备（U盘）")
                return None
            
            # 如果有多个可移动设备，选择第一个（静默处理）
            selected_drive = found_drives[0]
            # 静默返回，不显示额外信息框
            
            return selected_drive
            
        except Exception as e:
            messagebox.showerror("错误", f"获取U盘路径失败: {e}")
            return None

    def on_select(self, event):
        """处理设备选择事件"""
        selected_items = self.tree.selection()
        if selected_items:
            index = self.tree.index(selected_items[0])
            self.selected_device = self.usb_drives[index]
            self.start_btn.config(state="normal")

    def start_test(self):
        """点击"开始测试"按钮"""
        if not self.selected_device:
            messagebox.showwarning("提示", "请先选择一个U盘设备！")
            return

        # ✅ 获取真实U盘盘符和路径
        usb_drive_info = self.get_actual_usb_drive()
        if not usb_drive_info:
            messagebox.showerror("错误", "无法获取U盘真实路径，请检查U盘是否正常连接。")
            return
        
        # 将设备信息传递给主控制器（controller）
        usb_info = {
            "model": self.selected_device["model"],
            "size_gb": self.selected_device["size_gb"],
            "status": self.selected_device["status"],
            "drive": usb_drive_info["drive"],  # 真实盘符
            "path": usb_drive_info["path"],    # 真实路径
            "label": self.selected_device["model"]  # 可用作名称显示
        }

        # 显示统一的确认信息并提供选项
        device_info = (
            f"U盘设备信息：\n"
            f"型号：{self.selected_device['model']}\n"
            f"容量：{self.selected_device['size_gb']:.2f}GB\n"
            f"盘符：{usb_drive_info['drive']}\n"
            f"路径：{usb_drive_info['path']}\n"
            f"可用空间：{usb_drive_info['free_gb']:.2f}GB\n\n"
            f"是否开始测试？"
        )
        
        # 使用askyesno提供“是”和“否”选项
        result = messagebox.askyesno(
            "确认开始测试", 
            device_info
        )
        
        if result:  # 用户点击“是”
            self.controller.set_selected_usb(usb_info)
            self.controller.show_page("TestSetupPage")
        # 如果用户点击“否”，则什么也不做，留在当前页面

    def exit_application(self):
        """安全退出应用程序"""
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
