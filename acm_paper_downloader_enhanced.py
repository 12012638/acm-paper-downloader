#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACM Digital Library 论文自动下载器 (增强版)
专门应对反爬虫机制，适用于严格的网络环境

安装依赖:
pip install pandas openpyxl requests beautifulsoup4 lxml fake-useragent

使用方法:
python acm_paper_downloader_enhanced.py papers.xlsx
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
try:
    from fake_useragent import UserAgent
    HAS_FAKE_UA = True
except ImportError:
    HAS_FAKE_UA = False
    print("提示: 安装 fake-useragent 可以获得更好的反爬虫效果: pip install fake-useragent")


class ACMPaperDownloaderEnhanced:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.output_dir = "downloaded_papers"
        self.base_url = "https://dl.acm.org/search/search-results?q="
        self.session = None
        self.ua = UserAgent() if HAS_FAKE_UA else None
        self.setup_session()
        
    def get_random_user_agent(self):
        """获取随机User-Agent"""
        if self.ua:
            try:
                return self.ua.random
            except:
                pass
        
        # 备用User-Agent列表
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)
        
    def setup_session(self):
        """设置requests会话，包含重试策略和请求头"""
        self.session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[403, 429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置基础请求头
        self.update_headers()
        
        print("增强版网络会话初始化成功")
    
    def update_headers(self):
        """更新请求头，使用随机User-Agent"""
        self.session.headers.update({
            'User-Agent': self.get_random_user_agent(),
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
    
    def visit_homepage_first(self):
        """首先访问ACM主页，建立会话"""
        try:
            print("正在访问ACM主页建立会话...")
            response = self.session.get('https://dl.acm.org/', timeout=30)
            if response.status_code == 200:
                print("成功访问ACM主页")
                # 随机等待
                wait_time = random.randint(3, 8)
                time.sleep(wait_time)
                return True
            else:
                print(f"访问ACM主页失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"访问ACM主页出错: {e}")
            return False
    
    def search_paper(self, title):
        """在ACM网站搜索论文"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 每次搜索前更新User-Agent
                self.update_headers()
                
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
                    print(f"第{attempt+1}次尝试被拒绝(403)，等待后重试...")
                    if attempt < max_retries - 1:
                        wait_time = random.randint(30, 60)
                        print(f"等待{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"多次尝试后仍被拒绝，跳过此论文")
                        return None
                
                response.raise_for_status()
                
                # 随机等待，模拟人类行为
                wait_time = random.randint(10, 20)
                print(f"页面加载等待{wait_time}秒...")
                time.sleep(wait_time)
                
                # 解析搜索结果页面
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找第一个搜索结果链接
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
                print(f"第{attempt+1}次搜索论文时出错: {e}")
                if attempt < max_retries - 1:
                    wait_time = random.randint(15, 30)
                    print(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"多次尝试后仍然失败")
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
            
            # 随机等待
            wait_time = random.randint(8, 15)
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
            response = self.session.get(pdf_url, timeout=120, stream=True)
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
        
        # 首先访问主页建立会话
        if not self.visit_homepage_first():
            print("无法访问ACM主页，可能存在网络问题")
            return
        
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
                
                # 网络礼仪：随机等待30-60秒，避免被封IP
                if i < len(titles):  # 最后一个不需要等待
                    wait_time = random.randint(30, 60)
                    print(f"等待{wait_time}秒...")
                    time.sleep(wait_time)
                
        finally:
            print(f"\n下载完成统计:")
            print(f"成功下载: {successful_downloads} 篇")
            print(f"下载失败: {failed_downloads} 篇")
            print(f"总计处理: {len(titles)} 篇")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python acm_paper_downloader_enhanced.py <excel_file_path>")
        print("示例: python acm_paper_downloader_enhanced.py papers.xlsx")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    if not os.path.exists(excel_file):
        print(f"错误: 文件 '{excel_file}' 不存在")
        sys.exit(1)
    
    downloader = ACMPaperDownloaderEnhanced(excel_file)
    downloader.process_papers()


if __name__ == "__main__":
    main()