"""
移动端自动化模块
支持Android和iOS平台的快手APP自动化操作
"""
from .kuaishou_android import KuaishouAndroid
from .kuaishou_ios import KuaishouiOS
from .base_automation import BaseAutomation

__all__ = ['KuaishouAndroid', 'KuaishouiOS', 'BaseAutomation']
