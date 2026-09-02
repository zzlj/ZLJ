# pytest 接口自动化测试框架

基于 YAML 数据驱动的接口自动化测试框架，被测系统为本地 Flask + MySQL 的交易/用户管理服务。

## 环境要求

| 项 | 要求 |
|----|------|
| Python | 3.12+（开发使用 3.12.14） |
| MySQL | 8.0+，本机 3306 端口 |
| 被测服务 | Flask mock 服务，本机 8000 端口 |
| Allure 命令行 | 可选，用于生成 HTML 测试报告 |

## 一、安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/zzlj/ZLJ.git
cd ZLJ
```

### 2. 创建并激活虚拟环境

```bash
python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置数据库连接（推荐环境变量方式）

数据库凭据通过环境变量注入，避免把密码写进代码：

```bash
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password       # 改成你本机 MySQL 的密码
export DB_NAME=user_manage
```

Windows PowerShell：

```powershell
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="user_manage"
```

> 不设环境变量时，会回退到 [commons/config.py](pytest/commons/config.py) 中的本地默认值（仅供本地学习使用）。

### 5. 初始化数据库

确保 MySQL 已启动，并创建 `user_manage` 数据库及对应表（users / accounts / orders / positions / settlements / contracts）。
被测服务的建表脚本请参考后端项目（web-app-demo）。

### 6. 启动被测服务

被测 Flask 服务需监听 `http://127.0.0.1:8000`，启动方式参考后端项目。
启动后可用以下命令验证：

```bash
curl -X POST http://127.0.0.1:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'
```

返回 `{"code":0,...}` 即说明服务正常。

## 二、运行测试

### 方式一：直接跑 pytest（推荐）

```bash
cd ZLJ
source venv/bin/activate
python -m pytest
```

只跑某条用例（按用例名关键字过滤）：

```bash
python -m pytest -k "登录"
```

### 方式二：带 Allure 报告

```bash
python pytest/main.py
# 报告会生成到 report/ 目录，浏览器打开 report/index.html 查看
```

> 生成 HTML 报告需要本地安装 [Allure 命令行工具](https://allurereport.org/)（需 JDK 17+）。

## 三、项目结构

```
ZLJ/
├── pytest.ini                  # pytest 配置（测试路径、日志、markers）
├── requirements.txt            # Python 依赖
├── README.md
└── pytest/
    ├── conftest.py             # pytest fixture / sys.path 设置
    ├── main.py                 # 入口：跑 pytest + 生成 allure 报告
    ├── commons/                # 框架通用模块
    │   ├── config.py          # 数据库配置（环境变量优先）
    │   ├── db_utils.py         # MySQL 查询/执行
    │   ├── clean_trade.py      # 交易数据清理工具
    │   ├── runner_utils.py     # YAML 步骤执行器（request/response/db/extract）
    │   ├── extract_utils.py    # 变量提取（jsonpath）
    │   └── yaml_unit.py        # YAML 文件加载
    ├── responses_validator.py  # 递归断言（dict/list/标量）
    ├── data/                   # YAML 测试用例
    │   ├── test_01_login.yaml
    │   ├── test_02_register.yaml
    │   ├── test_03_users.yaml
    │   ├── test_04_trade.yaml
    │   └── test_05_trade_all.yaml
    └── test/
        └── test_yaml.py        # 参数化测试入口
```

## 四、YAML 用例语法简述

每条用例是一个 dict，包含 `name` 和 `steps`：

```yaml
- name: 用例名称
  steps:
    - request:               # 发起 HTTP 请求
        method: POST
        url: http://127.0.0.1:8000/api/login
        json: {username: admin, password: "123456"}

    - response:              # 断言响应
        status_code: 200
        json:
          code: 0
          msg: 登录成功

    - extract:               # 提取变量供后续步骤使用
        token: [json, $.data.token]

    - db:                    # 数据库操作
        execute: DELETE FROM orders       # 写操作（无返回）
        sql: SELECT * FROM users WHERE username = "whx"   # 查询
        expect:                            # 查询结果断言
          - username: whx
            role: user
```

### 变量替换

- 请求参数、断言、SQL 中可用 `${变量名}` 引用已提取的变量
- 整串为单个占位符时保留原类型（如 `${id}` → 整数 40，断言数字不会类型不匹配）
- 占位符混在文本中时按字符串拼接（如 `Bearer ${token}`）

### 类型约定（常见坑）

- YAML 中带引号 → 字符串；不带引号的数字 → int/float
- 期望数字字段（如 `amount: 570000.0`）**不要加引号**，否则 `'570000.0' != 570000.0`
- 数据库 DECIMAL 字段在 Python 中是 `Decimal`，与 JSON 返回的字符串/数字比较时可能类型不匹配

## 五、常见问题

### Q: 跑测试报 `Connection refused`？

被测服务（8000 端口）未启动，请先启动 Flask mock 服务。

### Q: 跑测试报 `Access denied for user 'root'`？

数据库密码不对，请通过 `DB_PASSWORD` 环境变量设置正确密码。

### Q: `no tests collected` / `1 skipped`？

YAML 文件解析失败。常见原因：
- flow mapping `{}` 中放了 `${var}`（`{` 是 YAML 语法字符）→ 改用块写法
- 缩进不一致 → 同一列表项左对齐
- 数字字段加了引号导致类型不匹配

### Q: 怎么看实际请求和响应？

查看 `logs/pytest.log`，每步都会记录请求参数、实际响应、变量提取结果。

## 六、依赖说明

核心依赖见 [requirements.txt](requirements.txt)。
若需复现开发时完整环境（含 selenium 等可选插件），可执行：

```bash
pip freeze > full_requirements.txt
```

## 七、协作笔记

详细的项目学习与协作历史见 [notes.md](notes.md)。
