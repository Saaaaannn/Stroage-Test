import string

# Windows API常量
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3

# 测试配置
TEST_DIR_NAME = "USBTestData"
REPORT_FILE = "usb_test_report.json"
SMALL_FILE_SIZE = 1024  # 1KB
MEDIUM_FILE_SIZE = 1024 * 1024  # 1MB
LARGE_FILE_SIZE = 10 * 1024 * 1024  # 10MB
STRESS_TEST_DURATION = 30  # 秒
STABILITY_TEST_DURATION = 60  # 1分钟

# 字母表用于驱动器检测
DRIVE_LETTERS = string.ascii_uppercase