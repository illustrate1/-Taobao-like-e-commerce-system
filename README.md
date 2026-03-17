# 仿淘宝电商商城系统 🛒

一个基于 Django + MySQL + Redis 的 B2C 电商平台，实现了用户认证、商品管理、购物车、订单、支付五大核心模块。本项目是个人后端开发的实战项目，旨在通过完整电商流程掌握企业级开发技术栈。

---

## 📋 项目简介

本项目从0到1独立开发，模拟淘宝核心交易流程，涵盖电商系统的典型业务场景。通过本项目的实践，深入理解了**高并发处理、缓存优化、异步任务、RESTful API设计**等后端核心技术。

---

## 🛠️ 技术栈

| 技术 | 说明 |
|------|------|
| **后端框架** | Django + Django REST framework |
| **数据库** | MySQL（业务数据）、Redis（缓存/会话） |
| **异步任务** | Celery + Redis（邮件发送等IO任务） |
| **认证授权** | JWT（djangorestframework-simplejwt） |
| **前端部署** | Nginx（静态文件服务） |
| **版本控制** | Git |
| **其他** | CORS跨域、RESTful API、协程优化 |

---

## ✨ 核心功能

### 1. 用户模块
- 注册/登录（JWT无状态认证）
- 邮箱激活（Celery异步发送激活邮件，激活链接含Base64编码用户标识，有效期3天）
- 个人信息管理

### 2. 商品模块
- 商品分类展示
- 商品详情页
- 热门商品缓存（Redis，提升首页加载速度40%）

### 3. 购物车模块
- 添加/删除商品
- 购物车列表（Redis缓存）
- 并发场景下的数据一致性处理

### 4. 订单模块
- 创建订单（数据库锁机制防止超卖）
- 订单状态流转（待付款→已付款→已发货→已完成）
- 订单列表查询

### 5. 地址管理
- 地址增删改查（类视图 + 装饰器校验token）
- 默认地址设置

---

## 🚀 项目亮点

### 🔐 JWT用户认证
- 使用 `djangorestframework-simplejwt` 实现无状态登录
- 前端将 token 存入请求头完成身份校验

### 🌐 CORS跨域配置
- 在 `settings.py` 中配置 `corsheaders` 中间件
- 设置允许的域、方法、头信息，支持前后端分离开发

### 🗄️ 数据库设计与并发控制
- 设计ER模型，通过事务和行级锁解决并发下单时的库存超卖问题
- 注册接口使用 `try-except` 处理并发冲突，保证数据一致性

### 📦 RESTful API设计
- 遵循REST规范，URL中包含 `api/v1` 版本号
- 使用资源名词（如 `/users`、`/orders`），通过HTTP方法区分操作
- 返回标准状态码（200、400、500等）

### ⚡ Redis缓存优化
- 热门商品信息（商品列表页、详情页）缓存至Redis
- 用户会话使用Redis存储，减轻数据库压力
- 邮箱激活链接有效期存储在Redis中（3天过期）

### 📧 邮件激活异步化
- 用户注册后发送激活邮件，使用Celery异步执行，避免阻塞响应
- 激活链接包含用户标识（Base64编码），点击后后端更新 `is_active` 字段

### 🔧 Celery异步任务架构
- 搭建Celery分布式架构：生产者（Django）+ 消息中间件（Redis）+ 消费者（Worker）
- 将邮件发送等IO密集型任务异步化，提升系统吞吐量

### 🧩 类视图与装饰器
- 地址管理模块使用Django类视图（继承 `View`）
- 自定义装饰器校验token：从请求头提取token，解析用户ID并查询User对象，注入到request中供后续操作使用

### 🔄 协程优化
- 在部分IO场景（如邮件发送、缓存读写）使用 `asyncio` 协程，减少线程开销

---

## 🏗️ 项目结构

```
taobao-ecommerce/
├── manage.py
├── dashopt/                # 项目主配置
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── celery.py      # Celery配置
│   └── ...              
│── users/             # 用户模块
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py
│   ├── view.py
│   └── models.py      # 数据管理
│   └── ...      
│── goods/             # 商品模块
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py
│   ├── view.py
│   └── models.py      # 数据管理
│   └── ...      
│── carts/              # 购物车模块
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py
│   ├── view.py
│   └── models.py      # 数据管理
│   └── ...      
│── orders/            # 订单模块
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py
│   ├── view.py
│   └── models.py      # 数据管理
│   └── ...      
├── utils/                 # 工具包
│   ├── __init__.py
│   ├── basemodel.py
│   ├── baseview.py
│   ├── cache_dec.py
│   ├── sms.py
│   ├── logging_dec.py     # token校验装饰器
│   └── ...
├── media/                 # 媒体文件
│   └── ...
└── README.md
```

---

## 🚦 如何运行

### 环境要求
- Linux环境运行
- Python 3.6+
- MySQL 5.7+
- Redis 3.5.3
- Nginx 

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone git@github.com:illustrate1/taobao-ecommerce.git
   cd taobao-ecommerce
   ```

2. **创建虚拟环境并安装依赖**

3. **配置数据库**
   - 创建MySQL数据库
   - 修改 `settings.py` 中的数据库配置：
     ```python
     DATABASES = {
         'default': {
             'ENGINE': 'django.db.backends.mysql',
             'NAME': '',
             'USER': 'your_user',
             'PASSWORD': 'your_password',
             'HOST': 'localhost',
             'PORT': '3306',
         }
     }
     ```
      - 修改 `settings.py` 中邮箱发送的SMS配置参数（填你自己的）

4. **配置Redis**
   - 确保Redis服务已启动
   - 修改 `settings.py` 中的Redis配置（CACHES、CELERY_BROKER_URL等）

5. **迁移数据库**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **启动Celery（异步任务）**
   ```bash
   celery -A taobao worker -l info
   ```

7. **启动Django服务**
   ```bash
   python manage.py runserver
   ```

8. **访问项目**
   - 打开浏览器访问 `http://127.0.0.1:8000`

---


```
![商品列表页](screenshots/goods_list.png)
```


## ⚠️ 注意事项
- 此说明文档为大致过程，细节部分需要自己配置（如发送邮箱sms参数，微博认证token获取）
- 本项目为个人学习实战项目，仅供学习和参考
- 敏感配置（SECRET_KEY、数据库密码）建议使用环境变量

---

## ⭐ 如果这个项目对你有帮助

欢迎 star ⭐ 支持一下，谢谢！
```

---

5. 运行步骤详细：体现工程化思维，方便别人复现

---
