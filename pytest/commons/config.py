"""项目统一配置：数据库连接信息集中在此管理。

设计原则：
    凭据优先从环境变量读取，避免把账号密码硬编码进业务代码/版本库。
    若未设置环境变量，则回退到本地开发默认值（仅供本地学习环境使用）。
    生产环境务必通过环境变量注入真实凭据。

可用环境变量：
    DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME
"""
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    # 本地开发默认密码；若部署到共享/公开环境，请通过 DB_PASSWORD 环境变量注入
    "password": os.getenv("DB_PASSWORD", "zhulingjia293"),
    "database": os.getenv("DB_NAME", "user_manage"),
    "charset": "utf8mb4",
}
