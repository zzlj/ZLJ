import pymysql

# 数据库凭据统一从 commons/config.py 获取（环境变量优先），
# 不再在业务代码里硬编码账号密码。
try:
    from commons.config import DB_CONFIG
except ImportError:
    from config import DB_CONFIG


def _get_conn():
    """创建数据库连接，参数统一取自共享配置 DB_CONFIG。"""
    return pymysql.connect(**DB_CONFIG)


def db_execute(sql, args=None):
    conn = _get_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, args)
            conn.commit()
    finally:
        conn.close()


def db_query(sql, args=None):
    conn = _get_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, args)
            rows = cur.fetchall()
            return rows
    finally:
        conn.close()

# res = db_query(f'select t.id,t.username,t.role from users t where username = %s', ('whx',))
# print(res)
