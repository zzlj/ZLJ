import requests
import re
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from responses_validator import validator,_match
from commons.extract_utils import extract_value
from commons.db_utils import db_query,db_execute

import logging

logger = logging.getLogger('ZLJ')

# 匹配 ${name} 占位符，name 只允许字母、数字、下划线
_VAR_PATTERN = re.compile(r'\$\{(\w+)\}')


def replace_var(value, my_var):
    """递归替换 dict/list/str 中的 ${name} 占位符为变量字典里的值"""
    # 字符串类型：将字符串中所有 ${xxx} 替换为 my_var 中对应的值
    # 若 my_var 中不存在该 key，则保留原占位符不做替换
    if isinstance(value, str):
        # 情况一：整个字符串就是单个 ${name} 占位符（如 '${id}'）
        # 此时直接返回变量的原始值，保留类型（int/float/bool 不被转成字符串）。
        # 否则后面断言数字时 '40' != 40 会类型不匹配而失败
        m = _VAR_PATTERN.fullmatch(value)
        if m and m.group(1) in my_var:
            return my_var[m.group(1)]
        # 情况二：占位符只是字符串的一部分（如 'Bearer ${token}'、'/api/users/${id}'）
        # 只能按文本拼接，用 str() 把变量值转成字符串
        return _VAR_PATTERN.sub(lambda m: str(my_var.get(m.group(1), m.group(0))), value)
    # 字典类型：递归处理每个 value，保持 key 不变
    if isinstance(value, dict):
        return {k: replace_var(v, my_var) for k, v in value.items()}
    # 列表类型：递归处理每个元素
    if isinstance(value, list):
        return [replace_var(item, my_var) for item in value]
    # 其他类型（int/float/bool/None 等）：直接返回，无需替换
    return value

def runner(k,v,my_var):
    match k:
        case 'request':
            logger.info('请求开始了')
            logger.info(v)
            v = replace_var(v,my_var)
            logger.info(f'请求参数替换后为：{v}')
            my_var['resp'] = requests.request(**v)
            logger.info(f'实际响应：{my_var["resp"].status_code} {my_var["resp"].text}')
        case 'response':
            logger.info('断言开始了')
            logger.info(v)
            # 先替换断言里的 ${变量} 为实际值，和 request 分支保持一致。
            # 否则 yaml 里写 data.id: ${id} 时，
            # 会拿字面量字符串 "${id}" 和实际返回的 36 比较 → 断言必失败
            v = replace_var(v,my_var)
            validator(my_var['resp'],**v)
        case 'db':
            logger.info('数据库操作开始了')
            logger.info(v)
            v = replace_var(v,my_var)
            # 有 execute：先执行写操作（如前置清理 DELETE）
            if 'execute' in v:
                db_execute(v['execute'],v.get('args'))
            # 有 sql：执行查询
            if 'sql' in v:
                db_res = db_query(v['sql'],v.get('args'))
                my_var['db_result'] = db_res
            # 有 expect：对查询结果做断言
            if 'expect' in v:
                expect = replace_var(v['expect'],my_var)
                _match(expect,my_var['db_result'],'db')
        case 'extract':
            logger.info('变量提取开始了')
            logger.info(v)
            for var_name,var_exp in v.items():
                # var_exp 形如 [来源, jsonpath表达式]，例如 ['db', '$.[0].id']
                # 来源是 'db' 时，从数据库查询结果 my_var['db_result'] 提取；
                # 其他来源（json/headers/cookies）仍从 HTTP 响应 my_var['resp'] 提取。
                # 注意必须先用来源判断：db 提取可能发生在任何请求之前，
                # 此时 my_var['resp'] 还不存在，直接访问会 KeyError。
                if var_exp[0] == 'db':
                    value = extract_value(my_var['db_result'],*var_exp)
                else:
                    value = extract_value(my_var['resp'],*var_exp)
                my_var[var_name] = value
                logger.info(f'{var_name} = {value}')
        case _:
            # 必修：未知关键字直接报错，拼错不再被静默忽略
            raise ValueError(f'未知关键字: {k}')