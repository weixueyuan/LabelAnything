"""
物体属性标注工具 - 模块化版本

模块化架构，易于扩展和维护
"""

__version__ = "2.0.0"
__author__ = "Your Name"

from .config import FIELD_CONFIG, UI_CONFIG, PATH_CONFIG
from .field_processor import FieldProcessor
from .data_handler import DataHandler
from .ui_builder import UIBuilder

__all__ = [
    'FIELD_CONFIG',
    'UI_CONFIG',
    'PATH_CONFIG',
    'FieldProcessor',
    'DataHandler',
    'UIBuilder',
]

