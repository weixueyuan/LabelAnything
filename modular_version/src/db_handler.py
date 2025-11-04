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
    
    def assign_to_user(self, model_id: str, uid: str):
        """
        仅分配数据给用户（浏览即占有）
        
        只更新 uid 字段，不触碰其他任何数据
        
        Args:
            model_id: 模型ID
            uid: 用户ID
        """
        try:
            annotation = self.session.query(Annotation).filter_by(model_id=model_id).first()
            if annotation:
                annotation.uid = uid
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"❌ 分配失败: {e}")
            return False
    
    def save_item(self, model_id: str, data: Dict, score: int = 1, uid: str = None):
        """
        保存标注数据（实际标注保存）
        
        Args:
            model_id: 模型ID
            data: 业务数据字典
            score: 标注得分（0=有错误, 1=完成）
            uid: 用户ID
        """
        try:
            annotation = self.session.query(Annotation).filter_by(model_id=model_id).first()
            if annotation:
                # 更新标注状态和数据
                annotation.annotated = True  # 保存即标记为已标注
                annotation.uid = uid if uid else annotation.uid
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
    
    def export_to_jsonl(self, output_dir: str = "exports") -> str:
        """
        导出数据库数据为JSONL文件
        
        Args:
            output_dir: 输出目录，默认为 "exports"
            
        Returns:
            导出文件的路径
        """
        import os
        from datetime import datetime
        
        # 创建导出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名（带日期时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.jsonl"
        filepath = os.path.join(output_dir, filename)
        
        try:
            # 获取所有数据
            annotations = self.session.query(Annotation).all()
            
            # 写入JSONL文件
            with open(filepath, 'w', encoding='utf-8') as f:
                for ann in annotations:
                    # 构建完整数据（包含元数据）
                    full_data = {
                        'annotated': ann.annotated,
                        'uid': ann.uid,
                        'score': ann.score,
                    }
                    
                    # 合并业务数据
                    if ann.data:
                        full_data.update(ann.data)
                    
                    # 处理 placement：如果是字符串，转换为数组（JSONL格式）
                    if 'placement' in full_data:
                        if isinstance(full_data['placement'], str):
                            # 字符串转数组
                            full_data['placement'] = [x.strip() for x in full_data['placement'].split(',') if x.strip()]
                        elif isinstance(full_data['placement'], list):
                            # 已经是数组，保持不变
                            pass
                    
                    # 写入 JSONL 格式：{"model_id": {数据}}
                    line_obj = {ann.model_id: full_data}
                    f.write(json.dumps(line_obj, ensure_ascii=False) + '\n')
            
            print(f"✅ 导出完成: {filepath}")
            print(f"   共导出 {len(annotations)} 条记录")
            return filepath
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'session'):
            self.session.close()
