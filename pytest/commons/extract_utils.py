import jsonpath


def extract_value(resp,attr_name,exp):
    if attr_name == 'db':
        data = resp
    elif attr_name == 'json':
        try:
            data = resp.json()
        except Exception:
            data = {}
    elif attr_name == 'headers':
        data = dict(resp.headers)
    elif attr_name == 'cookies':
        data = dict(resp.cookies)
    else:
        data = getattr(resp,attr_name,None)

    try:
        res = jsonpath.jsonpath(data,exp)
    except Exception:
        res = False
    return res[0] if res else None