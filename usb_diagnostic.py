#!/usr/bin/env python3
"""
U盘诊断工具 - 检查U盘写入问题
"""

import os
import sys
import ctypes
import string
import shutil
import subprocess
from pathlib import Path

def check_removable_drives():
    """检查所有可移动驱动器"""
    print("=" * 50)
    print("检测可移动驱动器...")
    print("=" * 50)
    
    removable_drives = []
    
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
        
        if drive_type == 2:  # DRIVE_REMOVABLE
            try:
                if os.path.exists(drive_path):
                    usage = shutil.disk_usage(drive_path)
                    free_gb = usage.free / (1024**3)
                    total_gb = usage.total / (1024**3)
                    
                    print(f"找到可移动驱动器: {letter}:")
                    print(f"  路径: {drive_path}")
                    print(f"  总容量: {total_gb:.2f}GB")
                    print(f"  可用空间: {free_gb:.2f}GB")
                    print(f"  使用率: {((total_gb - free_gb) / total_gb * 100):.1f}%")
                    
                    # 检查文件系统
                    try:
                        result = subprocess.run(['fsutil', 'fsinfo', 'volumeinfo', f'{letter}:'], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            for line in result.stdout.split('\n'):
                                if 'File System' in line or '文件系统' in line:
                                    print(f"  文件系统: {line.strip()}")
                        else:
                            print(f"  文件系统: 无法检测")
                    except:
                        print(f"  文件系统: 检测失败")
                    
                    print("-" * 30)
                    
                    removable_drives.append({
                        'letter': letter,
                        'path': drive_path,
                        'free_gb': free_gb,
                        'total_gb': total_gb
                    })
                    
            except Exception as e:
                print(f"检查 {letter}: 时出错: {e}")
    
    return removable_drives

def test_write_capability(drive_path):
    """测试写入能力"""
    print(f"\n测试驱动器 {drive_path} 的写入能力...")
    
    test_file = Path(drive_path) / "write_test.tmp"
    
    try:
        # 测试小文件写入
        print("1. 测试小文件写入 (1KB)...")
        with open(test_file, "wb") as f:
            f.write(b"X" * 1024)
            f.flush()
            os.fsync(f.fileno())
        print("   ✅ 小文件写入成功")
        
        # 测试中等文件写入 
        print("2. 测试中等文件写入 (10MB)...")
        with open(test_file, "wb") as f:
            for i in range(10):
                f.write(b"X" * 1024 * 1024)  # 1MB chunks
                f.flush()
            os.fsync(f.fileno())
        print("   ✅ 中等文件写入成功")
        
        # 测试大文件写入（接近4GB）
        print("3. 测试大文件写入 (100MB)...")
        with open(test_file, "wb") as f:
            for i in range(100):
                f.write(b"X" * 1024 * 1024)  # 1MB chunks
                f.flush()
                if i % 20 == 0:
                    print(f"   写入进度: {i+1}/100 MB")
            os.fsync(f.fileno())
        print("   ✅ 大文件写入成功")
        
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
            print("   ✅ 测试文件清理成功")
            
        return True
        
    except PermissionError as e:
        print(f"   ❌ 权限错误: {e}")
        return False
    except OSError as e:
        if "No space left" in str(e):
            print(f"   ❌ 磁盘空间不足: {e}")
        elif "file too large" in str(e).lower():
            print(f"   ❌ 文件过大(FAT32限制): {e}")
        else:
            print(f"   ❌ 系统错误: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 其他错误: {e}")
        return False
    finally:
        try:
            if test_file.exists():
                test_file.unlink()
        except:
            pass

def main():
    print("U盘诊断工具")
    print("=" * 50)
    
    # 检查管理员权限
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"管理员权限: {'是' if is_admin else '否'}")
    except:
        print("管理员权限: 检测失败")
    
    # 检测可移动驱动器
    drives = check_removable_drives()
    
    if not drives:
        print("❌ 未检测到任何可移动驱动器")
        return
    
    print(f"✅ 检测到 {len(drives)} 个可移动驱动器")
    
    # 对每个驱动器进行写入测试
    for drive in drives:
        print(f"\n{'='*50}")
        print(f"测试驱动器 {drive['letter']}:")
        success = test_write_capability(drive['path'])
        
        if success:
            print(f"✅ 驱动器 {drive['letter']}: 写入测试通过")
        else:
            print(f"❌ 驱动器 {drive['letter']}: 写入测试失败")

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")