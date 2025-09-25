import wmi
c = wmi.WMI()
# for cpu in c.Win32_Processor():
#    print(f"CPU 型号: {cpu.Name}")
#    print(f"核心数: {cpu.NumberOfCores}")
#
# for disk in c.Win32_DiskDrive():
#    print(f"硬盘型号: {disk.Model}")
#    print(f"硬盘大小: {int(disk.Size) / 1024 / 1024 / 1024:.2f} GB")


def list_only_usb_flash_drives():
    c = wmi.WMI()
    # 获取所有物理磁盘
    disk_drives = c.Win32_DiskDrive()

    usb_drives = []

    for disk in disk_drives:
        # 关键判断：介质类型是否为“可移动” (Removable)
        if not (disk.MediaType and "removable" in disk.MediaType.lower()):
            continue  # 跳过非U盘设备

        # 可选：进一步确认是通过 USB 接口连接
        if not (disk.InterfaceType and disk.InterfaceType.lower() == "usb"):
            continue  # 确保是 USB 接口（更精准）

        # 获取型号（Model）
        model = disk.Model.strip() if disk.Model else "Unknown"

        # 获取容量（Size 是字符串，单位是字节）
        size_gb = 0
        if disk.Size:
            try:
                size_gb = int(disk.Size) / (1024 ** 3)  # 转换为 GB
            except:
                size_gb = 0

        # 添加到结果
        usb_drives.append((model, size_gb))

    # 输出结果
    if usb_drives:
        for model, size_gb in usb_drives:
            print(f"U盘型号: {model}")
            print(f"U盘容量: {size_gb:.2f} GB")
            print("-" * 40)
    else:
        print("未检测到U盘设备。")

# 调用函数
list_only_usb_flash_drives()

import wmi


def list_usb_flash_drives_with_status():
    c = wmi.WMI()
    disk_drives = c.Win32_DiskDrive()

    usb_drives = []

    for disk in disk_drives:
        # 判断是否为可移动介质（U盘）
        if not (disk.MediaType and "removable" in disk.MediaType.lower()):
            continue

        # 确保是通过 USB 接口连接（更精准）
        if not (disk.InterfaceType and disk.InterfaceType.lower() == "usb"):
            continue

        # 获取基本信息
        model = disk.Model.strip() if disk.Model else "Unknown"

        # 获取容量（GB）
        size_gb = 0
        if disk.Size:
            try:
                size_gb = int(disk.Size) / (1024 ** 3)  # 转为 GB
            except (ValueError, TypeError):
                size_gb = 0

        # 🔹 获取当前状态（来自 Win32_DiskDrive 的 Status 属性）
        status = disk.Status if disk.Status else "Unknown"

        usb_drives.append((model, size_gb, status))

    # 输出结果
    if usb_drives:
        for model, size_gb, status in usb_drives:
            print(f"U盘型号: {model}")
            print(f"U盘容量: {size_gb:.2f} GB")
            print(f"当前状态: {status}")
            print("-" * 40)
    else:
        print("未检测到U盘设备。")


# 调用函数
list_usb_flash_drives_with_status()