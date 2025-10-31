"""
数据处理模块：处理数据的加载、解析和保存

支持JSONL格式和JSON格式
支持原始格式和已标注格式
"""

import os
import json
import re
import shutil
from datetime import datetime
from typing import Dict, Any
from config import FIELD_CONFIG
from field_processor import FieldProcessor


class DataHandler:
    """数据处理类"""
    
    def __init__(self, data_file: str):
        """
        初始化数据处理器
        
        Args:
            data_file: 数据文件路径
        """
        self.data_file = data_file
        self.field_processor = FieldProcessor()
        self.field_configs = FIELD_CONFIG
    
    def load_data(self) -> Dict:
        """
        加载数据文件（自动识别格式）
        
        Returns:
            数据字典 {key: value}
        """
        if self.data_file.endswith('.jsonl'):
            return self.load_jsonl()
        else:
            return self.load_json()
    
    def load_jsonl(self) -> Dict:
        """
        加载JSONL格式文件
        
        Returns:
            数据字典
        """
        data_dict = {}
        with open(self.data_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        data_dict.update(item)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ 跳过无效行: {line[:50]}... 错误: {e}")
        return data_dict
    
    def load_json(self) -> Dict:
        """
        加载JSON格式文件
        
        Returns:
            数据字典
        """
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
        
        data_dict = {}
        for item in data_list:
            data_dict.update(item)
        return data_dict
    
    def parse_item(self, value_data: Any) -> Dict:
        """
        解析单个数据项，返回标准化的字段字典
        
        直接从数据中提取字段，有就显示，没有就留空
        元数据（annotated、uid、score）也直接存储在数据中
        
        Args:
            value_data: 原始数据值
            
        Returns:
            标准化的属性字典（包含所有字段和元数据）
        """
        if not isinstance(value_data, dict):
            return self._empty_attrs()
        
        # 兼容旧格式：如果包含'data'字段（旧的嵌套格式）
        if 'data' in value_data:
            return self._parse_annotated(value_data)
        
        # 新格式：直接从数据中读取（扁平结构）
        return self._parse_simple(value_data)
    
    def _parse_simple(self, value_data: Dict) -> Dict:
        """
        简化版解析：直接从数据中提取字段
        
        Args:
            value_data: 数据字典
            
        Returns:
            属性字典
        """
        attrs = {
            'annotated': value_data.get('annotated', False),
            'uid': value_data.get('uid', ''),
            'score': value_data.get('score', 1)
        }
        
        # 直接用key从数据中提取，有就显示，没有就留空
        for field_conf in self.field_configs:
            key = field_conf['key']
            value = value_data.get(key, '')  # 直接用key查找，不需要映射
            
            # 字段处理（如数组转字符串）
            attrs[key] = self.field_processor.process_load(field_conf, value)
            
            # 勾选框状态
            if field_conf.get('has_checkbox', False):
                chk_key = self.field_processor.get_checkbox_key(key)
                attrs[chk_key] = value_data.get(chk_key, False)
        
        return attrs
    
    def _parse_annotated(self, value_data: Dict) -> Dict:
        """
        解析已标注格式数据
        
        Args:
            value_data: 已标注数据（包含'data'字段）
            
        Returns:
            属性字典
        """
        value_str = value_data.get('data', '')
        annotated = value_data.get('annotated', False)
        uid = value_data.get('uid', '')
        score = value_data.get('score', 1)
        
        # 提取JSON内容
        json_match = re.search(r'```json\s*\n(.*?)\n```', value_str, re.DOTALL)
        if json_match:
            try:
                attrs = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                attrs = {}
        else:
            attrs = {}
        
        # 处理每个字段
        for field_conf in self.field_configs:
            key = field_conf['key']
            if key in attrs:
                attrs[key] = self.field_processor.process_load(field_conf, attrs[key])
        
        attrs['annotated'] = annotated
        attrs['uid'] = uid
        attrs['score'] = score
        
        return attrs
    
    def _empty_attrs(self) -> Dict:
        """
        返回空属性字典
        
        Returns:
            空属性字典
        """
        attrs = {'annotated': False, 'uid': '', 'score': 1}
        
        for field_conf in self.field_configs:
            attrs[field_conf['key']] = ''
            if field_conf.get('has_checkbox', False):
                attrs[self.field_processor.get_checkbox_key(field_conf['key'])] = False
        
        return attrs
    
    def build_save_data(self, field_values: Dict, checkbox_values: Dict, uid: str) -> Dict:
        """
        构建保存数据（简化版）
        
        直接返回一个扁平的字典，包含所有字段和元数据
        
        Args:
            field_values: 字段值字典 {key: value}
            checkbox_values: 勾选框值字典 {key: bool}
            uid: 用户ID
            
        Returns:
            保存数据字典（扁平结构）
        """
        # 计算score（任意勾选框被选中则为0，否则为1）
        score = 0 if any(checkbox_values.values()) else 1
        
        # 构建扁平的数据字典
        data_dict = {
            "annotated": True,
            "uid": uid,
            "score": score
        }
        
        # 添加所有字段
        for field_conf in self.field_configs:
            key = field_conf['key']
            value = field_values.get(key, '')
            
            # 字段处理（UI值 -> 保存值）
            data_dict[key] = self.field_processor.process_save(field_conf, value)
            
            # 勾选框状态
            if field_conf.get('has_checkbox', False):
                chk_key = self.field_processor.get_checkbox_key(key)
                data_dict[chk_key] = checkbox_values.get(key, False)
        
        return data_dict
    
    def save_data(self, data_dict: Dict) -> None:
        """
        保存数据到文件（自动识别格式并备份）
        
        Args:
            data_dict: 数据字典
        """
        # 备份原文件
        self._backup_file()
        
        # 根据文件扩展名选择保存格式
        if self.data_file.endswith('.jsonl'):
            self._save_jsonl(data_dict)
        else:
            self._save_json(data_dict)
        
        print(f"💾 已保存到: {self.data_file}")
    
    def _backup_file(self) -> None:
        """备份原文件到backups目录"""
        if os.path.exists(self.data_file):
            backup_dir = os.path.join(os.path.dirname(self.data_file), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保持原文件扩展名
            ext = os.path.splitext(self.data_file)[1]
            backup_file = os.path.join(backup_dir, f"backup_{ts}{ext}")
            shutil.copy2(self.data_file, backup_file)
    
    def _save_jsonl(self, data_dict: Dict) -> None:
        """保存为JSONL格式"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            for key, value in data_dict.items():
                line_obj = {key: value}
                f.write(json.dumps(line_obj, ensure_ascii=False) + '\n')
    
    def _save_json(self, data_dict: Dict) -> None:
        """保存为JSON格式"""
        data_list = [{k: v} for k, v in data_dict.items()]
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4, ensure_ascii=False)

