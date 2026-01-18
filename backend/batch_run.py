#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量执行新闻联播爬虫结果存入SQLite数据库
日期范围：从2025年1月1日至昨天
"""

# 导入必要的模块
import datetime  # 用于日期处理
import subprocess  # 用于执行外部命令
import os  # 用于文件路径处理
import logging  # 用于日志记录
import yaml  # 用于解析YAML配置文件

# 加载配置文件
def load_config():
    """
    加载配置文件
    
    :return: 配置字典
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        # 返回默认配置
        return {
            'batch': {
                'python_path': 'python.exe',
                'main_script': 'news_to_sqlite.py',
                'default_start_date': '2022-01-01'
            },
            'logging': {
                'level': 'INFO',
                'batch_log_file': 'batch_run.log'
            }
        }

# 加载配置
config = load_config()

# 配置日志系统
logging.basicConfig(
    level=getattr(logging, config['logging']['level'], logging.INFO),  # 日志级别，使用配置文件中的值
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式，包含时间、级别和消息
    handlers=[
        logging.FileHandler(config['logging']['batch_log_file'], encoding='utf-8'),  # 日志文件输出，使用utf-8编码
        logging.StreamHandler()  # 控制台输出
    ]
)
logger = logging.getLogger(__name__)  # 获取日志记录器实例

class BatchRunner:
    """
    批量执行新闻联播爬虫的类
    用于执行指定日期范围内的新闻联播爬虫程序
    """
    
    def __init__(self):
        """
        初始化批量爬虫程序
        设置脚本路径、数据库路径等必要参数
        """
        # 获取当前脚本所在目录的绝对路径
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 主爬虫脚本的完整路径，news_to_sqlite.py用于爬取单天新闻
        self.main_script = os.path.join(self.script_dir, config['batch']['main_script'])
        
        # SQLite数据库文件的完整路径
        self.db_path = os.path.join(self.script_dir, config['database']['path'])
        
        # 记录初始化日志
        logger.info(f"=== 批量爬虫程序初始化 ===")
        logger.info(f"主脚本: {self.main_script}")
        logger.info(f"数据库: {self.db_path}")
        logger.info(f"脚本目录: {self.script_dir}")
        
    def run_single_date(self, date_str):
        """
        执行单个日期的爬虫程序
        
        :param date_str: 日期字符串，格式为YYYY-MM-DD
        :return: bool 是否执行成功，True表示成功，False表示失败
        """
        try:
            # 记录开始处理日志
            logger.info(f"开始处理日期: {date_str}")
            
            # 构建执行命令列表
            # 命令格式：python.exe news_to_sqlite.py --date YYYY-MM-DD --db news.db
            cmd = [
                # Python解释器路径，使用配置文件中的路径
                config['batch']['python_path'],
                self.main_script,  # 主爬虫脚本
                '--date', date_str,  # 日期参数
                '--db', self.db_path  # 数据库路径参数
            ]
            
            # 记录执行命令日志，将命令列表转换为字符串便于查看
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            # 执行命令，捕获输出和错误
            # subprocess.run()用于执行外部命令
            # capture_output=True 捕获标准输出和标准错误
            # text=True 将输出转换为字符串格式
            # cwd=self.script_dir 设置命令执行的工作目录
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.script_dir)
            
            # 检查命令执行结果
            if result.returncode == 0:  # returncode为0表示命令执行成功
                logger.info(f"✅ 日期 {date_str} 处理成功")
                
                # 如果有标准输出，记录为debug级别日志
                if result.stdout:
                    logger.debug(f"输出: {result.stdout}")
                
                # 如果有标准错误，记录为warning级别日志
                if result.stderr:
                    logger.warning(f"警告输出: {result.stderr}")
                
                return True  # 返回执行成功
            else:  # returncode不为0表示命令执行失败
                logger.error(f"❌ 日期 {date_str} 处理失败，返回码: {result.returncode}")
                
                # 记录错误信息
                if result.stdout:
                    logger.error(f"输出: {result.stdout}")
                if result.stderr:
                    logger.error(f"错误: {result.stderr}")
                
                return False  # 返回执行失败
                
        except Exception as e:  # 捕获所有异常
            logger.error(f"❌ 日期 {date_str} 执行异常: {e}")
            return False  # 返回执行失败
    
    def run_batch(self, start_date, end_date):
        """
        批量执行指定日期范围的爬虫程序
        
        :param start_date: 开始日期，格式为YYYY-MM-DD
        :param end_date: 结束日期，格式为YYYY-MM-DD
        :return: bool 是否批量执行成功，True表示成功，False表示失败
        """
        try:
            # 将日期字符串转换为datetime对象
            start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            
            # 检查开始日期是否大于结束日期
            if start > end:
                logger.error("开始日期不能大于结束日期")
                return False
            
            # 记录开始批量处理日志
            logger.info(f"=== 开始批量处理 ===")
            logger.info(f"日期范围: {start_date} 至 {end_date}")
            logger.info(f"总天数: {((end - start).days + 1)} 天")
            
            # 初始化统计变量
            total_days = 0  # 总处理天数
            success_days = 0  # 处理成功天数
            failed_days = 0  # 处理失败天数
            skipped_days = 0  # 跳过天数
            
            # 循环处理每一天
            current_date = start  # 当前处理日期，初始为开始日期
            while current_date <= end:  # 循环条件：当前日期小于等于结束日期
                date_str = current_date.strftime('%Y-%m-%d')  # 格式化日期为字符串
                total_days += 1  # 总天数+1
                
                # 执行单个日期的爬虫程序
                if self.run_single_date(date_str):
                    success_days += 1  # 成功天数+1
                else:
                    failed_days += 1  # 失败天数+1
                
                # 增加一天，处理下一天
                current_date += datetime.timedelta(days=1)
                
                # 注释掉的延迟，如需避免请求过快可取消注释
                # time.sleep(0.5)
            
            # 计算成功率
            success_rate = success_days / total_days * 100 if total_days > 0 else 0
            
            # 记录批量处理完成日志
            logger.info(f"=== 批量处理完成 ===")
            logger.info(f"总天数: {total_days}")
            logger.info(f"成功天数: {success_days}")
            logger.info(f"失败天数: {failed_days}")
            logger.info(f"跳过天数: {skipped_days}")
            logger.info(f"成功率: {success_rate:.2f}%")
            
            return True  # 返回批量执行成功
            
        except ValueError as e:  # 捕获日期格式错误
            logger.error(f"日期格式错误: {e}")
            logger.error("请使用 YYYY-MM-DD 格式")
            return False  # 返回批量执行失败
        except Exception as e:  # 捕获其他异常
            logger.error(f"批量执行异常: {e}")
            return False  # 返回批量执行失败


def main():
    """
    主函数，程序入口
    用于解析命令行参数，初始化批量爬虫程序并执行
    """
    import argparse  # 导入命令行参数解析模块
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='批量执行新闻联播爬虫')
    
    # 添加命令行参数
    # --start: 开始日期，使用配置文件中的默认值
    parser.add_argument('--start', default=config['batch']['default_start_date'], help='开始日期，格式 YYYY-MM-DD')
    # --end: 结束日期，默认为昨天
    parser.add_argument('--end', help='结束日期，格式 YYYY-MM-DD，默认为昨天')
    # --db: 数据库文件路径，默认使用当前目录的news.db
    parser.add_argument('--db', help='数据库文件路径，默认使用当前目录的news.db')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果未指定结束日期，设置为昨天
    if not args.end:
        # 获取昨天的日期
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        # 格式化昨天的日期为字符串
        args.end = yesterday.strftime('%Y-%m-%d')
    
    # 记录程序启动日志
    logger.info(f"=== 批量爬虫程序启动 ===")
    logger.info(f"命令行参数: {args}")
    
    # 创建批量运行实例
    runner = BatchRunner()
    
    # 如果指定了数据库路径，更新数据库路径
    if args.db:
        runner.db_path = args.db
        logger.info(f"更新数据库路径为: {runner.db_path}")
    
    # 执行批量运行
    success = runner.run_batch(args.start, args.end)
    
    # 记录程序执行结果日志
    if success:
        logger.info("✅ 批量爬虫程序执行完成")
    else:
        logger.error("❌ 批量爬虫程序执行失败")


# 程序入口检查
# 如果当前脚本被直接执行（而不是被导入），则执行main函数
if __name__ == '__main__':
    main()