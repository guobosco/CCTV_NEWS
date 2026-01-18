#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播爬虫结果存入SQLite数据库
功能：爬取指定日期的新闻联播内容，并将结果存入SQLite数据库
"""

# 导入必要的模块
import requests  # 用于发送HTTP请求，获取网页内容
import sqlite3  # 用于SQLite数据库操作
import time  # 用于添加延迟，避免请求过快
import argparse  # 用于解析命令行参数
import logging  # 用于日志记录
import re  # 用于正则表达式匹配，清理新闻内容
import os  # 用于文件路径处理
from datetime import datetime  # 用于处理日期和时间
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
            'spider': {
                'backend_url': 'http://localhost:5001',
                'request_timeout': 10,
                'request_delay': 0.5
            },
            'database': {'path': 'news.db'},
            'logging': {
                'level': 'INFO',
                'news_log_file': 'news_to_sqlite.log'
            }
        }

# 加载配置
config = load_config()

# 配置日志系统
logging.basicConfig(
    level=getattr(logging, config['logging']['level'], logging.INFO),  # 日志级别，使用配置文件中的值
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式，包含时间、级别和消息
    handlers=[
        logging.FileHandler(config['logging']['news_log_file'], encoding='utf-8'),  # 日志文件输出，使用utf-8编码
        logging.StreamHandler()  # 控制台输出
    ]
)
logger = logging.getLogger(__name__)  # 获取日志记录器实例

class NewsToSQLite:
    """
    新闻联播爬虫结果存入SQLite数据库的类
    用于爬取指定日期的新闻联播内容，并将结果存入SQLite数据库
    """
    
    def __init__(self, db_path='news.db'):
        """
        初始化NewsToSQLite实例
        
        :param db_path: SQLite数据库文件路径，默认为当前目录下的news.db
        """
        self.db_path = db_path  # 数据库文件路径
        self.conn = None  # 数据库连接对象，初始为None
        self.cursor = None  # 数据库游标对象，初始为None
    
    def connect(self):
        """
        连接SQLite数据库
        
        :return: bool 是否连接成功，True表示成功，False表示失败
        """
        try:
            # 连接SQLite数据库
            # check_same_thread=False 允许在不同线程中使用同一个连接
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # 设置row_factory为sqlite3.Row，使查询结果可以像字典一样访问
            self.conn.row_factory = sqlite3.Row
            # 获取游标对象，用于执行SQL语句
            self.cursor = self.conn.cursor()
            
            # 记录连接成功日志
            logger.info(f"成功连接到SQLite数据库: {self.db_path}")
            return True
        except sqlite3.Error as e:
            # 连接失败，记录错误日志
            logger.error(f"连接数据库失败: {e}")
            return False
    
    def create_table(self):
        """
        创建新闻表（如果不存在）
        同时创建必要的索引，提高查询效率
        
        :return: bool 是否创建成功，True表示成功，False表示失败
        """
        # 创建新闻表的SQL语句
        # IF NOT EXISTS 表示如果表已存在则不创建
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS news_联播 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 主键，自动递增
            date TEXT NOT NULL,  -- 新闻日期，格式为YYYY-MM-DD
            title TEXT NOT NULL,  -- 新闻标题
            link TEXT NOT NULL UNIQUE,  -- 新闻链接，唯一约束，避免重复
            item_number TEXT NOT NULL,  -- 新闻条目编号，格式：1/16
            total_items INTEGER NOT NULL,  -- 当日新闻总条数
            content TEXT NOT NULL,  -- 新闻内容
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 创建时间，自动生成
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP  -- 更新时间，自动生成
        );
        """
        try:
            # 执行创建表的SQL语句
            self.cursor.execute(create_table_sql)
            
            # 创建索引，提高查询效率
            # 按日期查询的索引
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON news_联播(date);")
            # 按标题查询的索引
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON news_联播(title);")
            # 按链接查询的索引
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_link ON news_联播(link);")
            
            # 提交事务
            self.conn.commit()
            
            # 记录创建成功日志
            logger.info("成功创建/确认新闻表和索引")
            return True
        except sqlite3.Error as e:
            # 创建失败，记录错误日志
            logger.error(f"创建表失败: {e}")
            return False
    
    def has_date_data(self, date):
        """
        检查数据库中是否已有该日的数据
        
        :param date: 日期字符串，格式为YYYY-MM-DD
        :return: bool 是否已有数据，True表示已有数据，False表示没有数据或查询失败
        """
        try:
            # 查询指定日期的数据数量
            self.cursor.execute("SELECT COUNT(*) AS count FROM news_联播 WHERE date = ?", (date,))
            # 获取查询结果
            result = self.cursor.fetchone()
            # 如果数量大于0，说明已有数据
            return result['count'] > 0
        except sqlite3.Error as e:
            # 查询失败，记录错误日志
            logger.error(f"检查日期数据失败: {e}")
            return False
    
    def fetch_news_list(self, date):
        """
        获取指定日期的新闻列表
        调用backend服务的/news/content接口获取新闻列表
        
        :param date: 日期字符串，格式为YYYY-MM-DD
        :return: 新闻列表数组，如果获取失败返回None
        """
        try:
            # 构建请求URL，调用backend服务
            url = f'{config["spider"]["backend_url"]}/news/content?date={date}'
            # 发送GET请求，使用配置文件中的超时时间
            response = requests.get(url, timeout=config["spider"]["request_timeout"])
            
            # 检查响应状态码，200表示请求成功
            if response.status_code == 200:
                # 解析JSON响应数据
                data = response.json()
                # 检查返回的code，200表示成功
                if data['code'] == 200:
                    # 记录成功日志
                    logger.info(f"成功获取 {date} 的新闻列表，共 {len(data['data']['items'])} 条新闻")
                    # 返回新闻列表
                    return data['data']['items']
                else:
                    # 返回的code不是200，获取失败
                    logger.error(f"获取新闻列表失败: {data['message']}")
                    return None
            else:
                # 响应状态码不是200，请求失败
                logger.error(f"请求新闻列表失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            # 发生异常，记录错误日志
            logger.error(f"获取新闻列表异常: {e}")
            return None
    
    def fetch_news_content(self, link):
        """
        获取单条新闻的详细内容
        调用backend服务的/news/item接口获取新闻详情
        
        :param link: 新闻链接
        :return: 新闻内容字符串，如果获取失败返回None
        """
        try:
            # 构建请求URL，调用backend服务
            url = f'{config["spider"]["backend_url"]}/news/item?link={link}'
            # 发送GET请求，使用配置文件中的超时时间
            response = requests.get(url, timeout=config["spider"]["request_timeout"])
            
            # 检查响应状态码，200表示请求成功
            if response.status_code == 200:
                # 解析JSON响应数据
                data = response.json()
                # 检查返回的code，200表示成功
                if data['code'] == 200:
                    # 返回新闻内容
                    return data['data']['content']
                else:
                    # 返回的code不是200，获取失败
                    logger.error(f"获取新闻内容失败: {data['message']}")
                    return None
            else:
                # 响应状态码不是200，请求失败
                logger.error(f"请求新闻内容失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            # 发生异常，记录错误日志
            logger.error(f"获取新闻内容异常: {e}")
            return None
    
    def clean_news_content(self, content):
        """
        清理新闻内容，移除HTML标签、乱码和无效字符
        
        :param content: 原始新闻内容
        :return: 清理后的新闻内容
        """
        # 如果内容为空，直接返回
        if not content:
            return content
        
        # 初始化清理后的内容
        cleaned = content
        
        # 1. 移除所有HTML标签，使用正则表达式
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # 2. 移除JavaScript代码模式1
        if 'ent").css("display","none");' in cleaned:
            cleaned = cleaned.split('ent").css("display","none");')[0]
        
        # 3. 移除JavaScript代码模式2
        if 'if ($.trim($("#content_area").html())==""){' in cleaned:
            cleaned = cleaned.split('if ($.trim($("#content_area").html())==""{')[0]
        
        # 4. 移除特殊字符和乱码，ASCII码范围
        cleaned = re.sub(r'[\x00-\x1f\x7f-\xff]+', '', cleaned)
        
        # 5. 移除无效乱码，只保留中文、英文、数字、空格和常见标点符号
        # [^\u4e00-\u9fa5a-zA-Z0-9\s，。！？：；“”‘’（）《》【】、·…—]+ 表示匹配不在这些范围内的字符
        cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？：；“”‘’（）《》【】、·…—]+', '', cleaned, flags=re.UNICODE)
        
        # 6. 移除连续空格和换行符，清理首尾空格
        cleaned = cleaned.rstrip('\r\n')
        cleaned = cleaned.strip()
        
        # 返回清理后的内容
        return cleaned
    
    def insert_news(self, news_item, date, total_items, item_index):
        """
        插入新闻数据到数据库
        
        :param news_item: 新闻条目字典，包含title、link、content等字段
        :param date: 新闻日期，格式为YYYY-MM-DD
        :param total_items: 当日新闻总条数
        :param item_index: 当前新闻条目索引，从0开始
        :return: bool 是否插入成功，True表示成功，False表示失败
        """
        try:
            # 准备插入语句，使用INSERT OR REPLACE
            # 当遇到唯一约束冲突时，替换原有数据
            insert_sql = """
            INSERT OR REPLACE INTO news_联播 (date, title, link, item_number, total_items, content)
            VALUES (?, ?, ?, ?, ?, ?);
            """
            
            # 准备插入数据
            # item_number格式："1/16"，表示第1条，共16条
            item_number = f"{item_index+1}/{total_items}"
            # 清理新闻内容
            content = self.clean_news_content(news_item.get('content', ''))
            # 数据元组，对应SQL语句中的占位符
            data = (
                date,  # 新闻日期
                news_item['title'],  # 新闻标题
                news_item['link'],  # 新闻链接
                item_number,  # 新闻条目编号
                total_items,  # 当日新闻总条数
                content  # 清理后的新闻内容
            )
            
            # 执行插入语句
            self.cursor.execute(insert_sql, data)
            # 提交事务
            self.conn.commit()
            
            # 记录插入成功日志
            logger.info(f"成功插入新闻: {news_item['title']}")
            return True
        except sqlite3.Error as e:
            # 插入失败，记录错误日志
            logger.error(f"插入新闻失败: {e}")
            return False
    
    def run(self, date):
        """
        主运行函数，执行完整的爬虫流程
        1. 连接数据库
        2. 创建表
        3. 检查是否已有该日数据
        4. 获取新闻列表
        5. 遍历新闻列表，获取每条新闻的详细内容并插入数据库
        
        :param date: 要爬取的日期，格式为YYYY-MM-DD
        :return: bool 是否执行成功，True表示成功，False表示失败
        """
        # 连接数据库
        if not self.connect():
            return False
        
        # 创建表
        if not self.create_table():
            return False
        
        # 检查是否已有该日数据
        if self.has_date_data(date):
            logger.info(f"数据库中已有 {date} 的数据，跳过处理")
            return True
        
        # 获取新闻列表
        news_list = self.fetch_news_list(date)
        if not news_list:
            logger.error(f"无法获取 {date} 的新闻列表")
            return False
        
        # 获取新闻总条数
        total_items = len(news_list)
        logger.info(f"开始处理 {date} 的 {total_items} 条新闻")
        
        # 遍历新闻列表，获取每条新闻的详细内容并插入数据库
        for i, news_item in enumerate(news_list):
            logger.info(f"处理新闻 {i+1}/{total_items}: {news_item['title']}")
            
            # 获取新闻详情
            content = self.fetch_news_content(news_item['link'])
            if content:
                # 将内容添加到新闻条目字典中
                news_item['content'] = content
                
                # 插入数据库
                self.insert_news(news_item, date, total_items, i)
            else:
                # 无法获取新闻内容，记录警告日志
                logger.warning(f"无法获取新闻内容: {news_item['title']}")
            
            # 避免请求过快，添加配置文件中的延迟
            time.sleep(config['spider']['request_delay'])
        
        # 记录处理完成日志
        logger.info(f"完成处理 {date} 的所有新闻")
        return True
    
    def close(self):
        """
        关闭数据库连接
        释放资源，避免内存泄漏
        """
        try:
            # 如果游标对象存在，关闭游标
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            # 如果连接对象存在，关闭连接
            if self.conn:
                self.conn.close()
                self.conn = None
            # 记录关闭成功日志
            logger.info("已关闭数据库连接")
        except Exception as e:
            # 关闭失败，记录警告日志
            logger.warning(f"关闭数据库连接时发生错误: {e}")


def main():
    """
    主函数，程序入口
    解析命令行参数，创建NewsToSQLite实例并执行
    """
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='新闻联播爬虫结果存入SQLite数据库')
    
    # 添加命令行参数
    # --date: 要爬取的日期，必填参数
    parser.add_argument('--date', required=True, help='要爬取的日期，格式：YYYY-MM-DD')
    # --db: SQLite数据库文件路径，默认值为news.db
    parser.add_argument('--db', default='news.db', help='SQLite数据库文件路径')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 创建NewsToSQLite实例
    news_to_sqlite = NewsToSQLite(db_path=args.db)
    
    try:
        # 执行爬虫流程
        success = news_to_sqlite.run(args.date)
        if success:
            logger.info("程序执行成功")
        else:
            logger.error("程序执行失败")
    finally:
        # 无论执行成功与否，都要关闭数据库连接
        news_to_sqlite.close()


# 程序入口检查
# 如果当前脚本被直接执行（而不是被导入），则执行main函数
if __name__ == '__main__':
    main()