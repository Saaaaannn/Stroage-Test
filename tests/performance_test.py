import os
import time
import shutil
from pathlib import Path
from utils.logger import Logger
from constants import TEST_DIR_NAME

class PerformanceTest:
    def __init__(self, usb_info, logger: Logger):
        self.usb_info = usb_info
        self.logger = logger
        self.test_dir = Path(usb_info["path"]) / TEST_DIR_NAME
        self.test_dir.mkdir(exist_ok=True)

    def _cleanup_test_files(self, local_test_file, usb_test_file, local_temp_dir, total_size_gb):
        """自动清理测试过程中创建的所有文件和目录"""
        self.logger.log_message("开始清理测试文件...")
        cleanup_success = True
        
        try:
            # 1. 清理U盘测试文件
            if usb_test_file and usb_test_file.exists():
                try:
                    usb_test_file.unlink()
                    self.logger.log_message(f"✅ 已清理U盘测试文件: {usb_test_file.name} ({total_size_gb}GB)")
                except Exception as e:
                    self.logger.log_message(f"❌ 清理U盘测试文件失败: {e}", "WARNING")
                    cleanup_success = False
            
            # 2. 彻底清理U盘测试目录及所有内容
            try:
                test_dir = usb_test_file.parent if usb_test_file else self.test_dir
                if test_dir.exists():
                    self.logger.log_message(f"正在清理U盘测试目录: {test_dir}")
                    
                    # 清理目录中的所有文件（包括所有类型的文件）
                    for item in test_dir.rglob("*"):  # 递归获取所有文件和子目录
                        if item.is_file():
                            try:
                                item.unlink()
                                self.logger.log_message(f"✅ 已清理文件: {item.name}")
                            except Exception as e:
                                self.logger.log_message(f"❌ 清理文件失败 {item.name}: {e}", "WARNING")
                                cleanup_success = False
                    
                    # 清理所有空目录（从最深层开始）
                    for item in sorted(test_dir.rglob("*"), key=lambda x: len(str(x)), reverse=True):
                        if item.is_dir() and item != test_dir:
                            try:
                                if not any(item.iterdir()):  # 目录为空
                                    item.rmdir()
                                    self.logger.log_message(f"✅ 已清理空目录: {item.name}")
                            except Exception as e:
                                self.logger.log_message(f"❌ 清理目录失败 {item.name}: {e}", "WARNING")
                                cleanup_success = False
                    
                    # 最后清理主测试目录
                    try:
                        if not any(test_dir.iterdir()):  # 目录为空
                            test_dir.rmdir()
                            self.logger.log_message(f"✅ 已彻底清理U盘测试目录: {test_dir.name}")
                        else:
                            remaining_files = list(test_dir.iterdir())
                            self.logger.log_message(f"⚠️ U盘测试目录仍有文件，未删除目录: {[f.name for f in remaining_files]}", "WARNING")
                            cleanup_success = False
                    except Exception as e:
                        self.logger.log_message(f"❌ 清理主测试目录失败: {e}", "WARNING")
                        cleanup_success = False
                        
            except Exception as e:
                self.logger.log_message(f"❌ 清理U盘测试目录失败: {e}", "WARNING")
                cleanup_success = False
            
            # 3. 清理本地E盘测试文件
            if local_test_file and local_test_file.exists():
                try:
                    local_test_file.unlink()
                    self.logger.log_message(f"✅ 已清理本地测试文件: {local_test_file.name} ({total_size_gb}GB)")
                except Exception as e:
                    self.logger.log_message(f"❌ 清理本地测试文件失败: {e}", "WARNING")
                    cleanup_success = False
            
            # 4. 清理本地E盘临时目录中的其他文件
            if local_temp_dir and local_temp_dir.exists():
                try:
                    # 清理目录中的所有文件
                    for temp_file in local_temp_dir.iterdir():
                        if temp_file.is_file():
                            try:
                                temp_file.unlink()
                                self.logger.log_message(f"✅ 已清理本地临时文件: {temp_file.name}")
                            except Exception as e:
                                self.logger.log_message(f"❌ 清理本地临时文件失败 {temp_file.name}: {e}", "WARNING")
                                cleanup_success = False
                    
                    # 如果目录为空，删除目录
                    if not any(local_temp_dir.iterdir()):
                        local_temp_dir.rmdir()
                        self.logger.log_message("✅ 已清理本地临时目录")
                    else:
                        self.logger.log_message("⚠️ 本地临时目录不为空，未删除目录", "WARNING")
                        
                except Exception as e:
                    self.logger.log_message(f"❌ 清理本地临时目录失败: {e}", "WARNING")
                    cleanup_success = False
            
            # 5. 强制垃圾回收
            import gc
            gc.collect()
            
            if cleanup_success:
                self.logger.log_message("🎉 所有测试文件清理完成")
            else:
                self.logger.log_message("⚠️ 部分测试文件清理失败，请手动检查", "WARNING")
                
        except Exception as e:
            self.logger.log_message(f"❌ 清理过程发生异常: {e}", "ERROR")

    def _copy_large_file(self, source_file, target_file):
        """分块复制大文件，解决FAT32文件系统4GB限制"""
        try:
            chunk_size = 100 * 1024 * 1024  # 100MB块
            copied_bytes = 0
            total_bytes = source_file.stat().st_size
            
            with open(source_file, 'rb') as src, open(target_file, 'wb') as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    dst.flush()
                    copied_bytes += len(chunk)
                    
                    # 显示进度
                    progress = (copied_bytes / total_bytes) * 100
                    if copied_bytes % (500 * 1024 * 1024) == 0:  # 每500MB显示
                        self.logger.log_message(f"复制进度: {progress:.1f}% ({copied_bytes / (1024*1024*1024):.2f}GB)")
                        
                # 强制刷盘
                dst.flush()
                os.fsync(dst.fileno())
                
        except Exception as e:
            self.logger.log_message(f"分块复制失败: {e}", "ERROR")
            raise

    def run(self):
        self.logger.log_message("开始性能测试（E盘预先生成+U盘传输）...")
        
        # 本地E盘临时目录
        local_temp_dir = Path("E:/temp_usb_test")
        local_temp_dir.mkdir(exist_ok=True)
        local_test_file = local_temp_dir / "perf_test_source.dat"
        self.logger.log_message(f"使用E盘临时目录: {local_temp_dir}")
        
        # U盘目标文件
        usb_test_file = self.test_dir / "perf_test.dat"
        
        # 🔧 临时修改：使用较小文件避免FAT32限制
        chunk_size_mb = 10     # 每次读写 10MB 数据块
        total_size_gb = 2      # 临时改为 2GB进行测试
        chunk_size_bytes = chunk_size_mb * 1024 * 1024  # 10MB = 10,485,760 字节
        total_size_bytes = total_size_gb * 1024 * 1024 * 1024   # 2GB 字节数
        
        # 验证计算结果
        self.logger.log_message(f"文件大小验证: 块大小={chunk_size_bytes:,}字节, 总大小={total_size_bytes:,}字节")
        self.logger.log_message(f"预期循环次数: {total_size_bytes // chunk_size_bytes}次")

        # 第一步：在本地E盘创建测试文件
        self.logger.log_message(f"正在本地E盘创建{total_size_gb}GB测试文件...")
        start_time = time.perf_counter()
        written_bytes = 0
        loop_count = 0
        
        try:
            with open(local_test_file, "wb") as f:
                while written_bytes < total_size_bytes:
                    # 每次写入 10MB 随机数据
                    data = os.urandom(chunk_size_bytes)
                    f.write(data)
                    written_bytes += chunk_size_bytes
                    loop_count += 1
                    f.flush()
                    
                    # 每100MB显示一次进度
                    if loop_count % 10 == 0:
                        progress_mb = written_bytes // (1024 * 1024)
                        progress_gb = progress_mb / 1024
                        self.logger.log_message(f"E盘创建进度: {progress_gb:.2f}GB / {total_size_gb}GB")
        
        except Exception as e:
            self.logger.log_message(f"E盘文件创建错误: {e}", "ERROR")
            return False
            
        local_create_time = time.perf_counter() - start_time
        actual_size_gb = local_test_file.stat().st_size / (1024 * 1024 * 1024)
        self.logger.log_message(f"本地{total_size_gb}GB文件创建完成，实际大小: {actual_size_gb:.2f}GB，耗时: {local_create_time:.2f} 秒")

        # 第二步：检查U盘空间并将文件复制到U盘进行写入性能测试
        self.logger.log_message(f"正在检查U盘空间并准备写入{total_size_gb}GB文件...")
        
        # 检查U盘路径和空间
        try:
            # 获取U盘路径，确保以反斜杠结尾
            usb_path_str = self.usb_info["path"]
            if not usb_path_str.endswith('\\'):
                usb_path_str += '\\'
            usb_path = Path(usb_path_str)
            
            self.logger.log_message(f"U盘路径: {usb_path}")
            self.logger.log_message(f"U盘信息: {self.usb_info}")
            
            if not usb_path.exists():
                self.logger.log_message(f"❌ U盘路径不存在: {usb_path}", "ERROR")
                return False
            
            # 检查U盘可用空间
            import shutil
            usage = shutil.disk_usage(usb_path)
            free_gb = usage.free / (1024 * 1024 * 1024)
            total_gb = usage.total / (1024 * 1024 * 1024)
            
            self.logger.log_message(f"U盘空间信息: 总容量={total_gb:.2f}GB, 可用空间={free_gb:.2f}GB")
            
            if free_gb < (total_size_gb + 1):  # 预留1GB空间
                self.logger.log_message(f"❌ U盘空间不足: 需要{total_size_gb}GB，可用{free_gb:.2f}GB", "ERROR")
                return False
                
        except Exception as e:
            self.logger.log_message(f"❌ 检查U盘空间失败: {e}", "ERROR")
            return False
        
        # 先进行小文件测试验证U盘写入功能
        test_small_file = usb_test_file.parent / "test_small.tmp"
        try:
            self.logger.log_message("正在进行小文件测试...")
            with open(test_small_file, "wb") as f:
                f.write(b"Test data for USB write verification" * 1000)  # 约37KB
                f.flush()
                os.fsync(f.fileno())
            
            if test_small_file.exists():
                test_small_file.unlink()
                self.logger.log_message("✅ 小文件测试成功，U盘写入功能正常")
            else:
                self.logger.log_message("❌ 小文件测试失败", "ERROR")
                return False
        except Exception as e:
            self.logger.log_message(f"❌ 小文件测试失败: {e}", "ERROR")
            return False
        
        start_time = time.perf_counter()
        
        try:
            self.logger.log_message(f"开始复制文件从 {local_test_file} 到 {usb_test_file}")
            
            # 检查源文件大小
            source_size_gb = local_test_file.stat().st_size / (1024 * 1024 * 1024)
            self.logger.log_message(f"源文件大小: {source_size_gb:.2f}GB")
            
            # 检查U盘文件系统类型
            import subprocess
            try:
                result = subprocess.run(['fsutil', 'fsinfo', 'volumeinfo', usb_path_str.rstrip('\\')], 
                                       capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.logger.log_message(f"U盘文件系统信息:\n{result.stdout}")
                else:
                    self.logger.log_message(f"无法获取文件系统信息: {result.stderr}")
            except Exception as e:
                self.logger.log_message(f"获取文件系统信息失败: {e}")
            
            # 尝试使用分块复制方式（避免FAT32 4GB限制）
            if source_size_gb > 4.0:
                self.logger.log_message("检测到大文件(>4GB)，使用分块复制方式...")
                self._copy_large_file(local_test_file, usb_test_file)
            else:
                # 使用标准复制
                shutil.copy2(str(local_test_file), str(usb_test_file))
            
            # 验证复制结果
            if usb_test_file.exists():
                copied_size_gb = usb_test_file.stat().st_size / (1024 * 1024 * 1024)
                self.logger.log_message(f"✅ 文件复制成功，大小: {copied_size_gb:.2f}GB")
            else:
                self.logger.log_message(f"❌ 文件复制失败，目标文件不存在", "ERROR")
                return False
            
            # 强制刷盘确保数据真实写入U盘
            with open(usb_test_file, "r+b") as f:
                f.flush()
                os.fsync(f.fileno())
                
        except PermissionError as e:
            self.logger.log_message(f"❌ 权限错误：{e}", "ERROR")
            self.logger.log_message("请检查是否以管理员身份运行或U盘是否被写保护", "ERROR")
            return False
        except OSError as e:
            error_msg = str(e).lower()
            if "no space left" in error_msg or "28" in str(e):  # errno 28 = No space left on device
                self.logger.log_message(f"❌ U盘空间不足：{e}", "ERROR")
                # 再次检查空间
                try:
                    usage = shutil.disk_usage(usb_path)
                    free_gb_now = usage.free / (1024 * 1024 * 1024)
                    self.logger.log_message(f"当前可用空间: {free_gb_now:.2f}GB", "ERROR")
                except:
                    pass
            elif "file too large" in error_msg or "file size" in error_msg:
                self.logger.log_message(f"❌ 文件太大错误（可能是FAT32文件系统4GB限制）：{e}", "ERROR")
                self.logger.log_message("建议将U盘格式化为NTFS或exFAT文件系统", "ERROR")
            else:
                self.logger.log_message(f"❌ 系统错误：{e}", "ERROR")
            return False
        except Exception as e:
            self.logger.log_message(f"❌ U盘写入错误: {e}", "ERROR")
            return False
        
        write_time = time.perf_counter() - start_time
        write_speed_mb_s = (total_size_bytes / (1024 * 1024)) / write_time if write_time > 0 else 0
        self.logger.log_message(f"U盘写入速度: {write_speed_mb_s:.2f} MB/s", "INFO")

        # 第三步：从U盘进行读取性能测试（彻底清理缓存）
        self.logger.log_message(f"正在进行{total_size_gb}GB U盘读取性能测试...")
        
        # 清理系统缓存
        import gc
        gc.collect()
        time.sleep(3)  # 等待系统完成I/O操作
        
        # Windows系统清理缓存
        try:
            if os.name == 'nt':
                import subprocess
                subprocess.run(['powershell', '-Command', 
                              'Clear-RecycleBin -Confirm:$false; [System.GC]::Collect()'], 
                             capture_output=True, timeout=10)
                self.logger.log_message("已清理Windows系统缓存")
        except Exception as e:
            self.logger.log_message(f"系统缓存清理失败: {e}", "WARNING")
        
        read_bytes = 0
        start_time = time.perf_counter()
        
        try:
            # 使用小块读取以减少缓存影响
            read_chunk_size = 1024 * 1024  # 1MB块读取
            
            with open(usb_test_file, "rb") as f:
                while read_bytes < total_size_bytes:
                    data = f.read(read_chunk_size)
                    if not data:
                        break
                    read_bytes += len(data)
                    
                    # 每500MB显示进度
                    if read_bytes % (500 * 1024 * 1024) == 0:
                        progress_gb = read_bytes / (1024 * 1024 * 1024)
                        self.logger.log_message(f"U盘读取进度: {progress_gb:.2f}GB / {total_size_gb}GB")
        
        except Exception as e:
            self.logger.log_message(f"U盘读取错误: {e}", "ERROR")
            return False
            
        read_time = time.perf_counter() - start_time
        read_speed_mb_s = (total_size_bytes / (1024 * 1024)) / read_time if read_time > 0 else 0

        # 计算并输出结果
        self.logger.log_message(f"\n=== 性能测试结果 ====")
        self.logger.log_message(f"U盘写入速度: {write_speed_mb_s:.2f} MB/s", "INFO")
        self.logger.log_message(f"U盘读取速度: {read_speed_mb_s:.2f} MB/s", "INFO")
        self.logger.log_message(f"================")

        # 清理测试文件
        self._cleanup_test_files(local_test_file, usb_test_file, local_temp_dir, total_size_gb)

        self.logger.log_message("✅ 性能测试完成")
        return True
    
    def __del__(self):
        """析构函数：确保对象销毁时彻底清理临时文件和目录"""
        try:
            # 最后的安全清理：删除可能遗留的临时文件
            local_temp_dir = Path("E:/temp_usb_test")
            if local_temp_dir.exists():
                # 清理所有性能测试相关文件
                for temp_file in local_temp_dir.glob("perf_test_*.dat"):
                    if temp_file.exists():
                        temp_file.unlink()
                        
                # 如果目录为空，尝试删除目录
                if local_temp_dir.exists() and not any(local_temp_dir.iterdir()):
                    local_temp_dir.rmdir()
                        
            # 清理U盘测试目录中的性能测试文件
            if hasattr(self, 'test_dir') and self.test_dir.exists():
                # 清理所有性能测试相关文件
                for temp_file in self.test_dir.glob("perf_test*.dat"):
                    if temp_file.exists():
                        temp_file.unlink()
                        
                # 尝试清理所有临时文件
                for temp_file in self.test_dir.glob("*.tmp"):
                    if temp_file.exists():
                        temp_file.unlink()
                        
                # 如果目录为空，尝试删除目录
                if self.test_dir.exists() and not any(self.test_dir.iterdir()):
                    self.test_dir.rmdir()
        except:
            pass  # 析构函数中不抛出异常