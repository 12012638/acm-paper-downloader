#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACM Digital Library 论文自动下载器

安装依赖:
pip install pandas openpyxl selenium requests

还需要安装Chrome浏览器和ChromeDriver:
1. 安装Chrome浏览器
2. 下载ChromeDriver: https://chromedriver.chromium.org/
3. 将ChromeDriver放到PATH中或指定路径

使用方法:
python acm_paper_downloader.py papers.xlsx
"""

import os
import sys
import time
import re
import random
import pandas as pd
import requests
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class ACMPaperDownloader:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.output_dir = "downloaded_papers"
        self.base_url = "https://dl.acm.org/search/search-results?q="
        self.driver = None
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        # 设置下载目录
        prefs = {
            "download.default_directory": os.path.abspath(self.output_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 可选：无头模式（不显示浏览器窗口）
        # chrome_options.add_argument("--headless")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("浏览器驱动初始化成功")
        except Exception as e:
            print(f"浏览器驱动初始化失败: {e}")
            print("请确保已安装Chrome浏览器和ChromeDriver")
            sys.exit(1)
    
    def create_output_directory(self):
        """创建输出目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"创建输出目录: {self.output_dir}")
        else:
            print(f"输出目录已存在: {self.output_dir}")
    
    def read_excel_file(self):
        """读取Excel文件中的论文标题"""
        try:
            df = pd.read_excel(self.excel_file_path)
            if 'Title' not in df.columns:
                print("错误: Excel文件中未找到'Title'列")
                return []
            
            titles = df['Title'].dropna().tolist()
            print(f"成功读取 {len(titles)} 个论文标题")
            return titles
        except Exception as e:
            print(f"读取Excel文件失败: {e}")
            return []
    
    def sanitize_filename(self, title):
        """净化文件名，移除非法字符"""
        # 移除或替换非法字符
        illegal_chars = r'[\\/:*?"<>|]'
        sanitized = re.sub(illegal_chars, '_', title)
        # 限制文件名长度
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        return sanitized + ".pdf"
    
    def search_paper(self, title):
        """在ACM网站搜索论文"""
        try:
            # 构建搜索URL
            search_url = self.base_url + quote(title)
            print(f"搜索URL: {search_url}")
            
            self.driver.get(search_url)
            # 页面加载后随机等待3-6秒
            page_wait = random.randint(3, 6)
            time.sleep(page_wait)
            
            # 等待搜索结果加载
            wait = WebDriverWait(self.driver, 15)
            
            # 查找搜索结果
            try:
                # 尝试找到第一个搜索结果链接
                first_result = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".issue-item__title a, .search__item .hlFld-Title a"))
                )
                
                result_url = first_result.get_attribute('href')
                print(f"找到第一个搜索结果: {result_url}")
                
                # 点击进入论文详情页
                first_result.click()
                # 详情页加载等待3-5秒
                detail_wait = random.randint(3, 5)
                time.sleep(detail_wait)
                
                return True
                
            except TimeoutException:
                print(f"未找到论文: {title}")
                return False
                
        except Exception as e:
            print(f"搜索论文时出错: {e}")
            return False
    
    def download_pdf(self, title):
        """下载PDF文件"""
        try:
            wait = WebDriverWait(self.driver, 15)
            
            # 尝试多种可能的PDF下载链接选择器
            pdf_selectors = [
                "a[href*='.pdf']",
                ".pdf-link",
                ".download-pdf",
                "a[title*='PDF']",
                "a[aria-label*='PDF']",
                ".btn--pdf",
                "a[href*='pdf']"
            ]
            
            pdf_link = None
            for selector in pdf_selectors:
                try:
                    pdf_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if pdf_elements:
                        pdf_link = pdf_elements[0]
                        break
                except:
                    continue
            
            if pdf_link:
                pdf_url = pdf_link.get_attribute('href')
                print(f"找到PDF链接: {pdf_url}")
                
                # 点击下载链接
                pdf_link.click()
                # 等待下载开始，随机等待5-8秒
                download_wait = random.randint(5, 8)
                time.sleep(download_wait)
                
                # 生成文件名
                filename = self.sanitize_filename(title)
                print(f"成功下载并保存为: {filename}")
                
                return True
            else:
                print(f"无法下载（可能需要付费）: {title}")
                return False
                
        except Exception as e:
            print(f"下载PDF时出错: {e}")
            print(f"无法下载（可能需要付费）: {title}")
            return False
    
    def process_papers(self):
        """处理所有论文"""
        titles = self.read_excel_file()
        if not titles:
            return
        
        self.create_output_directory()
        self.setup_driver()
        
        successful_downloads = 0
        failed_downloads = 0
        
        try:
            for i, title in enumerate(titles, 1):
                print(f"\n[{i}/{len(titles)}] 正在处理: {title}")
                
                # 搜索论文
                if self.search_paper(title):
                    # 尝试下载PDF
                    if self.download_pdf(title):
                        successful_downloads += 1
                    else:
                        failed_downloads += 1
                else:
                    failed_downloads += 1
                
                # 网络礼仪：随机等待10-20秒，避免被封IP
                wait_time = random.randint(10, 20)
                print(f"等待{wait_time}秒...")
                time.sleep(wait_time)
                
        finally:
            if self.driver:
                self.driver.quit()
                print("\n浏览器已关闭")
            
            print(f"\n下载完成统计:")
            print(f"成功下载: {successful_downloads} 篇")
            print(f"下载失败: {failed_downloads} 篇")
            print(f"总计处理: {len(titles)} 篇")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python acm_paper_downloader.py <excel_file_path>")
        print("示例: python acm_paper_downloader.py papers.xlsx")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    if not os.path.exists(excel_file):
        print(f"错误: 文件 '{excel_file}' 不存在")
        sys.exit(1)
    
    downloader = ACMPaperDownloader(excel_file)
    downloader.process_papers()


if __name__ == "__main__":
    main()