# pytest 接口自动化学习项目 · 协作笔记

> 本文档是当前对话的核心结论沉淀，供新对话快速接续使用。新对话打开项目后，先读本文件即可无缝继续。

## 1. 项目概览

| 项 | 说明 |
|----|------|
| 学习目标 | pytest 接口自动化测试（YAML 数据驱动） |
| 被测系统 | web-app-demo（Flask + MySQL），本地服务 |
| 测试工程 | `pytest/` 目录（YAML 驱动框架） |
| 框架来源 | 跟着视频学习编写，非现成框架 |

## 2. 被测后端（web-app-demo）

### 服务信息

- 访问地址：http://127.0.0.1:8000 （登录页 `/login`）
- 启动命令（web-app-demo 目录下）：
  ```bash
  env -u PYTHONHOME -u PYTHONPATH .venv/bin/python app.py
  ```
- 默认账号：`admin / 123456`
- 数据库：MySQL（本机 3306），库名 `user_manage`，root 密码 `zhulingjia293`（仅本地学习用）
- 注意：venv 的 pip 曾被 PYTHONHOME/PYTHONPATH 环境变量污染，用 `env -u` 清理后正常；已补装 `cryptography` 依赖

### 接口清单

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/login` | 无 | 接口说明（方便浏览器查看） |
| POST | `/api/register` | 无 | 注册（用户名≥3字符、密码≥6字符、不能重复） |
| POST | `/api/login` | 无 | 登录，成功返回 `data.token` / `data.expires_at` / `data.user` |
| GET | `/api/me` | 需 token | 当前用户信息 |
| POST | `/api/logout` | 需 token | 退出，token 立即失效 |
| GET | `/api/users` | 需 token | 用户列表（data 是数组） |
| POST | `/api/users` | 需 token | 新增用户 |
| PUT | `/api/users/<id>` | 需 token | 修改用户 |
| DELETE | `/api/users/<id>` | 需 token | 删除用户（不能删自己） |
| GET | `/api/contracts` | 需 token | 交易：合约列表（code/name/multiplier/last_price） |
| POST | `/api/orders` | 需 token | 交易：下单即成交，body `{contract_code, side(buy/sell), quantity, price}` |
| GET | `/api/orders` | 需 token | 交易：我的订单列表 |
| GET | `/api/orders/<id>` | 需 token | 交易：订单详情（只能查自己的） |
| GET | `/api/positions` | 需 token | 交易：我的持仓（含浮动盈亏） |
| GET | `/api/account` | 需 token | 交易：资金账户（默认 100 万） |
| POST | `/api/settlement/run` | 需 token | 交易：按结算价结算指定合约，body `{contract_code, settle_price}` |
| GET | `/api/settlements` | 需 token | 交易：我的结算记录 |

### 响应格式与错误码

- 统一响应：`{"code": 0, "msg": "success", "data": ...}`，`code=0` 成功
- 登录失败：HTTP 200 + `code: 1` + `msg: 用户名或密码错误` + `data: null`
- 鉴权失败：HTTP 401 + `code: 401`（无 token / 假 token / 过期）
- token 携带方式：请求头 `Authorization: Bearer <token>`（行业标准做法）
- 中文返回：`app.json.ensure_ascii = False` 已设置，msg 直接显示中文

## 3. pytest 测试工程结构

```
pytest/
├── .venv/                 # 专用虚拟环境（uv python 3.12），2026-08-28 建，装好 requests/pyyaml/jsonpath/allure-pytest/pymysql
├── data/                  # 用例文件（一个 YAML = 一个功能模块，顶层是 list）
│   ├── test_login.yaml    # 登录模块：成功/失败 + 退出 + me(带/无token)，共 6 条
│   ├── test_users.yaml    # 用户模块：查列表/鉴权 + 新增(正反例)/修改/删除/边界，共 12 条
│   ├── test_register.yaml # 注册模块：成功+登录闭环/重复/过短/缺字段，共 5 条
│   └── test_trade.yaml    # 【计划】交易模块：合约/下单/持仓/结算，见 pytest-trade-guide.html
├── commons/
│   ├── yaml_unit.py       # load_yaml()
│   ├── runner_utils.py    # runner() 分发 request/response/extract/db；extract 支持 db 来源；response 断言也做变量替换
│   ├── extract_utils.py   # jsonpath 提取（支持 db / json / headers / cookies 来源）
│   └── db_utils.py        # db_query() / db_execute()（写操作带 commit），已实现
├── responses_validator.py # 响应断言 validator()（递归匹配），2026-08-28 重建
├── test/
│   └── test_yaml.py       # 收集所有 yaml → parametrize 驱动（my_var 未注入 ts，暂未用时间戳方案）
├── conftest.py
└── main.py
```

### YAML 用例格式（方式一：一个文件一个模块）

```yaml
- name: 用例名称
  steps:
    - request:
        method: POST
        url: http://127.0.0.1:8000/api/login
        json: {username: admin, password: '123456'}
    - response:
        status_code: 200
        json:
          code: 0
    - extract:
        token: [json, $.data.token]
```

- 顶层是 list（每个 `-` 块 = 一条用例），`name` + `steps`
- step 三种类型：`request` / `response`（断言）/ `extract`（提取变量到 my_var）
- 断言写什么就校验什么，没写的不检查（递归匹配：dict 按 key、list 按索引）

### test_yaml.py 关键设计

- `collect_cases()`：glob 扫描 `data/` 下 `*.yaml`，逐个 `load_yaml` 后用 `extend` 合并成一个大 list
- `@pytest.mark.parametrize('data', all_cases, ids=[c['name'] for c in all_cases])`：每条用例独立执行
- 用例标题必须用 `allure.dynamic.title(data['name'])`（不是 `allure.title`，后者是装饰器不生效）

## 4. 框架待办 / 已知问题

| # | 问题 | 状态 | 处理 |
|---|------|------|------|
| 1 | `runner_utils.py` 的 request 分支没调用 `replace_var`，`${token}` 不会替换 | **已修** | 已加 `v = replace_var(v, my_var)` 再 `requests.request(**v)` |
| 2 | `extract_utils.py` 函数名（`extract`）与 runner 导入（`extract_value`）不一致 | **已修** | 函数已统一为 `extract_value` |
| 3 | 空 yaml 文件导致 `load_yaml` 返回 None，`cases.extend(None)` 崩溃 | **已修** | `collect_cases` 已加 `if not data: continue` 防御 |
| 4 | `data/` 下混入非用例文件（如 zlj.yaml 是 dict 结构） | **已修** | glob 已限定 `test_*.yaml` |
| 5 | 用户列表 `data` 是数组，列表字段断言写法 | **已验** | `data: - username: admin` 按索引匹配，2026-08-29 全量跑通 |
| 6 | `responses_validator.py` 缺失（`runner_utils` 导入直接报错） | **已修** | 2026-08-28 重建（`validator` + `_match` 递归断言），注意文件在 `pytest/` 根目录而非 `commons/` |
| 7 | 修改/删除用例依赖"whx 已存在"（顺序依赖） | **已知待改进** | 全量跑通过；但 `pytest -k` 单独跑会失败（db 查不到 id → None）；删除用例在数据不存在时有假通过风险（count=0 巧合）。改进方向：用例自给自足（先确保数据存在） |

## 5. 常见坑汇总（踩过/分析过）

- **requests 报 502**：本地代理拦截 localhost。解决：`proxies={"http": None, "https": None}` 或用 `requests.Session()` + `s.trust_env = False`
- **浏览器 F12 看不到响应 / failed to load response data**：页面跳转导致 DevTools 丢数据，勾选 Preserve log 或延迟跳转
- **pytest 终端显示 `test_yaml[\u767b\u5f55...]`**：pytest 对非 ASCII id 的显示转义，不影响功能，allure 报告正常显示中文
- **`/login` 和 `/api/login` 区分**：`/login` 是页面（GET），`/api/login` 是接口（POST），浏览器地址栏访问接口会 405
- **venv 的 pip 报 `dataclass() got an unexpected keyword argument 'slots'`**：PYTHONHOME/PYTHONPATH 被污染，用 `env -u PYTHONHOME -u PYTHONPATH` 清理
- **MySQL 自增 id 跳号**：AUTO_INCREMENT 只增不减，删除/回滚的插入都会消耗 id 且不复用；"表里只剩 2 个用户、新增却是 id 7/8"是正常现象不是 bug。重置需 `TRUNCATE`（清空表）或 `ALTER TABLE users AUTO_INCREMENT = N`（N 须大于当前 max(id)）
- **新增用户验证别断言 id**：接口返回 `data.id` 每次跑用例都不同（跳号），不要对具体值做断言；数据库验证用唯一键 `username` 定位（`SELECT ... WHERE username='...'`）；若后续删除需要用 id，用 `extract` 提取复用（`new_id: [json, $.data.id]`）即可
- **role / email 可选**：POST /api/users 缺 role/email 仍创建成功（role 默认 user、email 可空），"未录入"不是反例，应写成正向断言（缺 role → 成功且 role=user）
- **重复用户名 msg 带具体名**：返回是 `用户名 admin 已存在`（含用户名），断言别写成 `用户名已存在`
- **"查不到"要用 COUNT(*)**：`expect: []`（空列表）在 `_match` 规则下恒真 → 假通过；删除后验证写成 `SELECT COUNT(*) AS cnt ...` + `expect: [{cnt: 0}]`
- **PUT 空 body 也返回"更新成功"**：接口不校验请求体，属接口缺陷，测试照实断言 code:0
- **DevTools 请求头/响应头别混淆**：Request Headers 的 `Content-Length: 0` 是"请求体为空"（正常）；判断接口有没有返回要看 Response Headers 的 `content-length`（非 0 即有 body）。页面跳转后点 Response 显示 failed to load response data 是 DevTools 显示问题，接口数据是完整的（logout 实测 content-length 60，正常返回 `{"code":0,"msg":"已退出登录"}`）

## 6. 下一步建议（按顺序）

1. **基线已建立**：2026-08-30 全量 **23 passed**（登录 6 + 用户 12 + 注册 5）。命令：`cd /Users/zlj/Downloads/ZLJ_test && env -u PYTHONHOME -u PYTHONPATH pytest/.venv/bin/python -m pytest`
2. **剩余清单已完成**：注册模块、退出登录、/api/me（带/无 token）、PUT/DELETE 不存在 id 均已落地并验证
3. **（可选，未写）**：退出后 token 失效、DELETE 不能删自己、缺 role/email 正向修正 —— 用户决定暂不写，可接受
4. **交易模块用例（下一步）**：`test_trade.yaml` 按 `pytest-trade-guide.html` 写（后端已上线、页面已加 /trade）
5. 数据说明：注册"已存在"用例依赖首条创建的 ZLJ，跑完残留 1 个 ZLJ 用户（设计使然）；whx 被删除用例自动清掉
6. （可选）消除顺序依赖、时间戳唯一性、allure 报告留档

## 7. 相关产物

- `pytest-guide.html`：YAML 模块化用例编写提示（含骨架）
- `pytest-users-guide.html`：用户列表查询用例大纲（含代码功能说明）
- `pytest-user-add-guide/`（2026-08-28 新增）：新增用户接口测试·编写提示大纲 —— 含接口/表结构事实、db step 设计与用例骨架（已按此完成）
- `pytest-user-crud-guide/`（2026-08-29 新增）：用户模块进阶（修改/删除/新增反例）·编写提示大纲 —— 含探测事实、COUNT 技巧、顺序依赖提醒
- `pytest-trade-guide/`（2026-08-29 新增）：期货交易模块·自动化用例编写提示 —— 后端已扩展（web-app-demo 新增 8 接口/5 表），含业务公式、分组用例设计、业务闭环骨架
- 以上产物均在 TraeWork 工作目录，新对话如需可让 AI 读取
