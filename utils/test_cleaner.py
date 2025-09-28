# utils/test_cleaner.py
"""
全局测试文件清理工具
确保彻底清理U盘中的所有测试文件和目录
"""

import shutil
from pathlib import Path
from constants import TEST_DIR_NAME


class TestCleaner:
    """全局测试清理器，用于彻底清理所有测试遗留文件"""
    
    def __init__(self, usb_info, logger=None):
        self.usb_info = usb_info
        self.logger = logger
        self.usb_test_dir = Path(usb_info["path"]) / TEST_DIR_NAME
    
    def log_message(self, message, level="INFO"):
        """安全日志记录"""
        if self.logger:
            self.logger.log_message(message, level)
        else:
            print(f"[{level}] {message}")
    
    def cleanup_all_test_files(self):
        """彻底清理U盘中的所有测试文件和目录"""
        self.log_message("🧹 开始全局测试文件清理...")
        
        try:
            if not self.usb_test_dir.exists():
                self.log_message("✅ U盘测试目录不存在，无需清理")
                return True
            
            self.log_message(f"正在清理目录: {self.usb_test_dir}")
            
            # 方法1: 递归删除所有文件和子目录
            success = self._deep_cleanup()
            
            if success:
                # 方法2: 如果方法1成功，尝试删除主目录
                try:
                    if self.usb_test_dir.exists():
                        if not any(self.usb_test_dir.iterdir()):
                            self.usb_test_dir.rmdir()
                            self.log_message(f"✅ 已彻底删除测试目录: {TEST_DIR_NAME}")
                        else:
                            self.log_message(f"⚠️ 测试目录仍有文件残留: {list(self.usb_test_dir.iterdir())}", "WARNING")
                            return False
                except Exception as e:
                    self.log_message(f"❌ 删除测试目录失败: {e}", "ERROR")
                    return False
            
            return success
            
        except Exception as e:
            self.log_message(f"❌ 全局清理过程出错: {e}", "ERROR")
            return False
    
    def _deep_cleanup(self):
        """深度递归清理"""
        success = True
        
        try:
            # 获取所有子项目，按深度排序（深的在前）
            all_items = list(self.usb_test_dir.rglob("*"))
            all_items.sort(key=lambda x: len(str(x)), reverse=True)
            
            for item in all_items:
                try:
                    if item.is_file():
                        item.unlink()
                        self.log_message(f"✅ 已删除文件: {item.name}")
                    elif item.is_dir() and item != self.usb_test_dir:
                        # 确保目录为空后再删除
                        if not any(item.iterdir()):
                            item.rmdir()
                            self.log_message(f"✅ 已删除空目录: {item.name}")
                        else:
                            self.log_message(f"⚠️ 目录非空，跳过: {item.name}", "WARNING")
                            success = False
                except Exception as e:
                    self.log_message(f"❌ 删除项目失败 {item.name}: {e}", "ERROR")
                    success = False
            
            return success
            
        except Exception as e:
            self.log_message(f"❌ 深度清理失败: {e}", "ERROR")
            return False
    
    def force_cleanup_with_shutil(self):
        """使用shutil强制删除整个目录（备用方案）"""
        try:
            if self.usb_test_dir.exists():
                self.log_message("🔥 使用强制删除模式...")
                shutil.rmtree(str(self.usb_test_dir))
                self.log_message(f"✅ 强制删除成功: {TEST_DIR_NAME}")
                return True
            return True
        except Exception as e:
            self.log_message(f"❌ 强制删除失败: {e}", "ERROR")
            return False
    
    def cleanup_local_temp_files(self):
        """清理本地E盘临时文件"""
        try:
            local_temp_dir = Path("E:/temp_usb_test")
            if local_temp_dir.exists():
                self.log_message("正在清理本地临时文件...")
                
                # 清理所有文件
                for item in local_temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                        self.log_message(f"✅ 已删除本地文件: {item.name}")
                
                # 如果目录为空，删除目录
                if not any(local_temp_dir.iterdir()):
                    local_temp_dir.rmdir()
                    self.log_message("✅ 已删除本地临时目录")
                
                return True
        except Exception as e:
            self.log_message(f"❌ 清理本地临时文件失败: {e}", "ERROR")
            return False
    
    def complete_cleanup(self):
        """完整的清理流程"""
        self.log_message("🧽 开始完整清理流程...")
        
        # 1. 标准清理
        standard_success = self.cleanup_all_test_files()
        
        # 2. 如果标准清理失败，尝试强制清理
        if not standard_success:
            self.log_message("标准清理失败，尝试强制清理...")
            force_success = self.force_cleanup_with_shutil()
            if not force_success:
                self.log_message("❌ 所有清理方法都失败了", "ERROR")
                return False
        
        # 3. 清理本地临时文件
        self.cleanup_local_temp_files()
        
        self.log_message("🎉 完整清理流程完成")
        return True