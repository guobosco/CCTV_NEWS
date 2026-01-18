# CCTV新闻联播爬虫与后端服务

## 项目简介

本项目是一个用于爬取中央电视台新闻联播内容，并提供API接口的后端服务系统。该系统能够定时爬取新闻联播内容，存储到SQLite数据库中，并通过RESTful API提供数据查询服务。

## 项目结构

```
WeChatApp_CCTV_NEWS/
├── backend/                # 后端服务目录
│   ├── backend.py          # 后端API服务
│   ├── news_to_sqlite.py   # 新闻爬虫脚本
│   ├── batch_run.py        # 批量爬取脚本
│   ├── scheduled_spider.py # 定时爬虫脚本
│   ├── config.yaml         # 配置文件
│   ├── requirements.txt    # 依赖列表
│   ├── install_dependencies.py # 依赖安装脚本
│   └── news.db             # SQLite数据库文件
├── pages/                  # 微信小程序页面
│   ├── detail/             # 新闻详情页
│   └── index/              # 首页
├── app.js                  # 微信小程序入口
├── app.json                # 微信小程序配置
├── app.wxss                # 微信小程序样式
└── README.md               # 项目说明文档
```

## 功能介绍

### 1. 后端服务
- 提供RESTful API接口
- 支持查询指定日期的新闻列表
- 支持查询单条新闻的详细内容
- 支持CORS跨域请求

### 2. 新闻爬虫
- 爬取指定日期的新闻联播内容
- 解析新闻标题、链接和详细内容
- 将爬取结果存储到SQLite数据库
- 支持批量爬取多个日期的新闻

### 3. 定时任务
- 自动定时执行新闻爬取
- 支持自定义执行频率
- 支持日志记录

### 4. 配置管理
- 通过YAML配置文件管理所有参数
- 支持动态调整配置
- 无需修改代码即可更换服务器环境

## 技术栈

- **Python**: 3.8+
- **Web框架**: Flask 2.0+
- **HTTP客户端**: Requests 2.25+
- **HTML解析**: BeautifulSoup4 4.9+
- **数据库**: SQLite
- **配置管理**: PyYAML 6.0+
- **定时任务**: Schedule 1.1+
- **跨域支持**: Flask-CORS 3.0+

## 环境要求

- Python 3.8 或更高版本
- pip 19.0 或更高版本
- 支持的操作系统: Windows, Linux, macOS

## 安装步骤

### 方法一：使用自动安装脚本（推荐）

```bash
cd backend
python install_dependencies.py
```

### 方法二：手动安装

1. 安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

2. （可选）安装系统依赖（Linux系统）

```bash
sudo apt update
sudo apt install -y build-essential python3-venv libyaml-dev
```

## 配置说明

修改 `backend/config.yaml` 文件，根据实际需求调整配置：

### 后端服务配置

```yaml
backend:
  host: "0.0.0.0"          # 服务器IP，0.0.0.0表示监听所有网卡
  port: 5001                # 端口号
  debug: true               # 调试模式，生产环境建议设置为false
```

### 数据库配置

```yaml
database:
  path: "news.db"           # 数据库文件路径
```

### 爬虫配置

```yaml
spider:
  backend_url: "http://localhost:5001"  # 后端服务URL
  request_timeout: 10       # 请求超时时间（秒）
  max_retries: 5            # 最大重试次数
  request_delay: 1.0        # 请求延迟（秒）
```

### 批量运行配置

```yaml
batch:
  python_path: "python.exe"  # Python解释器路径
  main_script: "news_to_sqlite.py"  # 主爬虫脚本路径
  default_start_date: "2022-01-01"  # 默认开始日期
```

## 使用方法

### 1. 启动后端服务

```bash
cd backend
python backend.py
```

### 2. 运行单次爬虫

```bash
cd backend
python news_to_sqlite.py --date 2022-01-01
```

### 3. 批量爬取新闻

```bash
cd backend
python batch_run.py --start 2022-01-01 --end 2022-01-31
```

### 4. 启动定时爬虫

```bash
cd backend
python scheduled_spider.py
```

## API接口说明

### 1. 查询指定日期的新闻列表

**URL**: `/db/news_list?date=YYYY-MM-DD`

**方法**: `GET`

**参数**: 
- `date`: 日期，格式为YYYY-MM-DD

**返回示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "date": "2022-01-01",
    "items": [
      {
        "id": 1,
        "date": "2022-01-01",
        "title": "新闻标题1",
        "item_number": "1/10",
        "link": "http://example.com/news1"
      },
      // 更多新闻条目...
    ]
  }
}
```

### 2. 查询单条新闻详情

**URL**: `/db/news_detail?id=1`

**方法**: `GET`

**参数**: 
- `id`: 新闻ID

**返回示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "date": "2022-01-01",
    "title": "新闻标题1",
    "content": "新闻详细内容...",
    "item_number": "1/10"
  }
}
```

## 部署说明

### Linux系统部署

1. 创建虚拟环境

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. 配置系统服务

创建 `/etc/systemd/system/backend.service` 文件：

```ini
[Unit]
Description=CCTV News Backend Service
After=network.target

[Service]
User=ubuntu  # 替换为您的用户名
WorkingDirectory=/path/to/your/project/backend
ExecStart=/path/to/your/project/backend/venv/bin/python backend.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. 启用服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable backend.service
sudo systemctl start backend.service
```

4. 查看服务状态

```bash
sudo systemctl status backend.service
```

## 常见问题

1. **Q**: 爬虫运行时提示 "加载配置文件失败"
   **A**: 检查 `config.yaml` 文件是否存在，格式是否正确

2. **Q**: 后端服务无法启动
   **A**: 检查端口是否被占用，或是否有足够的权限

3. **Q**: API请求返回404
   **A**: 检查请求路径是否正确，或后端服务是否正常运行

4. **Q**: 爬取的数据为空
   **A**: 检查网络连接，或新闻网站结构是否有变化

5. **Q**: 数据库查询速度慢
   **A**: 检查数据库索引是否创建，或考虑优化查询语句

## 开发说明

### 代码结构

- `backend.py`: 主要负责API服务，使用Flask框架实现
- `news_to_sqlite.py`: 主要负责新闻爬取和数据库存储
- `batch_run.py`: 主要负责批量执行爬虫任务
- `scheduled_spider.py`: 主要负责定时执行爬虫任务

### 日志说明

- 定时爬虫日志: `scheduled_spider.log`
- 新闻爬虫日志: `news_to_sqlite.log`
- 批量运行日志: `batch_run.log`

### 数据库结构

新闻表结构: `news_联播`

| 字段名       | 类型          | 描述                   |
|------------|-------------|----------------------|
| id         | INTEGER     | 主键，自增               |
| date       | TEXT        | 新闻日期，格式YYYY-MM-DD  |
| title      | TEXT        | 新闻标题                 |
| link       | TEXT        | 新闻链接，唯一约束          |
| item_number| TEXT        | 新闻条目编号，格式如"1/10" |
| total_items| INTEGER     | 当日新闻总条数             |
| content    | TEXT        | 新闻内容                 |
| created_at | DATETIME    | 创建时间                 |
| updated_at | DATETIME    | 更新时间                 |

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 联系方式

如有问题或建议，欢迎通过以下方式联系：

- Email: your-email@example.com

## 更新日志

### v1.0.0 (2026-01-18)

- 初始版本发布
- 实现新闻联播内容爬取
- 实现RESTful API服务
- 实现定时爬取功能
- 支持配置文件管理

---

**温馨提示**: 本项目仅用于学习和研究目的，请勿用于商业用途。请遵守相关法律法规，合理使用爬虫技术。
