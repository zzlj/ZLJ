import yaml


def load_yaml(path):
    with open(path,'r',encoding='utf-8') as f:
        try:
            s = f.read()
            data = yaml.safe_load(s)
            return data
        except Exception:
            print('Yaml文件有误，请检查后重试')
            

# a = load_yaml('pytest/data/zlj.yaml')
# print(a)

