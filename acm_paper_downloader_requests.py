#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACM Digital Library 论文自动下载器 (requests版本)
适用于校园网环境，无需ChromeDriver

安装依赖:
pip install pandas openpyxl requests beautifulsoup4 lxml

使用方法:
python acm_paper_downloader_requests.py papers.xlsx
"""

import os
import sys
import time
import re
import random
import pandas as pd
import requests
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ACMPaperDownloaderRequests:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.output_dir = "downloaded_papers"
        self.base_url = "https://dl.acm.org/search/search-results?q="
        self.session = None
        self.setup_session()
        
    def setup_session(self):
        """设置requests会话，包含重试策略和请求头"""
        self.session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置请求头，模拟真实浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        })
        
        print("网络会话初始化成功")
    
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
            
            # 添加Referer头，模拟从ACM主页访问
            headers = {
                'Referer': 'https://dl.acm.org/',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            # 发送搜索请求
            response = self.session.get(search_url, headers=headers, timeout=30)
            
            # 检查响应状态
            if response.status_code == 403:
                print(f"访问被拒绝(403)，可能触发了反爬虫机制，建议增加延时")
                return None
            
            response.raise_for_status()
            
            # 随机等待，模拟人类行为（增加延时以避免403错误）
            wait_time = random.randint(8, 15)
            print(f"页面加载等待{wait_time}秒...")
            time.sleep(wait_time)
            
            # 解析搜索结果页面
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找第一个搜索结果链接
            # 尝试多种可能的选择器
            selectors = [
                '.issue-item__title a',
                '.search__item .hlFld-Title a',
                '.issue-item-title a',
                '.search-result-title a',
                'h5 a[href*="/doi/"]',
                'a[href*="/doi/"]'
            ]
            
            first_result_link = None
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    first_result_link = links[0].get('href')
                    break
            
            if first_result_link:
                # 确保链接是完整的URL
                if first_result_link.startswith('/'):
                    first_result_link = 'https://dl.acm.org' + first_result_link
                
                print(f"找到第一个搜索结果: {first_result_link}")
                return first_result_link
            else:
                print(f"未找到论文: {title}")
                return None
                
        except Exception as e:
            print(f"搜索论文时出错: {e}")
            return None
    
    def get_pdf_link(self, paper_url):
        """从论文详情页获取PDF下载链接"""
        try:
            # 添加Referer头
            headers = {
                'Referer': 'https://dl.acm.org/search/search-results',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            response = self.session.get(paper_url, headers=headers, timeout=30)
            
            if response.status_code == 403:
                print(f"访问论文详情页被拒绝(403)")
                return None
                
            response.raise_for_status()
            
            # 随机等待（增加延时）
            wait_time = random.randint(5, 10)
            print(f"详情页加载等待{wait_time}秒...")
            time.sleep(wait_time)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 尝试多种可能的PDF链接选择器
            pdf_selectors = [
                'a[href*=".pdf"]',
                'a[title*="PDF"]',
                'a[aria-label*="PDF"]',
                '.pdf-link',
                '.download-pdf',
                '.btn--pdf',
                'a[href*="pdf"]',
                'a[data-title*="PDF"]'
            ]
            
            for selector in pdf_selectors:
                pdf_links = soup.select(selector)
                if pdf_links:
                    pdf_url = pdf_links[0].get('href')
                    if pdf_url:
                        # 确保链接是完整的URL
                        if pdf_url.startswith('/'):
                            pdf_url = urljoin(paper_url, pdf_url)
                        print(f"找到PDF链接: {pdf_url}")
                        return pdf_url
            
            print("未找到PDF下载链接")
            return None
            
        except Exception as e:
            print(f"获取PDF链接时出错: {e}")
            return None
    
    def download_pdf(self, pdf_url, filename):
        """下载PDF文件"""
        try:
            print(f"开始下载PDF: {filename}")
            
            # 发送下载请求
            response = self.session.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # 检查响应内容类型
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application/octet-stream' not in content_type:
                print(f"警告: 响应内容类型不是PDF: {content_type}")
            
            # 保存文件
            file_path = os.path.join(self.output_dir, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size < 1024:  # 小于1KB可能是错误页面
                print(f"警告: 下载的文件很小 ({file_size} bytes)，可能不是有效的PDF")
                return False
            
            print(f"成功下载并保存为: {filename} ({file_size} bytes)")
            return True
            
        except Exception as e:
            print(f"下载PDF时出错: {e}")
            return False
    
    def process_papers(self):
        """处理所有论文"""
        titles = self.read_excel_file()
        if not titles:
            return
        
        self.create_output_directory()
        
        successful_downloads = 0
        failed_downloads = 0
        
        try:
            for i, title in enumerate(titles, 1):
                print(f"\n[{i}/{len(titles)}] 正在处理: {title}")
                
                # 搜索论文
                paper_url = self.search_paper(title)
                if paper_url:
                    # 获取PDF链接
                    pdf_url = self.get_pdf_link(paper_url)
                    if pdf_url:
                        # 下载PDF
                        filename = self.sanitize_filename(title)
                        if self.download_pdf(pdf_url, filename):
                            successful_downloads += 1
                        else:
                            failed_downloads += 1
                            print(f"无法下载（可能需要付费）: {title}")
                    else:
                        failed_downloads += 1
                        print(f"无法下载（可能需要付费）: {title}")
                else:
                    failed_downloads += 1
                
                # 网络礼仪：随机等待20-40秒，避免被封IP（增加延时以应对403错误）
                if i < len(titles):  # 最后一个不需要等待
                    wait_time = random.randint(20, 40)
                    print(f"等待{wait_time}秒...")
                    time.sleep(wait_time)
                
        finally:
            print(f"\n下载完成统计:")
            print(f"成功下载: {successful_downloads} 篇")
            print(f"下载失败: {failed_downloads} 篇")
            print(f"总计处理: {len(titles)} 篇")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python acm_paper_downloader_requests.py <excel_file_path>")
        print("示例: python acm_paper_downloader_requests.py papers.xlsx")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    if not os.path.exists(excel_file):
        print(f"错误: 文件 '{excel_file}' 不存在")
        sys.exit(1)
    
    downloader = ACMPaperDownloaderRequests(excel_file)
    downloader.process_papers()


if __name__ == "__main__":
    main()