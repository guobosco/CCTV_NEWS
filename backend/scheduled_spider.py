#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时执行新闻联播爬虫程序
功能：每隔2小时爬取今天的新闻，插入SQLite数据库
"""

# 导入必要的模块
import os  # 用于文件和目录操作
import sys  # 用于系统相关操作，如退出程序
import time  # 用于时间相关操作，如休眠
import schedule  # 用于设置定时任务
import logging  # 用于日志记录
import subprocess  # 用于执行外部命令
from datetime import datetime, timedelta  # 用于日期和时间处理

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,  # 日志级别，INFO表示只记录INFO及以上级别的日志
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式，包含时间、级别和消息
    handlers=[
        logging.FileHandler('scheduled_spider.log', encoding='utf-8'),  # 日志文件输出，使用utf-8编码
        logging.StreamHandler()  # 控制台输出
    ]
)
logger = logging.getLogger(__name__)  # 获取日志记录器实例

class ScheduledSpider:
    """
    定时爬虫类，用于每隔2小时执行一次新闻联播爬虫
    """
    
    def __init__(self):
        """
        初始化定时爬虫实例
        设置必要的文件路径和配置
        """
        # 获取当前脚本所在目录的绝对路径
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 爬虫主程序的完整路径，news_to_sqlite.py用于爬取单天新闻
        self.spider_script = os.path.join(self.script_dir, 'news_to_sqlite.py')
        
        # SQLite数据库文件的完整路径
        self.db_path = os.path.join(self.script_dir, 'news.db')
        
        # Python解释器的完整路径，用于执行爬虫脚本
        self.python_path = 'C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python313\\python.exe'
        
        # 记录初始化日志
        logger.info("=== 定时爬虫程序初始化 ===")
        logger.info(f"脚本目录: {self.script_dir}")
        logger.info(f"爬虫脚本: {self.spider_script}")
        logger.info(f"数据库文件: {self.db_path}")
        logger.info(f"Python解释器: {self.python_path}")
        
        # 检查必要文件是否存在
        self.check_files()
    
    def check_files(self):
        """
        检查必要文件是否存在
        包括Python解释器和爬虫脚本
        如果文件不存在，记录错误并退出程序
        """
        # 检查Python解释器是否存在
        if not os.path.exists(self.python_path):
            logger.error(f"Python解释器不存在: {self.python_path}")
            sys.exit(1)  # 退出程序，返回码1表示错误
        
        # 检查爬虫脚本是否存在
        if not os.path.exists(self.spider_script):
            logger.error(f"爬虫脚本不存在: {self.spider_script}")
            sys.exit(1)  # 退出程序，返回码1表示错误
        
        # 所有必要文件检查通过
        logger.info("✅ 所有必要文件检查通过")
    
    def get_today_date(self):
        """
        获取今天的日期
        
        :return: 今天的日期字符串，格式为YYYY-MM-DD
        """
        return datetime.now().strftime('%Y-%m-%d')
    
    def run_spider(self):
        """
        执行爬虫程序
        爬取今天的新闻，并将结果存入SQLite数据库
        """
        # 获取今天的日期
        today = self.get_today_date()
        logger.info(f"=== 开始执行爬虫任务 ===")
        logger.info(f"爬取日期: {today}")
        
        try:
            # 构建执行命令列表
            # 命令格式：python.exe news_to_sqlite.py --date YYYY-MM-DD --db news.db
            cmd = [
                self.python_path,  # Python解释器
                self.spider_script,  # 爬虫脚本
                '--date', today,  # 日期参数，爬取今天的新闻
                '--db', self.db_path  # 数据库路径参数
            ]
            
            # 记录执行命令日志
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            # 执行命令，捕获输出和错误
            # subprocess.run()用于执行外部命令
            # capture_output=True 捕获标准输出和标准错误
            # text=True 将输出转换为字符串格式
            # cwd=self.script_dir 设置命令执行的工作目录
            # timeout=300 设置超时时间为5分钟
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.script_dir,
                timeout=300  # 设置5分钟超时
            )
            
            # 检查命令执行结果
            if result.returncode == 0:  # returncode为0表示命令执行成功
                logger.info(f"✅ 爬虫任务执行成功")
                
                # 如果有标准输出，记录为debug级别日志
                if result.stdout:
                    logger.debug(f"输出: {result.stdout}")
                
                # 如果有标准错误，记录为warning级别日志
                if result.stderr:
                    logger.warning(f"警告: {result.stderr}")
            else:  # returncode不为0表示命令执行失败
                logger.error(f"❌ 爬虫任务执行失败，返回码: {result.returncode}")
                
                # 记录错误信息
                if result.stdout:
                    logger.error(f"输出: {result.stdout}")
                if result.stderr:
                    logger.error(f"错误: {result.stderr}")
        except subprocess.TimeoutExpired:  # 捕获超时异常
            logger.error(f"❌ 爬虫任务执行超时")
        except Exception as e:  # 捕获其他异常
            logger.error(f"❌ 执行爬虫任务时发生异常: {e}")
        finally:  # 无论是否发生异常，都会执行
            logger.info(f"=== 爬虫任务执行结束 ===")
    
    def run_immediately(self):
        """
        立即执行一次爬虫任务
        不等待定时任务的触发
        """
        logger.info("立即执行一次爬虫任务...")
        self.run_spider()
    
    def setup_schedule(self):
        """
        设置定时任务
        使用schedule库设置每隔2小时执行一次爬虫任务
        """
        # 每隔2小时执行一次run_spider方法
        schedule.every(2).hours.do(self.run_spider)
        logger.info("✅ 定时任务设置完成，每隔2小时执行一次")
        logger.info(f"下次执行时间: {schedule.next_run()}")  # 打印下次执行时间
    
    def start(self):
        """
        启动定时爬虫程序
        1. 立即执行一次爬虫任务
        2. 设置定时任务
        3. 启动调度器，循环检查并执行任务
        """
        # 立即执行一次爬虫任务
        self.run_immediately()
        
        # 设置定时任务
        self.setup_schedule()
        
        # 启动调度器，循环检查并执行任务
        logger.info("启动调度器，按Ctrl+C停止")
        try:
            while True:  # 无限循环
                schedule.run_pending()  # 运行所有待执行的任务
                time.sleep(60)  # 每60秒检查一次是否有任务需要执行
        except KeyboardInterrupt:  # 捕获Ctrl+C中断信号
            logger.info("收到终止信号，退出程序")
        except Exception as e:  # 捕获其他异常
            logger.error(f"调度器运行时发生异常: {e}")


# 程序入口检查
# 如果当前脚本被直接执行（而不是被导入），则执行以下代码
if __name__ == '__main__':
    # 创建定时爬虫实例
    spider = ScheduledSpider()
    # 启动定时爬虫程序
    spider.start()