#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播文稿获取后端服务(爬虫程序)
功能：
1. 提供新闻内容API接口
2. 爬取指定日期的新闻列表
3. 爬取单条新闻的详细内容
4. 提供数据库查询接口
"""

# 导入必要的模块
from flask import Flask, jsonify, request  # Flask框架，用于创建Web服务
from flask_cors import CORS  # CORS跨域支持
import requests  # 用于发送HTTP请求，爬取网页内容
from bs4 import BeautifulSoup  # 用于解析HTML内容
from datetime import datetime, timedelta  # 用于日期处理
import sqlite3  # 用于SQLite数据库操作
import os  # 用于文件路径处理
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
            'backend': {'host': '0.0.0.0', 'port': 5001, 'debug': True},
            'database': {'path': 'news.db'},
            'spider': {'max_retries': 5, 'request_delay': 1.0}
        }

# 加载配置
config = load_config()

# 创建Flask应用实例
app = Flask(__name__)
# 启用CORS，允许所有跨域请求
CORS(app, resources=r'/*')

# 请求头，模拟浏览器访问，避免被反爬
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# 数据库文件路径，使用绝对路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), config['database']['path'])


# 数据库连接函数
def get_db_connection():
    """
    获取数据库连接
    
    :return: sqlite3.Connection 对象，数据库连接
    """
    try:
        # 连接SQLite数据库
        conn = sqlite3.connect(DB_PATH)
        # 设置row_factory为sqlite3.Row，使查询结果可以像字典一样访问
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        # 连接失败，打印错误信息
        print(f"数据库连接失败: {e}")
        return None


# 页面获取函数
def fetch_page(url):
    """
    获取页面内容，增加重试机制和反爬优化
    
    :param url: 要爬取的网页URL
    :return: 页面HTML内容，失败返回None
    """
    max_retries = 5  # 最大重试次数
    
    # 增加请求头池，模拟不同浏览器
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/90.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/92.0.902.55"
    ]
    
    import time
    import random
    
    # 重试机制
    for retry in range(max_retries):
        try:
            print(f"请求页面 (重试 {retry+1}/{max_retries}): {url}")
            
            # 随机选择一个User-Agent
            random_headers = HEADERS.copy()
            random_headers['User-Agent'] = random.choice(user_agents)
            
            # 增加随机延迟，避免请求过于频繁
            time.sleep(random.uniform(0.5, 2.0))
            
            # 发送GET请求
            response = requests.get(url, headers=random_headers, timeout=20, stream=True)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                # 读取响应内容
                try:
                    return response.text
                except requests.ConnectionError as e:
                    print(f"读取响应内容时连接错误: {e}")
                    continue
            else:
                print(f"获取页面失败，状态码: {response.status_code}")
        except requests.Timeout:
            print(f"请求超时")
        except requests.ConnectionError as e:
            print(f"连接错误: {e}")
            # 针对连接重置错误，增加更长的延迟
            if '10054' in str(e) or '远程主机强迫关闭了一个现有的连接' in str(e):
                print(f"检测到连接重置错误，增加延迟后重试...")
                time.sleep(random.uniform(2.0, 5.0))
        except Exception as e:
            print(f"获取页面异常: {e}")
        
        # 重试间隔，随重试次数增加而增加
        retry_delay = random.uniform(1.0, 3.0) * (retry + 1)
        print(f"重试间隔: {retry_delay:.2f}秒")
        time.sleep(retry_delay)
    
    print(f"多次重试后仍无法获取页面")
    return None


# 获取最近7天的新闻列表
# @app.route('/news/list', methods=['GET'])
# def news_list():
    """
    获取最近7天的新闻列表
    
    :return: JSON格式的新闻列表
    """
    try:
        today = datetime.now()  # 获取当前日期
        news_list = []  # 初始化新闻列表
        
        # 生成最近7天的日期
        for i in range(7):
            date = today - timedelta(days=i)  # 计算日期
            date_str = date.strftime("%Y-%m-%d")  # 格式化日期
            year_month_day = date.strftime("%Y%m%d")  # 格式化日期为YYYYMMDD格式
            
            # 构建新闻URL
            news_url = f"https://tv.cctv.com/lm/xwlb/{year_month_day}.shtml"
            # 添加到新闻列表
            news_list.append({
                "date": date_str,
                "title": f"{date_str} 新闻联播",
                "link": news_url
            })
        
        # 返回成功响应
        return jsonify({
            "code": 200,
            "message": "success",
            "data": news_list
        })
        
    except Exception as e:
        # 发生异常，返回错误响应
        print(f"获取新闻列表失败: {e}")
        return jsonify({
            "code": 500,
            "message": f"获取新闻列表失败: {str(e)}",
            "data": []
        })


# 获取指定日期的新闻内容
# @app.route('/news/content', methods=['GET'])
# def news_content():
    """
    获取指定日期的新闻内容
    流程：确认日期 -> 爬取该日期的新闻标题 -> 获取每条新闻的详情链接
    
    :return: JSON格式的新闻内容
    """
    # 获取日期参数
    date = request.args.get('date')
    if not date:  # 检查日期参数是否存在
        return jsonify({
            "code": 400,
            "message": "缺少date参数"
        })
    
    try:
        print(f"\n=== 开始获取 {date} 的新闻内容 ===")
        
        # 构建指定日期的新闻页面URL
        target_date = date.replace('-', '')
        
        # 尝试多种URL格式，优先使用day子目录格式，这对历史日期更有效
        url_formats = [
            f"https://tv.cctv.com/lm/xwlb/day/{target_date}.shtml",
            f"https://tv.cctv.com/lm/xwlb/{target_date}.shtml",
            f"https://tv.cctv.com/lm/xwlb/{target_date}-1.shtml",
            f"https://tv.cctv.com/lm/xwlb/index.shtml?date={target_date}"
        ]
        
        date_page = None
        # 尝试不同的URL格式，直到获取成功
        for url_format in url_formats:
            print(f"尝试URL格式: {url_format}")
            date_page = fetch_page(url_format)
            if date_page:
                break
        
        if not date_page:  # 所有URL格式都尝试失败
            raise Exception("无法获取新闻页面")
        
        # 解析页面，提取新闻标题和链接
        soup = BeautifulSoup(date_page, 'html.parser')
        
        # 查找新闻条目，尝试多种可能的方式
        news_items = []
        
        # 方式1: 尝试当前页面的选择器
        print("尝试方式1: 查找ul标签中的新闻列表")
        ul_selectors = [
            soup.find('ul', class_='rililist'),
            soup.find('ul', id='content'),
            soup.find('ul', class_='news-items')
        ]
        
        for ul in ul_selectors:
            if ul:  # 如果找到ul标签
                list_items = ul.find_all('li')  # 查找所有li标签
                for i, li in enumerate(list_items):
                    a_tag = li.find('a')  # 查找a标签
                    if a_tag:  # 如果找到a标签
                        href = a_tag.get('href', '')  # 获取链接
                        title = a_tag.get_text(strip=True)  # 获取标题
                        if href and title:  # 链接和标题都存在
                            # 只过滤掉完整的"完整版《新闻联播》"条目（完整广播），保留其他新闻条目
                            if not (title.startswith('完整版《新闻联播》') or title.startswith('完整版<新闻联播>')):
                                # 清理标题，移除"完整版[视频]"前缀、"[视频]"标签和时间字符
                                clean_title = title
                                clean_title = clean_title.replace('完整版[视频]', '', 1)  # 移除"完整版[视频]"
                                clean_title = clean_title.replace('完整版', '', 1)  # 移除"完整版"
                                clean_title = clean_title.replace('[视频]', '', 1)  # 移除"[视频]"
                                
                                # 移除时间字符，如"00:02:18"或"20260110"等时间格式
                                import re
                                clean_title = re.sub(r'\d{2}:\d{2}:\d{2}', '', clean_title)  # 移除"00:02:18"格式
                                clean_title = re.sub(r'\d{8}', '', clean_title)  # 移除"20260110"格式
                                clean_title = re.sub(r'\d{4}-\d{2}-\d{2}', '', clean_title)  # 移除"2026-01-10"格式
                                clean_title = clean_title.strip()  # 清理空格
                                
                                # 补全相对链接
                                if not href.startswith('http'):
                                    href = f"https://tv.cctv.com{href}"
                                # 添加到新闻条目列表
                                news_items.append({
                                    "number": str(i + 1),
                                    "title": clean_title,
                                    "link": href
                                })
        
        # 方式2: 如果方式1失败，尝试查找所有包含新闻链接的div
        if not news_items:
            print("尝试方式2: 查找div标签中的新闻列表")
            div_selectors = [
                soup.find('div', class_='news-list'),
                soup.find('div', id='news-list'),
                soup.find('div', class_='list-content'),
                soup.find('div', class_='content-list'),
                soup.find('div', class_='video-list'),
                soup.find('div', id='video-list')
            ]
            
            for div in div_selectors:
                if div:  # 如果找到div标签
                    a_tags = div.find_all('a')  # 查找所有a标签
                    for i, a_tag in enumerate(a_tags):
                        href = a_tag.get('href', '')  # 获取链接
                        title = a_tag.get_text(strip=True)  # 获取标题
                        if href and title:  # 链接和标题都存在
                            # 只过滤掉完整的"完整版《新闻联播》"条目（完整广播），保留其他新闻条目
                            if not (title.startswith('完整版《新闻联播》') or title.startswith('完整版<新闻联播>')):
                                # 清理标题，移除"完整版[视频]"前缀、"[视频]"标签和时间字符
                                clean_title = title
                                if clean_title.startswith('完整版[视频]'):
                                    clean_title = clean_title[6:]  # 移除"完整版[视频]"
                                elif clean_title.startswith('完整版'):
                                    clean_title = clean_title[3:]  # 移除"完整版"
                                # 移除"[视频]"标签
                                clean_title = clean_title.replace('[视频]', '', 1)
                                
                                # 移除时间字符，如"00:02:18"或"20260110"等时间格式
                                import re
                                clean_title = re.sub(r'\d{2}:\d{2}:\d{2}', '', clean_title)  # 移除"00:02:18"格式
                                clean_title = re.sub(r'\d{8}', '', clean_title)  # 移除"20260110"格式
                                clean_title = re.sub(r'\d{4}-\d{2}-\d{2}', '', clean_title)  # 移除"2026-01-10"格式
                                clean_title = clean_title.strip()  # 清理空格
                                
                                # 补全相对链接
                                if not href.startswith('http'):
                                    href = f"https://tv.cctv.com{href}"
                                # 添加到新闻条目列表
                                news_items.append({
                                    "number": str(i + 1),
                                    "title": clean_title,
                                    "link": href
                                })
        
        # 方式3: 如果方式1和方式2失败，尝试查找页面中所有的a标签，过滤出新闻链接
        if not news_items:
            print("尝试方式3: 查找页面中所有的新闻链接")
            all_a_tags = soup.find_all('a')  # 查找所有a标签
            for i, a_tag in enumerate(all_a_tags):
                href = a_tag.get('href', '')  # 获取链接
                title = a_tag.get_text(strip=True)  # 获取标题
                # 过滤条件：链接包含news或video，且标题不为空
                if href and title and ('news' in href or 'video' in href or 'VID' in href):
                            # 只过滤掉完整的"完整版《新闻联播》"条目（完整广播），保留其他新闻条目
                            if not (title.startswith('完整版《新闻联播》') or title.startswith('完整版<新闻联播>')):
                                # 清理标题，移除"完整版[视频]"前缀、"[视频]"标签和时间字符
                                clean_title = title
                                clean_title = clean_title.replace('完整版[视频]', '', 1)  # 移除"完整版[视频]"
                                clean_title = clean_title.replace('完整版', '', 1)  # 移除"完整版"
                                clean_title = clean_title.replace('[视频]', '', 1)  # 移除"[视频]"
                                
                                # 移除时间字符，如"00:02:18"或"20260110"等时间格式
                                import re
                                clean_title = re.sub(r'\d{2}:\d{2}:\d{2}', '', clean_title)  # 移除"00:02:18"格式
                                clean_title = re.sub(r'\d{8}', '', clean_title)  # 移除"20260110"格式
                                clean_title = re.sub(r'\d{4}-\d{2}-\d{2}', '', clean_title)  # 移除"2026-01-10"格式
                                clean_title = clean_title.strip()  # 清理空格
                                
                                # 补全相对链接
                                if not href.startswith('http'):
                                    href = f"https://tv.cctv.com{href}"
                                # 添加到新闻条目列表
                                news_items.append({
                                    "number": str(i + 1),
                                    "title": clean_title,
                                    "link": href
                                })
        
        # 方式4: 如果方式1、方式2和方式3失败，尝试查找页面中包含特定关键词的链接
        if not news_items:
            print("尝试方式4: 查找包含特定关键词的链接")
            all_a_tags = soup.find_all('a')  # 查找所有a标签
            keywords = ['新闻联播', '视频', '联播快讯', '央视网']  # 关键词列表
            for i, a_tag in enumerate(all_a_tags):
                href = a_tag.get('href', '')  # 获取链接
                title = a_tag.get_text(strip=True)  # 获取标题
                if href and title:  # 链接和标题都存在
                            # 检查标题或链接中是否包含关键词
                            if any(keyword in title or keyword in href for keyword in keywords):
                                # 只过滤掉完整的"完整版《新闻联播》"条目（完整广播），保留其他新闻条目
                                if not (title.startswith('完整版《新闻联播》') or title.startswith('完整版<新闻联播>')):
                                    # 清理标题，移除"完整版[视频]"前缀、"[视频]"标签和时间字符
                                    clean_title = title
                                    clean_title = clean_title.replace('完整版[视频]', '', 1)  # 移除"完整版[视频]"
                                    clean_title = clean_title.replace('完整版', '', 1)  # 移除"完整版"
                                    clean_title = clean_title.replace('[视频]', '', 1)  # 移除"[视频]"
                                    
                                    # 移除时间字符，如"00:02:18"或"20260110"等时间格式
                                    import re
                                    clean_title = re.sub(r'\d{2}:\d{2}:\d{2}', '', clean_title)  # 移除"00:02:18"格式
                                    clean_title = re.sub(r'\d{8}', '', clean_title)  # 移除"20260110"格式
                                    clean_title = re.sub(r'\d{4}-\d{2}-\d{2}', '', clean_title)  # 移除"2026-01-10"格式
                                    clean_title = clean_title.strip()  # 清理空格
                                    
                                    # 补全相对链接
                                    if not href.startswith('http'):
                                        href = f"https://tv.cctv.com{href}"
                                    # 添加到新闻条目列表
                                    news_items.append({
                                        "number": str(i + 1),
                                        "title": clean_title,
                                        "link": href
                                    })
        
        # 方式5: 如果还是没有找到，尝试从页面标题中提取信息
        if not news_items:
            print("尝试方式5: 从页面标题提取信息")
            page_title = soup.title.text if soup.title else f"{date} 新闻联播"  # 获取页面标题
            # 只过滤掉完整的"完整版《新闻联播》"条目（完整广播）
            if not (page_title.startswith('完整版《新闻联播》') or page_title.startswith('完整版<新闻联播>')):
                # 清理标题，移除"完整版[视频]"前缀、"[视频]"标签和时间字符
                clean_title = page_title
                clean_title = clean_title.replace('完整版[视频]', '', 1)  # 移除"完整版[视频]"
                clean_title = clean_title.replace('完整版', '', 1)  # 移除"完整版"
                clean_title = clean_title.replace('[视频]', '', 1)  # 移除"[视频]"
                
                # 移除时间字符，如"00:02:18"或"20260110"等时间格式
                import re
                clean_title = re.sub(r'\d{2}:\d{2}:\d{2}', '', clean_title)  # 移除"00:02:18"格式
                clean_title = re.sub(r'\d{8}', '', clean_title)  # 移除"20260110"格式
                clean_title = re.sub(r'\d{4}-\d{2}-\d{2}', '', clean_title)  # 移除"2026-01-10"格式
                clean_title = clean_title.strip()  # 清理空格
                
                # 添加到新闻条目列表
                news_items.append({
                    "number": "1",
                    "title": clean_title,
                    "link": url_formats[0]
                })
            else:
                # 如果页面标题是完整版新闻联播，创建一个通用的新闻条目
                news_items.append({
                    "number": "1",
                    "title": f"{date} 新闻联播主要内容",
                    "link": url_formats[0]
                })
        
        print(f"成功提取 {len(news_items)} 条新闻条目")
        
        # 重新编号新闻条目
        for i, item in enumerate(news_items):
            item["number"] = str(i + 1)
        
        # 返回成功响应
        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "content": f"{date} 新闻联播完整内容",
                "items": news_items
            }
        })
        
    except Exception as e:
        # 发生异常，返回错误响应
        print(f"获取新闻内容失败: {e}")
        return jsonify({
            "code": 500,
            "message": "未爬取成功",
            "data": {
                "content": "",
                "items": []
            }
        })


# 获取单条新闻的详细内容
# @app.route('/news/item', methods=['GET'])
# def news_item():
    """
    获取单条新闻的详细内容
    
    :return: JSON格式的新闻详情
    """
    # 获取链接参数
    link = request.args.get('link')
    if not link:  # 检查链接参数是否存在
        return jsonify({
            "code": 400,
            "message": "缺少link参数"
        })
    
    try:
        print(f"\n=== 开始获取单条新闻内容 ===")
        
        # 获取新闻详情页
        # 增加重试机制
        max_retries = 3
        item_page = None
        for retry in range(max_retries):
            print(f"获取新闻详情页 (重试 {retry+1}/{max_retries})")
            item_page = fetch_page(link)  # 获取页面内容
            if item_page:
                break
            
            print(f"获取新闻详情页失败，等待后重试...")
            import time
            time.sleep(2)
        
        if not item_page:  # 所有重试都失败
            raise Exception("无法获取新闻详情页")
        
        # 解析新闻详情
        try:
            soup = BeautifulSoup(item_page, 'html.parser')  # 解析HTML
        except Exception as e:
            print(f"解析HTML失败: {e}")
            raise Exception("无法解析新闻详情页")
        
        # 提取新闻内容
        news_content = ""  # 初始化新闻内容
        
        # 方法1: 尝试不同的内容选择器，覆盖CCTV新闻页面的各种结构
        content_selectors = [
            # CCTV新闻常用选择器
            '.cnt_bd',
            '#content_body',
            '.article-body',
            '.content',
            '.main-content',
            '.article_content',
            '.news-content',
            '.text-content',
            '.content-article',
            '#content',
            '.detail-content',
            '.articleDetail',
            '.newsText',
            '.text',
            '.article',
            '.allcontent',  # 视频新闻的内容容器
            # 针对视频新闻的选择器
            '.video-info',
            '.video-description',
            '.video-content'
        ]
        
        for selector in content_selectors:
            try:
                content_div = soup.select_one(selector)  # 查找内容容器
                if content_div:  # 如果找到内容容器
                    temp_content = content_div.get_text(separator='\n', strip=True)  # 获取文本内容
                    # 检查是否为"加载更多"或内容过短
                    if temp_content and temp_content.strip() != "加载更多" and len(temp_content) > 50:
                        news_content = temp_content
                        break
            except Exception as e:
                print(f"使用选择器 {selector} 提取内容失败: {e}")
                continue
        
        # 方法2: 如果方法1失败，尝试从meta标签获取contentid，调用API获取内容
        if not news_content or news_content.strip() == "加载更多":
            print("尝试从meta标签获取contentid...")
            content_id_meta = soup.find('meta', attrs={'name': 'contentid'})  # 查找meta标签
            
            if content_id_meta:  # 如果找到meta标签
                content_id = content_id_meta.get('content', '')  # 获取contentid
                if content_id:  # contentid存在
                    print(f"获取到contentid: {content_id}")
                    # 尝试构造API请求获取内容
                    # CCTV新闻API通常使用类似的结构
                    api_urls = [
                        f"https://api.cctv.com/video/detail?id={content_id}",
                        f"https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid={content_id}",
                        f"https://api.cctv.com/content/article/{content_id}"
                    ]
                    
                    for api_url in api_urls:
                        try:
                            # 使用fetch_page函数获取API内容，增加重试机制
                            api_content = fetch_page(api_url)
                            if api_content:  # API请求成功
                                # 尝试解析API响应
                                try:
                                    import json
                                    api_data = json.loads(api_content)
                                    # 从API响应中提取内容
                                    if isinstance(api_data, dict):
                                        # 检查常见的内容字段
                                        content_fields = ['content', 'description', 'body', 'text', 'intro']
                                        for field in content_fields:
                                            if field in api_data and api_data[field]:
                                                news_content = str(api_data[field])
                                                break
                                except ValueError:
                                    # 如果不是JSON，尝试从HTML中提取
                                    api_soup = BeautifulSoup(api_content, 'html.parser')
                                    api_text = api_soup.get_text(separator='\n', strip=True)
                                    if api_text and len(api_text) > 50:
                                        news_content = api_text
                                        break
                        except Exception as api_e:
                            print(f"API请求失败: {api_e}")
                            continue
        
        # 方法3: 尝试查找所有p标签并拼接内容
        if not news_content or news_content.strip() == "加载更多":
            try:
                paragraphs = soup.find_all('p')  # 查找所有p标签
                if paragraphs:  # 如果找到p标签
                    p_content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    if p_content and len(p_content) > 50:
                        news_content = p_content
            except Exception as e:
                print(f"提取p标签内容失败: {e}")
        
        # 方法4: 使用通用方法提取，过滤掉过多的空白行
        if not news_content or news_content.strip() == "加载更多":
            try:
                # 使用通用方法提取，过滤掉过多的空白行
                for script in soup(['script', 'style', 'iframe', 'nav', 'header', 'footer', 'aside']):
                    script.decompose()  # 移除不需要的标签
                raw_content = soup.get_text(separator='\n', strip=True)  # 获取文本内容
                # 清理内容，移除过多的空行
                news_content = '\n'.join([line for line in raw_content.split('\n') if line.strip()])
            except Exception as e:
                print(f"通用方法提取内容失败: {e}")
        
        # 方法5: 从页面中提取视频简介
        if not news_content or news_content.strip() == "加载更多":
            print("尝试提取视频简介...")
            try:
                # 查找包含视频简介的元素
                all_content_div = soup.find('div', class_='allcontent')
                if all_content_div:  # 如果找到allcontent标签
                    # 提取所有文本，但过滤掉无效内容
                    all_text = all_content_div.get_text(separator='\n', strip=True)
                    # 清理内容，保留有意义的部分
                    lines = [line for line in all_text.split('\n') if len(line) > 10]  # 保留长度大于10的行
                    if lines:  # 如果有符合条件的行
                        news_content = '\n'.join(lines)
            except Exception as e:
                print(f"提取视频简介失败: {e}")
        
        # 方法6: 尝试从article标签提取内容
        if not news_content or news_content.strip() == "加载更多":
            print("尝试从article标签提取内容...")
            try:
                article_tag = soup.find('article')  # 查找article标签
                if article_tag:  # 如果找到article标签
                    article_content = article_tag.get_text(separator='\n', strip=True)
                    if article_content and len(article_content) > 50:
                        news_content = article_content
            except Exception as e:
                print(f"提取article标签内容失败: {e}")
        
        # 方法7: 尝试从div[id*='content']提取内容
        if not news_content or news_content.strip() == "加载更多":
            print("尝试从包含content的id标签提取内容...")
            try:
                content_div = soup.find('div', id=lambda x: x and 'content' in x.lower())  # 查找id包含content的div
                if content_div:  # 如果找到content标签
                    content = content_div.get_text(separator='\n', strip=True)
                    if content and len(content) > 50:
                        news_content = content
            except Exception as e:
                print(f"提取content id标签内容失败: {e}")
        
        # 过滤掉不需要的内容
        if news_content:  # 如果新闻内容存在
            # 定义要过滤的内容列表
            filters = [
                "央视网消息（新闻联播）：",
                "央视网消息\n（新闻联播）：",
                "央视网消息\n（新闻联播）：\n",
                "主要内容",
                "编辑：",
                "责任编辑：",
                "责任",
                "陈平丽",
                "刘亮"
            ]
            
            # 执行过滤
            filtered_content = news_content
            for filter_text in filters:
                filtered_content = filtered_content.replace(filter_text, "")  # 替换过滤文本为空格
            
            # 清理多余的空行和空白字符
            lines = [line for line in filtered_content.split("\n") if line.strip()]  # 过滤掉空行
            filtered_content = "\n".join(lines)  # 重新拼接
            
            # 最终清理：移除行尾的多余字符
            final_lines = []
            for line in filtered_content.split("\n"):
                # 移除行尾的空白字符和可能的残留字符
                cleaned_line = line.strip()
                if cleaned_line:  # 只保留非空行
                    final_lines.append(cleaned_line)
            
            # 去掉最后面的作者信息
            # 查找常见的作者标识行
            author_patterns = [
                r'^编辑：',
                r'^责任编辑：',
                r'^文\s*/\s*',
                r'^图\s*/\s*',
                r'^摄影\s*：',
                r'^记者\s*：',
                r'^\s*作者\s*：',
                r'^\s*\w+\s*\w+$'  # 匹配可能的作者姓名行
            ]
            
            # 从后往前检查，移除作者相关行
            import re
            cleaned_final_lines = []
            for line in reversed(final_lines):
                is_author_line = False  # 标记是否为作者行
                for pattern in author_patterns:
                    if re.match(pattern, line):  # 检查是否匹配作者模式
                        is_author_line = True
                        break
                if is_author_line:
                    continue  # 跳过作者行
                # 检查是否为简单的中文姓名（2-4个汉字）
                if re.match(r'^[\u4e00-\u9fa5]{2,4}$', line):
                    continue  # 跳过简单中文姓名行
                cleaned_final_lines.append(line)
            
            # 反转回来，恢复正常顺序
            cleaned_final_lines.reverse()
            
            # 如果清理后没有内容，保留原始内容
            if cleaned_final_lines:
                news_content = "\n".join(cleaned_final_lines)
            else:
                news_content = "\n".join(final_lines)
            
            # 过滤正文中最后一个句号后的人名（编辑姓名）
            # 查找最后一个句号的位置
            last_period_index = news_content.rfind('。')
            if last_period_index != -1:
                # 获取最后一个句号后的内容
                content_after_last_period = news_content[last_period_index + 1:].strip()
                
                # 检查最后一个句号后的内容是否为中文姓名（2-4个汉字）
                import re
                if re.match(r'^[\u4e00-\u9fa5]{2,4}$', content_after_last_period):
                    # 如果是中文姓名，移除最后一个句号后的内容
                    news_content = news_content[:last_period_index + 1].strip()
                # 也处理英文句号的情况
                last_dot_index = news_content.rfind('.')
                if last_dot_index != -1:
                    content_after_last_dot = news_content[last_dot_index + 1:].strip()
                    if re.match(r'^[\u4e00-\u9fa5]{2,4}$', content_after_last_dot):
                        news_content = news_content[:last_dot_index + 1].strip()
        
        if not news_content:  # 新闻内容为空
            raise Exception("无法提取新闻内容")
        
        print(f"成功提取单条新闻内容")
        
        # 返回成功响应
        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "content": news_content,
                "link": link
            }
        })
        
    except Exception as e:
        # 发生异常，返回错误响应
        print(f"获取单条新闻内容失败: {e}")
        return jsonify({
            "code": 500,
            "message": "未爬取成功",
            "data": {
                "content": "",
                "link": link
            }
        })


# 从数据库获取指定日期的新闻列表
@app.route('/db/news_list', methods=['GET'])
def db_news_list():
    """
    从数据库获取指定日期的新闻列表
    
    :return: JSON格式的新闻列表
    """
    # 获取日期参数
    date = request.args.get('date')
    if not date:  # 检查日期参数是否存在
        return jsonify({
            "code": 400,
            "message": "缺少date参数"
        })
    
    print(f"收到请求：/db/news_list?date={date}")
    
    try:
        conn = get_db_connection()  # 获取数据库连接
        if not conn:  # 连接失败
            print(f"数据库连接失败")
            return jsonify({
                "code": 500,
                "message": "数据库连接失败"
            })
        
        cursor = conn.cursor()  # 获取游标
        
        # 查询指定日期的新闻
        query = """
        SELECT id, date, title, item_number, link
        FROM `news_联播` 
        WHERE date = ? 
        ORDER BY CAST(SUBSTRING(item_number, '/', 1) AS INTEGER) ASC
        """
        
        print(f"执行查询: {query}，参数: {date}")
        cursor.execute(query, (date,))  # 执行查询
        news_rows = cursor.fetchall()  # 获取查询结果
        
        print(f"查询结果: {len(news_rows)} 条新闻")
        
        # 将Row对象转换为字典列表
        news_items = []
        for row in news_rows:
            news_items.append(dict(row))  # 转换为字典
        
        cursor.close()  # 关闭游标
        conn.close()  # 关闭连接
        
        # 返回成功响应
        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "date": date,
                "items": news_items
            }
        })
        
    except Exception as e:  # 发生异常
        print(f"从数据库获取新闻列表失败: {e}")
        import traceback
        traceback.print_exc()  # 打印堆栈信息
        return jsonify({
            "code": 500,
            "message": f"从数据库获取新闻列表失败: {str(e)}",
            "data": {
                "date": date,
                "items": []
            }
        })


# 从数据库获取单条新闻详情
@app.route('/db/news_detail', methods=['GET'])
def db_news_detail():
    """
    从数据库获取单条新闻详情
    
    :return: JSON格式的新闻详情
    """
    # 获取新闻ID参数
    news_id = request.args.get('id')
    if not news_id:  # 检查ID参数是否存在
        return jsonify({
            "code": 400,
            "message": "缺少id参数"
        })
    
    try:
        conn = get_db_connection()  # 获取数据库连接
        if not conn:  # 连接失败
            return jsonify({
                "code": 500,
                "message": "数据库连接失败"
            })
        
        cursor = conn.cursor()  # 获取游标
        
        # 查询指定ID的新闻
        query = """
        SELECT id, date, title, content, item_number
        FROM `news_联播` 
        WHERE id = ?
        """
        
        cursor.execute(query, (news_id,))  # 执行查询
        news_row = cursor.fetchone()  # 获取查询结果
        
        cursor.close()  # 关闭游标
        conn.close()  # 关闭连接
        
        if not news_row:  # 新闻不存在
            return jsonify({
                "code": 404,
                "message": "新闻不存在"
            })
        
        # 将Row对象转换为字典
        news_item = dict(news_row)
        
        # 返回成功响应
        return jsonify({
            "code": 200,
            "message": "success",
            "data": news_item
        })
        
    except Exception as e:  # 发生异常
        print(f"从数据库获取新闻详情失败: {e}")
        return jsonify({
            "code": 500,
            "message": f"从数据库获取新闻详情失败: {str(e)}",
            "data": {}
        })


# 主函数
if __name__ == '__main__':
    # 启动Flask应用，使用配置文件中的参数
    app.run(
        host=config['backend']['host'],
        port=config['backend']['port'],
        debug=config['backend']['debug']
    )
# 添加WSGI入口，供Gunicorn使用
wsgi_app = app