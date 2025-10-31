"""
数据库处理器：简化版
"""

import json
from typing import Dict, Any
from sqlalchemy.exc import IntegrityError
from .db_models import Annotation, get_session, init_database
from .field_processor import FieldProcessor


class DatabaseHandler:
    """数据库处理类"""
    
    def __init__(self, db_path: str = 'databases/annotation.db'):
        """
        初始化数据库处理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.field_processor = FieldProcessor()
        # 初始化数据库
        init_database(db_path)
        self.session = get_session(db_path)
    
    def load_data(self) -> Dict[str, Annotation]:
        """加载所有数据"""
        try:
            annotations = self.session.query(Annotation).all()
            return {ann.model_id: ann for ann in annotations}
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            return {}
    
    def parse_item(self, item: Annotation) -> Dict:
        """解析单条数据"""
        if isinstance(item, Annotation):
            result = item.to_dict()
            
            # 预处理 placement：数组转字符串（兼容旧版逻辑）
            if 'placement' in result and isinstance(result['placement'], list):
                result['placement'] = ', '.join(result['placement'])
            
            return result
        return {}
    
    def save_item(self, model_id: str, data: Dict, score: int = 1, uid: str = None):
        """保存单条数据"""
        try:
            annotation = self.session.query(Annotation).filter_by(model_id=model_id).first()
            if annotation:
                # 更新
                annotation.annotated = True
                annotation.uid = uid if uid else data.get('uid', annotation.uid)
                annotation.score = score
                # 更新业务数据（排除元数据字段）
                annotation.data = {k: v for k, v in data.items() if k not in ['uid', 'annotated', 'score']}
                self.session.commit()
                return True
        except Exception as e:
            self.session.rollback()
            print(f"❌ 保存失败: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            total = self.session.query(Annotation).count()
            annotated = self.session.query(Annotation).filter_by(annotated=True).count()
            return {
                'total': total,
                'annotated': annotated,
                'pending': total - annotated
            }
        except Exception as e:
            print(f"❌ 获取统计失败: {e}")
            return {'total': 0, 'annotated': 0, 'pending': 0}
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'session'):
            self.session.close()
