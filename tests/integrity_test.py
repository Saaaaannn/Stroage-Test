import os
import hashlib
from pathlib import Path
from utils.logger import Logger
from constants import TEST_DIR_NAME

class IntegrityTest:
    def __init__(self, usb_info, logger: Logger):
        self.usb_info = usb_info
        self.logger = logger
        self.test_dir = Path(usb_info["path"]) / TEST_DIR_NAME
        self.test_dir.mkdir(exist_ok=True)

    def generate_test_file(self, filename, size):
        filepath = self.test_dir / filename
        with open(filepath, "wb") as f:
            f.write(os.urandom(size))
        return filepath

    def calculate_file_hash(self, filepath):
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def run(self):
        self.logger.log_message("开始数据完整性测试...")
        small_files = []
        hashes = {}

        # 创建50个1KB文件
        for i in range(50):
            filename = f"integrity_test_{i:03d}.txt"
            filepath = self.generate_test_file(filename, 1024)
            small_files.append(filepath)
            hashes[str(filepath)] = self.calculate_file_hash(filepath)

        # 验证所有文件
        all_passed = True
        for filepath_str in hashes:
            filepath = Path(filepath_str)
            if filepath.exists():
                current_hash = self.calculate_file_hash(filepath)
                if current_hash != hashes[filepath_str]:
                    self.logger.log_message(f"文件 {filepath.name} 完整性验证失败", "ERROR")
                    all_passed = False
            else:
                self.logger.log_message(f"文件 {filepath.name} 丢失", "ERROR")
                all_passed = False

        if all_passed:
            self.logger.log_message("✅ 数据完整性测试通过")
        else:
            self.logger.log_message("❌ 数据完整性测试失败", "ERROR")

        # 清理测试文件
        self._cleanup_test_files()

        return all_passed

    def _cleanup_test_files(self):
        """清理完整性测试生成的所有文件"""
        try:
            if self.test_dir.exists():
                # 清理所有测试文件
                for test_file in self.test_dir.glob("integrity_test_*.txt"):
                    if test_file.is_file():
                        test_file.unlink()
                        self.logger.log_message(f"✅ 已清理完整性测试文件: {test_file.name}")
                
                # 清理其他可能的临时文件
                for temp_file in self.test_dir.glob("*.tmp"):
                    if temp_file.is_file():
                        temp_file.unlink()
                        
                # 如果目录为空，删除目录
                if not any(self.test_dir.iterdir()):
                    self.test_dir.rmdir()
                    self.logger.log_message(f"✅ 已清理测试目录: {self.test_dir.name}")
        except Exception as e:
            self.logger.log_message(f"⚠️ 清理完整性测试文件时出错: {e}", "WARNING")