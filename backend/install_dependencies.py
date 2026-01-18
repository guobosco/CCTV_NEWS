#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖安装脚本
用于自动安装项目所需的所有依赖
"""

import subprocess
import sys
import os


def check_python_version():
    """
    检查Python版本是否符合要求
    
    :return: bool 是否符合要求
    """
    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 8:
        print("✓ Python版本符合要求 (≥ 3.8)")
        return True
    else:
        print("✗ Python版本过低，需要Python 3.8或更高版本")
        return False


def install_pip():
    """
    安装或升级pip
    
    :return: bool 是否安装成功
    """
    try:
        # 检查pip是否已安装
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True, text=True)
        print("✓ pip已安装，正在升级...")
        # 升级pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True)
        print("✓ pip已升级到最新版本")
        return True
    except subprocess.CalledProcessError:
        print("✗ pip未安装，正在安装...")
        # 安装pip
        try:
            from ensurepip import bootstrap
            bootstrap()
            print("✓ pip安装成功")
            return True
        except Exception as e:
            print(f"✗ pip安装失败: {e}")
            return False


def install_dependencies(requirements_file):
    """
    从requirements.txt文件安装依赖
    
    :param requirements_file: requirements.txt文件路径
    :return: bool 是否安装成功
    """
    try:
        print(f"正在从 {requirements_file} 安装依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                      check=True)
        print("✓ 所有依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败: {e}")
        return False


def main():
    """
    主函数
    """
    print("=== 依赖安装脚本 ===")
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装或升级pip
    if not install_pip():
        sys.exit(1)
    
    # 获取requirements.txt文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(current_dir, "requirements.txt")
    
    # 检查requirements.txt文件是否存在
    if not os.path.exists(requirements_file):
        print(f"✗ 未找到requirements.txt文件: {requirements_file}")
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies(requirements_file):
        sys.exit(1)
    
    print("\n=== 安装完成 ===")
    print("所有依赖已成功安装，可以开始运行项目了！")
    
    # 显示下一步操作建议
    print("\n下一步操作建议:")
    print("1. 修改config.yaml配置文件，设置您的服务器IP、端口等参数")
    print("2. 启动后端服务: python backend.py")
    print("3. 运行定时爬虫: python scheduled_spider.py")


if __name__ == "__main__":
    main()
