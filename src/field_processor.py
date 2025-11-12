"""
字段处理器：处理不同类型字段的读取和保存

支持的处理类型：
- None: 不处理，直接返回原值
- 'array_to_string': 数组 <-> 逗号分隔字符串
- 'json': 对象 <-> JSON字符串
"""

import json
from typing import Any, Dict


class FieldProcessor:
    """字段处理器类"""
    
    @staticmethod
    def process_load(field_config: Dict, value: Any) -> Any:
        """
        加载时处理字段值
        
        Args:
            field_config: 字段配置字典
            value: 原始值
            
        Returns:
            处理后的值（用于UI显示）
        """
        process_type = field_config.get('process', None)
        
        if process_type == 'array_to_string':
            # 将数组转为逗号分隔字符串
            if isinstance(value, list):
                return ', '.join(str(v) for v in value)
            return value or ''
        
        elif process_type == 'json':
            # 将对象转为JSON字符串
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False, indent=2)
            return value or ''
        
        # 默认：不处理
        return value or ''
    
    @staticmethod
    def process_save(field_config: Dict, value: Any) -> Any:
        """
        保存时处理字段值
        
        Args:
            field_config: 字段配置字典
            value: UI输入的值
            
        Returns:
            处理后的值（用于保存到数据库）
        """
        process_type = field_config.get('process', None)
        field_type = field_config.get('type')

        # 1. 根据 'process' 类型进行转换
        if process_type == 'array_to_string':
            if isinstance(value, str):
                return [item.strip() for item in value.split(',') if item.strip()]
            return value if isinstance(value, list) else []
        
        elif process_type == 'json':
            if isinstance(value, str) and value.strip():
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value # 如果解析失败，返回原字符串
            return value or {}

        # 2. 根据组件 'type' 进行最终格式化
        if field_type == 'multiselect':
            # multiselect 组件的返回值本身就应该是列表
            return value if isinstance(value, list) else []
            
        # 3. 默认：不处理，返回原值
        return value
    
    @staticmethod
    def get_checkbox_key(field_key: str) -> str:
        """
        获取勾选框的key
        
        Args:
            field_key: 字段key
            
        Returns:
            勾选框key（格式: chk_{field_key}）
        """
        return f"chk_{field_key}"
    
    @staticmethod
    def extract_checkbox_keys(field_configs: list) -> list:
        """
        提取所有勾选框的key
        
        Args:
            field_configs: 字段配置列表
            
        Returns:
            勾选框key列表
        """
        return [
            FieldProcessor.get_checkbox_key(f['key'])
            for f in field_configs
            if f.get('has_checkbox', False)
        ]

