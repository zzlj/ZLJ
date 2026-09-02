import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure

from commons.yaml_unit import load_yaml
from commons.runner_utils import runner

# 第4点：用 __file__ 拼绝对路径，不依赖"在哪执行"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
# 第3、4点：glob 只收集 data/ 下 test_*.yaml，逐个 load_yaml 后合并
# 空文件/解析失败返回 None 时跳过，避免 cases.extend(None) 崩溃
def collect_cases():
    cases = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, 'test_*.yaml'))):
        print(f'加载文件 {path}')
        data = load_yaml(path)
        if not data:
            print(f'跳过空文件或解析失败: {path}')
            continue
        cases.extend(data)
    return cases

all_cases = collect_cases()

@pytest.mark.parametrize('data', all_cases, ids=[c['name'] for c in all_cases])
@pytest.mark.api
def test_yaml(data,auth_token):
    my_var = {'token':auth_token}
    allure.dynamic.title(data['name'])
    for step in data['steps']:
        for k,v in step.items():
            runner(k,v,my_var)