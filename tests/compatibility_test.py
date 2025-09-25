import os
import hashlib
from pathlib import Path
from utils.logger import Logger
from constants import TEST_DIR_NAME, SMALL_FILE_SIZE, MEDIUM_FILE_SIZE, LARGE_FILE_SIZE

class CompatibilityTest:
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
        self.logger.log_message("开始数据兼容性测试...")
        test_files = {
            "small.txt": SMALL_FILE_SIZE,
            "medium.bin": MEDIUM_FILE_SIZE,
            "large.dat": LARGE_FILE_SIZE
        }

        hashes = {}
        for filename, size in test_files.items():
            filepath = self.generate_test_file(filename, size)
            hashes[filename] = self.calculate_file_hash(filepath)
            self.logger.log_message(f"创建测试文件: {filename} ({size} bytes)")

        for filename, original_hash in hashes.items():
            filepath = self.test_dir / filename
            if filepath.exists():
                current_hash = self.calculate_file_hash(filepath)
                if current_hash == original_hash:
                    self.logger.log_message(f"文件 {filename} 完整性验证通过")
                else:
                    self.logger.log_message(f"文件 {filename} 完整性验证失败", "ERROR")
                    return False
            else:
                self.logger.log_message(f"文件 {filename} 丢失", "ERROR")
                return False

        self.logger.log_message("✅ 数据兼容性测试完成")
        return True