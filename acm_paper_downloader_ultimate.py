#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACM Digital Library 论文自动下载器 (终极版)
专门应对严格的反爬虫机制，包含代理支持和多种绕过策略

安装依赖:
pip install pandas openpyxl requests beautifulsoup4 lxml fake-useragent cloudscraper

使用方法:
python acm_paper_downloader_ultimate.py papers.xlsx
"""

import os
import sys
import time
import re
import random
import json
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

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    print("提示: 安装 cloudscraper 可以绕过Cloudflare保护: pip install cloudscraper")


class ACMPaperDownloaderUltimate:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.output_dir = "downloaded_papers"
        self.base_url = "https://dl.acm.org/search/search-results?q="
        self.session = None
        self.ua = UserAgent() if HAS_FAKE_UA else None
        self.use_cloudscraper = HAS_CLOUDSCRAPER
        self.setup_session()
        
    def get_random_user_agent(self):
        """获取随机User-Agent"""
        if self.ua:
            try:
                return self.ua.random
            except:
                pass
        
        # 备用User-Agent列表 - 更多样化
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        return random.choice(user_agents)
        
    def setup_session(self):
        """设置requests会话，优先使用cloudscraper"""
        if self.use_cloudscraper:
            print("使用CloudScraper绕过Cloudflare保护...")
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'darwin' if sys.platform == 'darwin' else 'windows',
                    'desktop': True
                }
            )
        else:
            print("使用标准requests会话...")
            self.session = requests.Session()
            
            # 设置重试策略
            retry_strategy = Retry(
                total=3,
                backoff_factor=3,
                status_forcelist=[403, 429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        
        # 设置基础请求头
        self.update_headers()
        
        print("终极版网络会话初始化成功")
    
    def update_headers(self):
        """更新请求头，使用随机User-Agent和更真实的浏览器特征"""
        headers = {
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
            'DNT': '1',
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"macOS"' if sys.platform == 'darwin' else '"Windows"'
        }
        
        self.session.headers.update(headers)
    
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
    
    def try_alternative_search_methods(self, title):
        """尝试多种搜索方法"""
        search_methods = [
            # 方法1: 传统搜索URL（之前成功率较高）
            lambda t: self.base_url + quote(t),
            # 方法2: 简化搜索（去掉特殊字符）
            lambda t: self.base_url + quote(re.sub(r'[^\w\s]', ' ', t)),
            # 方法3: 只搜索前几个关键词
            lambda t: self.base_url + quote(' '.join(t.split()[:5])),
            # 方法4: 使用ACM的doSearch API - 全字段搜索
            lambda t: f"https://dl.acm.org/action/doSearch?AllField={quote(t)}&expand=all",
            # 方法5: 使用ACM的doSearch API - 标题搜索
            lambda t: f"https://dl.acm.org/action/doSearch?Title={quote(t)}&expand=all"
        ]
        
        for i, method in enumerate(search_methods, 1):
            try:
                search_url = method(title)
                print(f"尝试搜索方法 {i}: {search_url}")
                result = self.perform_search_request(search_url, title)
                if result:
                    return result
                    
                # 每次尝试后等待
                wait_time = random.randint(3, 8)
                print(f"方法 {i} 失败，等待{wait_time}秒后尝试下一种方法...")
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"搜索方法 {i} 出错: {e}")
                continue
        
        return None
    
    def perform_search_request(self, search_url, title):
        """执行搜索请求"""
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                # 每次请求前更新User-Agent
                self.update_headers()
                
                # 添加随机延迟
                if attempt > 0:
                    wait_time = random.randint(5, 15)
                    print(f"第{attempt+1}次尝试前等待{wait_time}秒...")
                    time.sleep(wait_time)
                
                # 设置请求头
                headers = {
                    'Referer': 'https://dl.acm.org/',
                    'Origin': 'https://dl.acm.org',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin'
                }
                
                # 发送请求
                response = self.session.get(search_url, headers=headers, timeout=45)
                
                # 检查响应状态
                if response.status_code == 403:
                    print(f"第{attempt+1}次尝试被拒绝(403)")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        print(f"所有尝试都被拒绝，可能需要更换网络环境")
                        return None
                
                if response.status_code == 429:
                    print(f"请求过于频繁(429)，需要等待更长时间")
                    wait_time = random.randint(60, 120)
                    print(f"等待{wait_time}秒...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                # 随机等待，模拟人类行为
                wait_time = random.randint(3, 8)
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
                    'a[href*="/doi/"]',
                    '.search-result a[href*="/doi/"]',
                    '.result-item a[href*="/doi/"]'
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
                    
                    print(f"找到搜索结果: {first_result_link}")
                    return first_result_link
                else:
                    print(f"未找到搜索结果")
                    return None
                    
            except Exception as e:
                print(f"第{attempt+1}次搜索请求出错: {e}")
                if attempt < max_retries - 1:
                    wait_time = random.randint(5, 15)
                    print(f"等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"所有搜索尝试都失败了")
                    return None
    
    def search_paper(self, title):
        """搜索论文，使用多种方法"""
        print(f"开始搜索论文: {title}")
        return self.try_alternative_search_methods(title)
    
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
            
            response = self.session.get(paper_url, headers=headers, timeout=45)
            
            if response.status_code == 403:
                print(f"访问论文详情页被拒绝(403)")
                return None
                
            response.raise_for_status()
            
            # 随机等待
            wait_time = random.randint(2, 5)
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
                'a[data-title*="PDF"]',
                '.download-link[href*="pdf"]',
                'a[href*="/ft_gateway.cfm"]'
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
            response = self.session.get(pdf_url, timeout=180, stream=True)
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
        
        print("\n=== 开始处理论文下载 ===")
        print(f"提示: 如果遇到大量403错误，建议:")
        print(f"1. 更换网络环境（如使用VPN）")
        print(f"2. 等待一段时间后重试")
        print(f"3. 联系学校图书馆获取数据库访问权限")
        print("\n")
        
        try:
            for i, title in enumerate(titles, 1):
                print(f"\n[{i}/{len(titles)}] 正在处理: {title}")
                print("=" * 80)
                
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
                            print(f"下载失败: {title}")
                    else:
                        failed_downloads += 1
                        print(f"无法获取PDF链接: {title}")
                else:
                    failed_downloads += 1
                    print(f"搜索失败: {title}")
                
                # 网络礼仪：随机等待，避免被封IP
                if i < len(titles):  # 最后一个不需要等待
                    wait_time = random.randint(15, 30)
                    print(f"\n等待{wait_time}秒后处理下一篇论文...")
                    time.sleep(wait_time)
                
        finally:
            print(f"\n" + "=" * 50)
            print(f"下载完成统计:")
            print(f"成功下载: {successful_downloads} 篇")
            print(f"下载失败: {failed_downloads} 篇")
            print(f"总计处理: {len(titles)} 篇")
            print(f"成功率: {successful_downloads/len(titles)*100:.1f}%" if titles else "0%")
            
            if failed_downloads > 0:
                print(f"\n失败原因可能包括:")
                print(f"- 论文需要付费或订阅")
                print(f"- 网络访问受限(403错误)")
                print(f"- 论文不存在于ACM数据库")
                print(f"- 网络连接问题")


def main():
    if len(sys.argv) != 2:
        print("使用方法: python acm_paper_downloader_ultimate.py <excel_file_path>")
        print("示例: python acm_paper_downloader_ultimate.py papers.xlsx")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    
    if not os.path.exists(excel_file):
        print(f"错误: 文件 '{excel_file}' 不存在")
        sys.exit(1)
    
    downloader = ACMPaperDownloaderUltimate(excel_file)
    downloader.process_papers()


if __name__ == "__main__":
    main()