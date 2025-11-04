#!/usr/bin/env python
"""
快速检查数据库中的数据状态
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db_models import Annotation, get_session

def check_database(db_path="databases/annotation.db"):
    """检查数据库状态"""
    
    print("🔍 数据库诊断")
    print("=" * 60)
    
    session = get_session(db_path)
    
    # 随机取5条记录检查
    annotations = session.query(Annotation).limit(5).all()
    
    print(f"\n📊 前5条记录详情:\n")
    
    for i, ann in enumerate(annotations, 1):
        print(f"记录 {i}:")
        print(f"  Model ID: {ann.model_id}")
        print(f"  Annotated: {ann.annotated}")
        print(f"  UID: {ann.uid if ann.uid else '(未分配)'}")
        print(f"  Score: {ann.score}")
        print(f"  Data字段内容: {ann.data}")
        print(f"  转换后的字典: {ann.to_dict()}")
        print("-" * 60)
    
    # 统计
    total = session.query(Annotation).count()
    empty_data = session.query(Annotation).filter(Annotation.data == {}).count()
    null_data = session.query(Annotation).filter(Annotation.data == None).count()
    
    print(f"\n📈 数据统计:")
    print(f"  总记录数: {total}")
    print(f"  data字段为空字典的: {empty_data}")
    print(f"  data字段为NULL的: {null_data}")
    print(f"  data字段有内容的: {total - empty_data - null_data}")
    
    # 检查有uid但data为空的记录
    assigned_empty = session.query(Annotation).filter(
        Annotation.uid != '',
        Annotation.data == {}
    ).count()
    
    if assigned_empty > 0:
        print(f"\n⚠️  警告: {assigned_empty} 条记录已分配用户但data为空")
        print("     这可能是由于'浏览即占有'逻辑清空了数据")
        
        # 显示几条示例
        examples = session.query(Annotation).filter(
            Annotation.uid != '',
            Annotation.data == {}
        ).limit(3).all()
        
        print("\n     示例记录:")
        for ex in examples:
            print(f"     - {ex.model_id} (uid={ex.uid}, annotated={ex.annotated})")
    
    session.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='检查数据库状态')
    parser.add_argument('--db', default='databases/annotation.db', help='数据库路径')
    args = parser.parse_args()
    
    check_database(args.db)

