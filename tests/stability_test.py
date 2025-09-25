import os
import time
from pathlib import Path
from utils.logger import Logger
from constants import TEST_DIR_NAME, STABILITY_TEST_DURATION

class StabilityTest:
    def __init__(self, usb_info, logger: Logger):
        self.usb_info = usb_info
        self.logger = logger
        self.test_dir = Path(usb_info["path"]) / TEST_DIR_NAME
        self.test_dir.mkdir(exist_ok=True)

    def run(self):
        self.logger.log_message(f"开始稳定性测试（持续 {STABILITY_TEST_DURATION} 秒）...")
        start_time = time.time()
        file_count = 0

        while time.time() - start_time < STABILITY_TEST_DURATION:
            try:
                filename = f"stability_{file_count:05d}.tmp"
                filepath = self.test_dir / filename

                # 循环写入-读取-删除
                with open(filepath, "wb") as f:
                    f.write(os.urandom(4096))

                with open(filepath, "rb") as f:
                    data = f.read()
                    if len(data) != 4096:
                        raise Exception("读取数据长度不匹配")

                filepath.unlink()
                file_count += 1

                if file_count % 100 == 0:
                    self.logger.log_message(f"已执行 {file_count} 次稳定操作", "DEBUG")

            except Exception as e:
                self.logger.log_message(f"稳定性测试出错: {e}", "ERROR")
                return False

        self.logger.log_message(f"✅ 稳定性测试完成，共执行 {file_count} 次操作")
        return True