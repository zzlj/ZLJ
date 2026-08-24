import requests
import re
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from responses_validator import validator
from commons.extract_utils import extract_value

import logging

logger = logging.getLogger('ZLJ')

# 匹配 ${name} 占位符，name 只允许字母、数字、下划线
_VAR_PATTERN = re.compile(r'\$\{(\w+)\}')

def replace_var(value, my_var):
    """递归替换 dict/list/str 中的 ${name} 占位符为变量字典里的值"""
    if isinstance(value, str):
        return _VAR_PATTERN.sub(lambda m: str(my_var.get(m.group(1), m.group(0))), value)
    if isinstance(value, dict):
        return {k: replace_var(v, my_var) for k, v in value.items()}
    if isinstance(value, list):
        return [replace_var(item, my_var) for item in value]
    return value

def runner(k,v,my_var):
    match k:
        case 'request':
            logger.info(f'{v},请求开始了')
            my_var['resp'] = requests.request(**v)
        case 'response':
            logger.info(f'{v},断言开始了')
            validator(my_var['resp'],**v)
        case 'extract':
            logger.info(f'变量提取开始了')
            for var_name,var_exp in v.items():
                value = extract_value(my_var['resp'],*var_exp)
                my_var[var_name] = value
                logger.info(f'{var_name} = {value}')
        case _:
            # 必修：未知关键字直接报错，拼错不再被静默忽略
            raise ValueError(f'未知关键字: {k}')