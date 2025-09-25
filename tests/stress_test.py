import os
import time
import threading
from pathlib import Path
from utils.logger import Logger
from constants import TEST_DIR_NAME, STRESS_TEST_DURATION

class StressTest:
    def __init__(self, usb_info, logger: Logger):
        self.usb_info = usb_info
        self.logger = logger
        self.test_dir = Path(usb_info["path"]) / TEST_DIR_NAME
        self.test_dir.mkdir(exist_ok=True)
        self.is_running = False

    def stress_worker(self, worker_id):
        file_count = 0
        while self.is_running:
            try:
                filename = f"stress_{worker_id}_{file_count:04d}.tmp"
                filepath = self.test_dir / filename

                # 写入
                with open(filepath, "wb") as f:
                    f.write(os.urandom(1024))

                # 读取
                with open(filepath, "rb") as f:
                    f.read()

                # 删除
                filepath.unlink()
                file_count += 1

            except Exception as e:
                self.logger.log_message(f"压力测试线程 {worker_id} 出错: {e}", "ERROR")
                break

    def run(self):
        self.logger.log_message(f"开始压力测试（持续 {STRESS_TEST_DURATION} 秒）...")
        self.is_running = True

        threads = []
        for i in range(3):  # 3个并发线程
            t = threading.Thread(target=self.stress_worker, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(STRESS_TEST_DURATION)
        self.is_running = False

        for t in threads:
            t.join(timeout=1)

        self.logger.log_message("✅ 压力测试完成")
        return True