import yaml
import os


def load_yaml(path):
    # 以 UTF-8 编码读取 YAML 文件内容。
    with open(path,'r',encoding='utf-8') as f:
        try:
            s = f.read()
            # 将 YAML 文本解析为 Python 对象并返回。
            data = yaml.safe_load(s)
            return data
        except Exception:
            # 文件内容格式错误时提示用户检查 YAML 文件。
            print('Yaml文件有误，请检查后重试')
            

# a = load_yaml('pytest/data/test_login.yaml')
# print(a)


