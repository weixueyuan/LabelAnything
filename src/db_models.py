"""
数据库模型：通用数据库模型，支持多任务多数据库

新架构特性：
- 支持多个数据库文件（每个任务一个数据库）
- 使用 JSON 字段存储动态业务数据
- 不再依赖 db_config.py
"""

from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, DateTime, Float, JSON, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Annotation(Base):
    """
    标注记录表（通用版本）
    
    使用 JSON 字段存储所有业务数据，支持不同任务的不同字段
    """
    __tablename__ = 'annotations'
    
    # 主键
    model_id = Column(String(255), primary_key=True, comment='模型ID')
    
    # 元数据字段（所有任务共有）
    annotated = Column(Boolean, default=False, nullable=False, comment='是否已标注')
    uid = Column(String(100), default='', nullable=False, comment='标注者ID')
    score = Column(Integer, default=1, nullable=False, comment='质量分数')
    modified = Column(Boolean, default=False, nullable=False, comment='是否已修改（标注后数据是否发生变化）')
    
    # 业务数据（JSON格式，存储所有字段）
    data = Column(JSON, default={}, comment='业务数据JSON')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            包含元数据和业务数据的完整字典
        """
        result = {
            'annotated': self.annotated,
            'uid': self.uid,
            'score': self.score,
            'modified': self.modified,
        }
        
        # 合并业务数据
        if self.data:
            result.update(self.data)
        
        return result
    



# ========================
# 数据库引擎和会话
# ========================

def get_engine(db_path: str = None):
    """
    获取数据库引擎
    
    Args:
        db_path: 数据库文件路径（如 "databases/annotation.db"）
                如果为None，使用默认路径 "annotations.db"
    
    Returns:
        SQLAlchemy engine对象
    """
    if db_path is None:
        db_path = "annotations.db"
    
    # 确保目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # 创建引擎
    db_url = f"sqlite:///{db_path}"
    return create_engine(db_url, echo=False)


def get_session(db_path: str = None):
    """
    获取数据库会话
    
    Args:
        db_path: 数据库文件路径
    
    Returns:
        SQLAlchemy session对象
    """
    engine = get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()


def migrate_database(db_path: str = None):
    """
    迁移数据库：为现有表添加缺失的列（参考 score 的处理方式）
    
    Args:
        db_path: 数据库文件路径
    """
    engine = get_engine(db_path)
    
    # 检查表是否存在
    inspector = inspect(engine)
    
    if 'annotations' in inspector.get_table_names():
        # 表已存在，检查列
        columns = [col['name'] for col in inspector.get_columns('annotations')]
        
        # 检查并添加缺失的列（参考 score 的处理方式，设置默认值）
        with engine.connect() as conn:
            if 'modified' not in columns:
                try:
                    # 添加 modified 列，默认值为 False（参考 score 的 default=1）
                    conn.execute(text("ALTER TABLE annotations ADD COLUMN modified BOOLEAN DEFAULT 0 NOT NULL"))
                    conn.commit()
                    print(f"✅ 已添加 modified 列到数据库: {db_path or 'annotations.db'}")
                except Exception as e:
                    print(f"⚠️  添加 modified 列时出错: {e}")
                    conn.rollback()


def init_database(db_path: str = None):
    """
    初始化数据库（创建所有表，并迁移现有表）
    
    Args:
        db_path: 数据库文件路径
    """
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    
    # 迁移现有数据库（添加缺失的列，参考 score 的处理方式）
    migrate_database(db_path)
    
    print(f"✅ 数据库初始化完成: {db_path or 'annotations.db'}")


if __name__ == "__main__":
    # 测试：创建数据库
    init_database("test.db")

