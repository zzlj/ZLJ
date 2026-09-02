import pytest
import datetime
import os, sys
import requests


# 导入 commons 目录下的文件
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

#pytest 打开 log_file 早于 fixture 执行,这里在导入时确保 logs 目录存在
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'), exist_ok=True)

@pytest.fixture(autouse=True,scope='session')
def f():
    print(f'{datetime.datetime.now()} 自动化测试开始啦')
    yield 123
    print(f'{datetime.datetime.now()} 自动化测试结束啦')
    
@pytest.fixture(scope='session')
def auth_token():
    resp = requests.post(
        'http://127.0.0.1:8000/api/login',
        json={
            "username": "admin",
            "password": "123456"
        }
    )
    print('token 获取成功',resp.json()['data']['token'])
    return resp.json()['data']['token']