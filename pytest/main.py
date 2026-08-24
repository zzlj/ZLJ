import pytest
import os
import allure

pytest.main()
os.system("allure generate -o report   -c temps")