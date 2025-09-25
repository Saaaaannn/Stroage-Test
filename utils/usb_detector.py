import ctypes
from pathlib import Path
import shutil
from constants import DRIVE_REMOVABLE, DRIVE_FIXED, DRIVE_LETTERS

class USBDetector:
    def __init__(self):
        pass

    def get_drive_type(self, drive_letter):
        """获取驱动器类型"""
        kernel32 = ctypes.windll.kernel32
        drive_path = f"{drive_letter}:\\"
        return kernel32.GetDriveTypeW(drive_path)

    def find_usb_drives(self):
        """查找所有U盘"""
        usb_drives = []
        for letter in DRIVE_LETTERS:
            drive = f"{letter}:"
            drive_path = Path(f"{drive}\\")

            if not drive_path.exists():
                continue

            drive_type = self.get_drive_type(letter)
            if drive_type == DRIVE_REMOVABLE and letter != 'C':
                try:
                    usage = shutil.disk_usage(str(drive_path))
                    free_gb = usage.free / (1024 ** 3)
                    total_gb = usage.total / (1024 ** 3)

                    usb_drives.append({
                        "drive": drive,
                        "path": str(drive_path),
                        "free_space_gb": round(free_gb, 2),
                        "total_space_gb": round(total_gb, 2)
                    })
                except Exception as e:
                    print(f"无法访问驱动器 {drive}: {e}")

        return usb_drives