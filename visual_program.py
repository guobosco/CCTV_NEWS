#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻联播爬虫可视化管理程序
功能：
1. 自动执行backend后台服务，并显示服务状态
2. 执行定时执行新闻联播爬虫程序，并显示服务状态
3. 显示数据库文件的大小
界面尺寸：1080×800
"""

import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter.messagebox import showinfo, showerror, askyesno
import threading
import psutil
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('visual_program.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsSpiderVisualApp:
    def __init__(self):
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title("新闻联播爬虫管理系统")
        self.root.geometry("1080x800")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)
        
        # 设置淡蓝色背景
        self.root.configure(bg="#E6F3FF")
        
        # 配置ttk样式，使其与淡蓝色背景匹配
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#E6F3FF")
        self.style.configure("TLabelFrame", background="#E6F3FF")
        self.style.configure("TLabel", background="#E6F3FF")
        self.style.configure("TButton", background="#E6F3FF")
        self.style.configure("TCombobox", background="#E6F3FF")
        self.style.configure("TNotebook", background="#E6F3FF")
        self.style.configure("TNotebook.Tab", background="#E6F3FF")
        self.style.configure("Vertical.TScrollbar", background="#E6F3FF")
        self.style.configure("Horizontal.TScrollbar", background="#E6F3FF")
        
        # 设置跨平台字体
        self.default_font = ('Arial', 10)
        self.title_font = ('Arial', 12, 'bold')
        
        # 程序状态
        self.backend_process = None
        self.spider_process = None
        self.is_running = True
        
        # 获取当前可执行文件或脚本所在目录
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            current_dir = os.path.dirname(sys.executable)
            # 查找Python解释器
            import shutil
            # 先从PATH中查找python.exe
            self.python_path = shutil.which('python.exe') or shutil.which('python')
            if not self.python_path:
                # 如果找不到，使用默认安装路径（使用原始字符串或双反斜杠）
                self.python_path = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
        else:
            # 开发环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.python_path = sys.executable
        
        # 数据库相关 - 跨平台路径
        self.db_path = os.path.join(current_dir, "backend", "news.db")
        
        # 文件路径 - 跨平台路径
        self.backend_script = os.path.join(current_dir, "backend", "backend.py")
        self.spider_script = os.path.join(current_dir, "backend", "scheduled_spider.py")
        
        # 初始化界面
        self.create_widgets()
        
        # 启动自动检查
        self.check_files()
        self.start_autostart()
        
        # 启动数据库监控
        self.start_db_monitor()
        
        # 主循环
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def create_widgets(self):
        """创建界面控件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="新闻联播爬虫管理系统", font=('微软雅黑', 16, 'bold'))
        title_label.pack(pady=10)
        
        # 内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 设置网格布局权重
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # 左侧服务控制区域
        left_frame = ttk.LabelFrame(content_frame, text="服务管理", padding="10")
        left_frame.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="nsew")
        
        # 右侧状态信息区域
        right_frame = ttk.LabelFrame(content_frame, text="状态信息", padding="10")
        right_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(content_frame, text="运行日志", padding="10")
        log_frame.grid(row=1, column=1, padx=(10, 0), pady=(10, 0), sticky="nsew")
        
        # 服务控制区域内容
        self.create_service_controls(left_frame)
        
        # 状态信息区域内容
        self.create_status_info(right_frame)
        
        # 日志显示区域内容
        self.create_log_display(log_frame)
    
    def create_service_controls(self, parent):
        """创建服务控制控件"""
        # Backend服务控件
        backend_frame = ttk.LabelFrame(parent, text="Backend服务", padding="10")
        backend_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.backend_status_var = tk.StringVar(value="未启动")
        backend_status = ttk.Label(backend_frame, text="状态:", font=self.default_font)
        backend_status.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.backend_status_label = ttk.Label(backend_frame, textvariable=self.backend_status_var, font=self.default_font)
        self.backend_status_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        backend_buttons_frame = ttk.Frame(backend_frame)
        backend_buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.backend_start_btn = ttk.Button(backend_buttons_frame, text="启动", command=self.start_backend)
        self.backend_start_btn.pack(side=tk.LEFT, padx=5)
        
        self.backend_stop_btn = ttk.Button(backend_buttons_frame, text="停止", command=self.stop_backend, state=tk.DISABLED)
        self.backend_stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.backend_restart_btn = ttk.Button(backend_buttons_frame, text="重启", command=self.restart_backend, state=tk.DISABLED)
        self.backend_restart_btn.pack(side=tk.LEFT, padx=5)
        
        # 定时爬虫控件
        spider_frame = ttk.LabelFrame(parent, text="定时爬虫", padding="10")
        spider_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.spider_status_var = tk.StringVar(value="未启动")
        spider_status = ttk.Label(spider_frame, text="状态:", font=self.default_font)
        spider_status.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.spider_status_label = ttk.Label(spider_frame, textvariable=self.spider_status_var, font=self.default_font)
        self.spider_status_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        spider_buttons_frame = ttk.Frame(spider_frame)
        spider_buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.spider_start_btn = ttk.Button(spider_buttons_frame, text="启动", command=self.start_spider)
        self.spider_start_btn.pack(side=tk.LEFT, padx=5)
        
        self.spider_stop_btn = ttk.Button(spider_buttons_frame, text="停止", command=self.stop_spider, state=tk.DISABLED)
        self.spider_stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.spider_restart_btn = ttk.Button(spider_buttons_frame, text="重启", command=self.restart_spider, state=tk.DISABLED)
        self.spider_restart_btn.pack(side=tk.LEFT, padx=5)
    
    def create_status_info(self, parent):
        """创建状态信息控件"""
        # 数据库信息
        db_frame = ttk.LabelFrame(parent, text="数据库信息", padding="10")
        db_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.db_size_var = tk.StringVar(value="0 KB")
        db_size_label = ttk.Label(db_frame, text="数据库大小:", font=self.default_font)
        db_size_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        db_size_value = ttk.Label(db_frame, textvariable=self.db_size_var, font=self.default_font, foreground="#0066CC")
        db_size_value.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        db_refresh_btn = ttk.Button(db_frame, text="刷新", command=self.update_db_size)
        db_refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        
        db_path_label = ttk.Label(db_frame, text="数据库路径:", font=self.default_font)
        db_path_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        db_path_value = ttk.Label(db_frame, text=self.db_path, font=self.default_font, wraplength=400)
        db_path_value.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # 服务信息
        service_info_frame = ttk.LabelFrame(parent, text="服务信息", padding="10")
        service_info_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.backend_pid_var = tk.StringVar(value="未运行")
        backend_pid_label = ttk.Label(service_info_frame, text="Backend PID:", font=self.default_font)
        backend_pid_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        backend_pid_value = ttk.Label(service_info_frame, textvariable=self.backend_pid_var, font=self.default_font)
        backend_pid_value.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.spider_pid_var = tk.StringVar(value="未运行")
        spider_pid_label = ttk.Label(service_info_frame, text="爬虫PID:", font=self.default_font)
        spider_pid_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        spider_pid_value = ttk.Label(service_info_frame, textvariable=self.spider_pid_var, font=self.default_font)
        spider_pid_value.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
    
    def create_log_display(self, parent):
        """创建日志显示控件"""
        # 日志文本框，设置淡蓝色背景
        self.log_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, font=('Consolas', 9), bg="#E6F3FF")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 日志控制
        log_control_frame = ttk.Frame(parent)
        log_control_frame.pack(fill=tk.X)
        
        clear_log_btn = ttk.Button(log_control_frame, text="清空日志", command=self.clear_log)
        clear_log_btn.pack(side=tk.RIGHT, padx=5)
        
        log_level_label = ttk.Label(log_control_frame, text="日志级别:")
        log_level_label.pack(side=tk.LEFT, padx=5)
        
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(log_control_frame, textvariable=self.log_level_var, values=["DEBUG", "INFO", "WARNING", "ERROR"], width=10)
        log_level_combo.pack(side=tk.LEFT, padx=5)
    
    def check_files(self):
        """检查必要文件是否存在"""
        files_to_check = [
            (self.python_path, "Python解释器"),
            (self.backend_script, "Backend脚本"),
            (self.spider_script, "爬虫脚本")
        ]
        
        for file_path, file_name in files_to_check:
            if os.path.exists(file_path):
                self.log(f"✅ {file_name} 存在", "INFO")
            else:
                self.log(f"❌ {file_name} 不存在: {file_path}", "ERROR")
    
    def start_autostart(self):
        """启动自动启动流程"""
        # 启动Backend服务
        self.start_backend()
        
        # 延迟启动爬虫
        self.root.after(3000, self.start_spider)
    
    def start_backend(self):
        """启动Backend服务"""
        if self.backend_process and self.is_process_running(self.backend_process):
            self.log("Backend服务已经在运行中", "WARNING")
            return
        
        try:
            self.log("正在启动Backend服务...", "INFO")
            
            # 确保backend脚本存在
            if not os.path.exists(self.backend_script):
                self.log(f"Backend脚本不存在: {self.backend_script}", "ERROR")
                self.update_backend_status("启动失败")
                return
            
            # 获取backend脚本所在目录
            backend_dir = os.path.dirname(self.backend_script)
            
            self.backend_process = subprocess.Popen(
                [self.python_path, self.backend_script],
                cwd=backend_dir if os.path.exists(backend_dir) else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            self.log(f"Backend服务启动成功，PID: {self.backend_process.pid}", "INFO")
            self.update_backend_status("运行中")
            self.update_backend_pid(str(self.backend_process.pid))
            self.update_backend_buttons(True)
        except Exception as e:
            self.log(f"Backend服务启动失败: {str(e)}", "ERROR")
            self.log(f"Backend脚本路径: {self.backend_script}", "DEBUG")
            self.log(f"Backend目录: {os.path.dirname(self.backend_script)}", "DEBUG")
            self.update_backend_status("启动失败")
    
    def stop_backend(self):
        """停止Backend服务"""
        if not self.backend_process or not self.is_process_running(self.backend_process):
            self.log("Backend服务未在运行中", "WARNING")
            return
        
        try:
            self.log(f"正在停止Backend服务，PID: {self.backend_process.pid}...", "INFO")
            self.backend_process.terminate()
            self.backend_process.wait(timeout=5)
            self.log("Backend服务已停止", "INFO")
            self.update_backend_status("已停止")
            self.update_backend_pid("未运行")
            self.update_backend_buttons(False)
        except Exception as e:
            self.log(f"Backend服务停止失败: {str(e)}", "ERROR")
    
    def restart_backend(self):
        """重启Backend服务"""
        self.stop_backend()
        self.root.after(1000, self.start_backend)
    
    def start_spider(self):
        """启动定时爬虫"""
        if self.spider_process and self.is_process_running(self.spider_process):
            self.log("定时爬虫已经在运行中", "WARNING")
            return
        
        try:
            self.log("正在启动定时爬虫...", "INFO")
            
            # 确保spider脚本存在
            if not os.path.exists(self.spider_script):
                self.log(f"定时爬虫脚本不存在: {self.spider_script}", "ERROR")
                self.update_spider_status("启动失败")
                return
            
            # 获取spider脚本所在目录
            spider_dir = os.path.dirname(self.spider_script)
            
            self.spider_process = subprocess.Popen(
                [self.python_path, self.spider_script],
                cwd=spider_dir if os.path.exists(spider_dir) else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            self.log(f"定时爬虫启动成功，PID: {self.spider_process.pid}", "INFO")
            self.update_spider_status("运行中")
            self.update_spider_pid(str(self.spider_process.pid))
            self.update_spider_buttons(True)
        except Exception as e:
            self.log(f"定时爬虫启动失败: {str(e)}", "ERROR")
            self.log(f"定时爬虫脚本路径: {self.spider_script}", "DEBUG")
            self.log(f"定时爬虫目录: {os.path.dirname(self.spider_script)}", "DEBUG")
            self.update_spider_status("启动失败")
    
    def stop_spider(self):
        """停止定时爬虫"""
        if not self.spider_process or not self.is_process_running(self.spider_process):
            self.log("定时爬虫未在运行中", "WARNING")
            return
        
        try:
            self.log(f"正在停止定时爬虫，PID: {self.spider_process.pid}...", "INFO")
            self.spider_process.terminate()
            self.spider_process.wait(timeout=5)
            self.log("定时爬虫已停止", "INFO")
            self.update_spider_status("已停止")
            self.update_spider_pid("未运行")
            self.update_spider_buttons(False)
        except Exception as e:
            self.log(f"定时爬虫停止失败: {str(e)}", "ERROR")
    
    def restart_spider(self):
        """重启定时爬虫"""
        self.stop_spider()
        self.root.after(1000, self.start_spider)
    
    def update_backend_status(self, status):
        """更新Backend服务状态"""
        self.backend_status_var.set(status)
        
        # 更新状态颜色
        if status == "运行中":
            self.backend_status_label.config(foreground="#009900")
        elif status == "已停止":
            self.backend_status_label.config(foreground="#666666")
        else:
            self.backend_status_label.config(foreground="#CC0000")
    
    def update_spider_status(self, status):
        """更新爬虫状态"""
        self.spider_status_var.set(status)
        
        # 更新状态颜色
        if status == "运行中":
            self.spider_status_label.config(foreground="#009900")
        elif status == "已停止":
            self.spider_status_label.config(foreground="#666666")
        else:
            self.spider_status_label.config(foreground="#CC0000")
    
    def update_backend_pid(self, pid):
        """更新Backend PID"""
        self.backend_pid_var.set(pid)
    
    def update_spider_pid(self, pid):
        """更新爬虫PID"""
        self.spider_pid_var.set(pid)
    
    def update_backend_buttons(self, running):
        """更新Backend按钮状态"""
        if running:
            self.backend_start_btn.config(state=tk.DISABLED)
            self.backend_stop_btn.config(state=tk.NORMAL)
            self.backend_restart_btn.config(state=tk.NORMAL)
        else:
            self.backend_start_btn.config(state=tk.NORMAL)
            self.backend_stop_btn.config(state=tk.DISABLED)
            self.backend_restart_btn.config(state=tk.DISABLED)
    
    def update_spider_buttons(self, running):
        """更新爬虫按钮状态"""
        if running:
            self.spider_start_btn.config(state=tk.DISABLED)
            self.spider_stop_btn.config(state=tk.NORMAL)
            self.spider_restart_btn.config(state=tk.NORMAL)
        else:
            self.spider_start_btn.config(state=tk.NORMAL)
            self.spider_stop_btn.config(state=tk.DISABLED)
            self.spider_restart_btn.config(state=tk.DISABLED)
    
    def start_db_monitor(self):
        """启动数据库监控"""
        self.update_db_size()
        self.root.after(10000, self.start_db_monitor)  # 每10秒更新一次
    
    def update_db_size(self):
        """更新数据库大小"""
        try:
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                size_kb = size_bytes / 1024
                size_mb = size_kb / 1024
                
                if size_mb > 1:
                    size_str = f"{size_mb:.2f} MB"
                else:
                    size_str = f"{size_kb:.2f} KB"
                
                self.db_size_var.set(size_str)
                self.log(f"数据库大小更新: {size_str}", "DEBUG")
            else:
                self.db_size_var.set("数据库不存在")
        except Exception as e:
            self.log(f"更新数据库大小失败: {str(e)}", "ERROR")
    
    def is_process_running(self, process):
        """检查进程是否在运行"""
        try:
            return psutil.pid_exists(process.pid) and psutil.Process(process.pid).status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # 输出到控制台
        print(log_entry.strip())
        
        # 输出到日志文本框
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 输出到文件
        logging.info(message)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清空", "INFO")
    
    def on_closing(self):
        """关闭窗口时的处理"""
        if askyesno("退出", "确定要退出程序吗？"):
            self.is_running = False
            
            # 停止服务
            self.stop_backend()
            self.stop_spider()
            
            # 关闭窗口
            self.root.destroy()

if __name__ == "__main__":
    app = NewsSpiderVisualApp()