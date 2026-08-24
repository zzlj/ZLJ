import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure

from commons.yaml_unit import load_yaml
from commons.runner_utils import runner

@pytest.mark.api
def test_yaml():
    my_var = {}
    data = load_yaml('pytest/data/test_api.yaml')
    allure.title(data['name'])
    
    for step in data['steps']:
        for k,v in step.items():
            runner(k,v,my_var)