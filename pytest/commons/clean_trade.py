"""交易模块数据清理工具：清空订单/持仓/结算，重置账户余额与合约最新价。

用法：
    单独运行（命令行）：python -m pytest.commons.clean_trade
    留作工具函数：  from commons.clean_trade import clean_trade; clean_trade()
"""
import pymysql
from pymysql.cursors import DictCursor

# 数据库凭据统一从 commons/config.py 获取（环境变量优先），
# 不再在业务代码里硬编码账号密码。
try:
    from commons.config import DB_CONFIG
except ImportError:
    from config import DB_CONFIG

# 与 db.py 中预置合约的初始最新价保持一致
SEED_PRICE = {"IF2509": 3980.0, "CU2509": 72000.0, "AU2508": 560.0}

RESET_CASH = 1000000.00


def clean_trade():
    """清空交易相关数据，并将账户与合约恢复到初始状态。"""
    conn = pymysql.connect(cursorclass=DictCursor, **DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM orders")
            cur.execute("DELETE FROM positions")
            cur.execute("DELETE FROM settlements")
            cur.execute(f"UPDATE accounts SET cash = {RESET_CASH}")
            for code, price in SEED_PRICE.items():
                cur.execute("UPDATE contracts SET last_price = %s WHERE code = %s", (price, code))
        conn.commit()
    finally:
        conn.close()


def reset_trade_cash():
    """仅重置用户在 accounts 中的可用资金为初始值（不清理订单/持仓/结算）。"""
    conn = pymysql.connect(cursorclass=DictCursor, **DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE accounts SET cash = {RESET_CASH}")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    clean_trade()
    print("完成：orders/positions/settlements 已清空，accounts 重置为100万，合约最新价已恢复初始值。")