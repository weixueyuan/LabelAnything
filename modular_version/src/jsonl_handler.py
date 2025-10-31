"""
JSONL 数据处理器：直接读写 JSONL 文件（用于调试）

提供和 DatabaseHandler 相同的接口
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict


class JSONLItem:
    """JSONL 数据项（模拟 Annotation 对象）"""
    
    def __init__(self, model_id: str, data: dict):
        self.model_id = model_id
        self.annotated = data.get('annotated', False)
        self.uid = data.get('uid', '')
        self.score = data.get('score', 1)
        
        # 业务数据（排除元数据）
        self.data = {k: v for k, v in data.items() 
                     if k not in ['annotated', 'uid', 'score']}
    
    def to_dict(self):
        """转换为字典"""
        result = {
            'annotated': self.annotated,
            'uid': self.uid,
            'score': self.score,
        }
        result.update(self.data)
        return result


class JSONLHandler:
    """JSONL 文件处理类（提供和 DatabaseHandler 相同的接口）"""
    
    def __init__(self, jsonl_path: str):
        """
        初始化 JSONL 处理器
        
        Args:
            jsonl_path: JSONL 文件路径
        """
        self.jsonl_path = jsonl_path
        self._data_cache = None  # 数据缓存
    
    def load_data(self) -> Dict[str, JSONLItem]:
        """加载所有数据（和 DatabaseHandler.load_data 接口一致）"""
        if self._data_cache is not None:
            return self._data_cache
        
        data_dict = {}
        
        if not os.path.exists(self.jsonl_path):
            print(f"⚠️  文件不存在: {self.jsonl_path}")
            return data_dict
        
        try:
            with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析：{"model_id": {属性字典}}
                    item = json.loads(line)
                    
                    for model_id, attrs in item.items():
                        data_dict[model_id] = JSONLItem(model_id, attrs)
            
            self._data_cache = data_dict
            return data_dict
            
        except Exception as e:
            print(f"❌ 加载 JSONL 失败: {e}")
            return {}
    
    def parse_item(self, item: JSONLItem) -> Dict:
        """解析单条数据（和 DatabaseHandler.parse_item 接口一致）"""
        if isinstance(item, JSONLItem):
            result = item.to_dict()
            
            # 预处理 placement：数组转字符串（UI 显示需要）
            if 'placement' in result and isinstance(result['placement'], list):
                result['placement'] = ', '.join(result['placement'])
            
            return result
        return {}
    
    def save_item(self, model_id: str, data: Dict, score: int = 1, uid: str = None):
        """
        保存单条数据（和 DatabaseHandler.save_item 接口一致）
        
        会更新缓存并写回文件
        """
        try:
            # 更新缓存
            if self._data_cache is None:
                self._data_cache = self.load_data()
            
            if model_id in self._data_cache:
                item = self._data_cache[model_id]
                item.annotated = True
                item.uid = uid if uid else data.get('uid', item.uid)
                item.score = score
                # 更新业务数据（排除元数据字段）
                item.data = {k: v for k, v in data.items() 
                            if k not in ['uid', 'annotated', 'score']}
            
            # 写回文件
            self._save_to_file()
            
            # 清除缓存，确保下次读取时从文件加载最新数据（用于修改检测）
            self._data_cache = None
            
            return True
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def _save_to_file(self):
        """将缓存写回 JSONL 文件"""
        # 备份原文件
        if os.path.exists(self.jsonl_path):
            backup_dir = os.path.join(os.path.dirname(self.jsonl_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{ts}.jsonl")
            shutil.copy2(self.jsonl_path, backup_file)
        
        # 写入新数据
        with open(self.jsonl_path, 'w', encoding='utf-8') as f:
            for model_id, item in self._data_cache.items():
                # 构建完整数据（包含元数据）
                full_data = {
                    'annotated': item.annotated,
                    'uid': item.uid,
                    'score': item.score,
                }
                full_data.update(item.data)
                
                # 处理 placement：字符串转数组
                if 'placement' in full_data and isinstance(full_data['placement'], str):
                    full_data['placement'] = [x.strip() for x in full_data['placement'].split(',') if x.strip()]
                
                # 写入 JSONL 格式
                line_obj = {model_id: full_data}
                f.write(json.dumps(line_obj, ensure_ascii=False) + '\n')
        
        print(f"💾 已保存到: {self.jsonl_path}")
    
    def get_statistics(self) -> Dict:
        """获取统计信息（和 DatabaseHandler.get_statistics 接口一致）"""
        if self._data_cache is None:
            self._data_cache = self.load_data()
        
        total = len(self._data_cache)
        annotated = sum(1 for item in self._data_cache.values() if item.annotated)
        
        return {
            'total': total,
            'annotated': annotated,
            'pending': total - annotated
        }
    
    def close(self):
        """关闭（占位方法，保持接口一致）"""
        pass

