import wmi

def list_all_devices():
    c = wmi.WMI()
    devices = c.Win32_PnPEntity()
    for device in devices:
        print(f"设备名称: {device.Name}, 当前状态: {device.Status}")

# 调用函数，输出所有设备的名称及状态
list_all_devices()