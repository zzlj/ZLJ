"""
响应断言模块：YAML 里 response 步骤写什么就校验什么，没写的不检查。
递归匹配规则：dict 按 key 匹配、list 按索引匹配、其他类型按 == 匹配。
"""


def _match(expect, actual, path):
    """递归断言 expect(期望) 与 actual(实际) 是否匹配"""
    if isinstance(expect, dict):
        assert isinstance(actual, dict), f'断言失败: {path} 期望是 dict, 实际是 {type(actual).__name__}'
        for k, v in expect.items():
            assert k in actual, f'断言失败: {path}.{k} 不存在'
            _match(v, actual[k], f'{path}.{k}')
    elif isinstance(expect, list):
        assert isinstance(actual, list), f'断言失败: {path} 期望是 list, 实际是 {type(actual).__name__}'
        assert len(actual) >= len(expect), f'断言失败: {path} 期望长度 {len(expect)}, 实际长度 {len(actual)}'
        for i, v in enumerate(expect):
            _match(v, actual[i], f'{path}[{i}]')
    else:
        try:
            expect_num = float(expect)
            actual_num = float(actual)
        except (TypeError,ValueError):
            assert expect == actual, f'断言失败：{path} 期望{expect!r}, 实际{actual!r}'
        else:   
            assert expect_num == actual_num, f'断言失败：{path} 期望{expect!r}, 实际{actual!r}'


def validator(resp, **kwargs):
    """
    按 response 步骤里的断言项校验，支持 status_code / json / headers / text。
    例：validator(resp, status_code=200, json={'code': 0})
    """
    for attr_name, expect in kwargs.items():
        if attr_name == 'status_code':
            actual = resp.status_code
        elif attr_name == 'json':
            try:
                actual = resp.json()
            except Exception:
                actual = None
        elif attr_name in ('headers', 'cookies'):
            actual = dict(getattr(resp, attr_name))
        elif attr_name == 'text':
            actual = resp.text
        else:
            actual = getattr(resp, attr_name, None)
        _match(expect, actual, attr_name)
