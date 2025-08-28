# ACM Digital Library 论文自动下载器

这是一个Python脚本，能够根据Excel文件中列出的论文标题，自动在ACM Digital Library网站上搜索并下载对应的PDF论文。

## 🌐 三个版本可选

### 1. Selenium版本 (`acm_paper_downloader.py`)
- 使用Chrome浏览器自动化
- 需要安装ChromeDriver
- 适合有完整网络环境的用户

### 2. Requests版本 (`acm_paper_downloader_requests.py`) **🎓 校园网推荐**
- 纯HTTP请求，无需浏览器
- 无需安装ChromeDriver
- 适合校园网环境，网络限制较多的情况
- 更轻量，资源占用更少

### 3. 增强版 (`acm_paper_downloader_enhanced.py`) **🛡️ 反爬虫环境推荐**
- 专门应对403 Forbidden错误
- 包含多重反反爬虫策略
- 随机User-Agent和智能重试机制
- 适合遇到频繁403错误的情况

### 4. 终极版 (`acm_paper_downloader_ultimate.py`) **🚀 最强反爬虫版本**
- 使用CloudScraper绕过Cloudflare保护
- 多种搜索策略自动切换
- 最强的反反爬虫机制
- **已验证可解决403错误问题**

## 功能特点

- 📚 从Excel文件读取论文标题列表
- 🔍 自动在ACM Digital Library搜索论文
- 📄 自动下载找到的PDF文件
- 🛡️ 智能错误处理和重试机制
- 📝 详细的日志输出
- ⏱️ 智能随机延时策略，有效避免IP被封禁
- 📁 自动创建下载目录和文件名净化

## 安装依赖

### 通用依赖（所有版本都需要）
```bash
pip install pandas openpyxl requests
```

### Selenium版本额外依赖
```bash
pip install selenium
```

### Requests版本额外依赖（校园网推荐）
```bash
pip install beautifulsoup4 lxml
```

### 增强版额外依赖（反爬虫环境推荐）
```bash
pip install beautifulsoup4 lxml fake-useragent
```

### 终极版额外依赖（最强反爬虫版本）
```bash
pip install beautifulsoup4 lxml fake-useragent cloudscraper
```

### 一键安装所有依赖
```bash
pip install -r requirements.txt
```

### 2. 安装Chrome浏览器和ChromeDriver

#### macOS:
```bash
# 安装Chrome浏览器（如果还没有）
brew install --cask google-chrome

# 安装ChromeDriver
brew install chromedriver
```

#### Windows:
1. 下载并安装Chrome浏览器
2. 从 [ChromeDriver官网](https://chromedriver.chromium.org/) 下载对应版本的ChromeDriver
3. 将ChromeDriver.exe放到PATH环境变量中的目录

#### Linux:
```bash
# Ubuntu/Debian
sudo apt-get install google-chrome-stable
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
# 下载对应版本的ChromeDriver
```

## 使用方法

### 0. 选择合适的版本

**校园网用户推荐使用Requests版本：**
```bash
python acm_paper_downloader_requests.py your_papers.xlsx
```

**有完整网络环境的用户可以使用Selenium版本：**
```bash
python acm_paper_downloader.py your_papers.xlsx
```

**遇到403 Forbidden错误推荐使用增强版：**
```bash
python acm_paper_downloader_enhanced.py your_papers.xlsx
```

**最强反爬虫版本推荐使用终极版：**
```bash
python acm_paper_downloader_ultimate.py your_papers.xlsx
```

**如果遇到403 Forbidden错误，强烈推荐使用终极版！已验证可解决403问题。**

### 1. 准备Excel文件

创建一个Excel文件（.xlsx格式），包含一个名为 `Title` 的列，每行填入一个论文的完整标题。

示例Excel文件结构：
```
| Title                                                    |
|----------------------------------------------------------|
| The Design and Implementation of a Log-Structured File System |
| MapReduce: Simplified Data Processing on Large Clusters |
| Bigtable: A Distributed Storage System for Structured Data |
```

### 2. 运行脚本

**校园网环境（推荐）：**
```bash
python acm_paper_downloader_requests.py your_papers.xlsx
```

**完整网络环境：**
```bash
python acm_paper_downloader.py your_papers.xlsx
```

### 3. 使用示例文件测试

我们提供了一个示例Excel文件，你可以直接使用：

**校园网环境：**
```bash
python acm_paper_downloader_requests.py sample_papers.xlsx
```

**完整网络环境：**
```bash
python acm_paper_downloader.py sample_papers.xlsx
```

## 输出说明

脚本会在当前目录下创建一个 `downloaded_papers` 文件夹，所有下载的PDF文件都会保存在这里。

文件名会根据论文标题自动生成，并移除非法字符（如 `\/:*?"<>|`）。

## 日志输出示例

```
浏览器驱动初始化成功
成功读取 5 个论文标题
创建输出目录: downloaded_papers

[1/5] 正在处理: The Design and Implementation of a Log-Structured File System
搜索URL: https://dl.acm.org/search/search-results?q=The%20Design%20and%20Implementation%20of%20a%20Log-Structured%20File%20System
找到第一个搜索结果: https://dl.acm.org/doi/10.1145/146941.146943
找到PDF链接: https://dl.acm.org/doi/pdf/10.1145/146941.146943
成功下载并保存为: The Design and Implementation of a Log-Structured File System.pdf
等待15秒...

[2/5] 正在处理: MapReduce: Simplified Data Processing on Large Clusters
...
```

## 错误处理

脚本包含以下错误处理机制：

- **搜索无结果**：如果搜索某个标题后没有返回任何结果，会打印"未找到论文"并跳过
- **找不到PDF**：如果无法找到PDF下载链接（可能需要付费），会打印"无法下载（可能需要付费）"并跳过
- **网络错误**：自动重试和错误日志记录
- **文件名冲突**：自动净化文件名，移除非法字符

## 注意事项

1. **网络礼仪**：脚本采用智能随机延时策略，每次论文处理间隔10-20秒，页面加载等待3-6秒，请不要修改这些延时，以免被网站封禁
2. **付费内容**：某些论文可能需要付费订阅才能下载，脚本会跳过这些论文
3. **浏览器窗口**：脚本运行时会打开Chrome浏览器窗口，这是正常现象
4. **下载速度**：下载速度取决于网络状况和ACM服务器响应速度

## 故障排除

### ChromeDriver相关问题

如果遇到ChromeDriver错误：

1. 确保Chrome浏览器已安装
2. 确保ChromeDriver版本与Chrome浏览器版本兼容
3. 确保ChromeDriver在PATH环境变量中

### Excel文件读取问题

1. 确保Excel文件格式为.xlsx
2. 确保文件中有名为"Title"的列
3. 确保论文标题不为空

### 网络连接问题

1. 确保网络连接正常
2. 如果在公司网络，可能需要配置代理
3. 某些地区可能需要VPN访问ACM网站

## 文件结构

```
.
├── acm_paper_downloader.py          # Selenium版本（需要ChromeDriver）
├── acm_paper_downloader_requests.py # Requests版本（校园网推荐）
├── acm_paper_downloader_enhanced.py # 增强版（反爬虫环境推荐）
├── acm_paper_downloader_ultimate.py # 终极版（最强反爬虫版本）⭐
├── requirements.txt                 # 依赖包列表
├── sample_papers.xlsx               # 示例Excel文件
├── README.md                        # 说明文档
└── downloaded_papers/               # 下载的PDF文件目录（运行后创建）
```

## 许可证

本项目仅供学术研究使用，请遵守ACM Digital Library的使用条款和版权规定。