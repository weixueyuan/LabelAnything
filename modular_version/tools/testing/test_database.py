#!/usr/bin/env python
"""
数据库测试工具

测试数据库连接、数据完整性等
"""

import sqlite3
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / 'databases' / 'annotation.db'


def test_database_exists():
    """测试数据库文件是否存在"""
    if not DB_PATH.exists():
        print("❌ 数据库文件不存在")
        return False
    print("✅ 数据库文件存在")
    return True


def test_database_structure():
    """测试数据库表结构"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='annotations'")
        if not cursor.fetchone():
            print("❌ annotations表不存在")
            return False
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(annotations)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        required_columns = {
            'model_id': 'VARCHAR(255)',
            'annotated': 'BOOLEAN',
            'uid': 'VARCHAR(100)',
            'score': 'INTEGER',
            'data': 'JSON',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in columns:
                print(f"❌ 缺少字段: {col_name}")
                return False
        
        print("✅ 数据库表结构正确")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库结构测试失败: {e}")
        return False


def test_data_integrity():
    """测试数据完整性"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查数据总数
        cursor.execute("SELECT COUNT(*) FROM annotations")
        total = cursor.fetchone()[0]
        
        if total == 0:
            print("⚠️  数据库为空")
            return False
        
        print(f"✅ 数据总数: {total:,} 条")
        
        # 检查数据JSON格式
        cursor.execute("SELECT model_id, data FROM annotations LIMIT 10")
        for model_id, data_json in cursor.fetchall():
            try:
                data = json.loads(data_json)
                # 检查必要字段
                if 'category' not in data:
                    print(f"⚠️  记录 {model_id} 缺少 category 字段")
            except json.JSONDecodeError:
                print(f"❌ 记录 {model_id} 的JSON格式错误")
                return False
        
        print("✅ 数据格式正确")
        
        # 检查是否有image_url字段
        cursor.execute("SELECT data FROM annotations LIMIT 1")
        data = json.loads(cursor.fetchone()[0])
        if 'image_url' in data:
            print("✅ image_url 字段已添加")
        else:
            print("⚠️  缺少 image_url 字段")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据完整性测试失败: {e}")
        return False


def test_database_query():
    """测试数据库查询性能"""
    try:
        import time
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 测试查询速度
        start = time.time()
        cursor.execute("SELECT COUNT(*) FROM annotations")
        cursor.fetchone()
        elapsed = time.time() - start
        
        print(f"✅ 查询性能: {elapsed*1000:.2f}ms")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 查询测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("数据库测试")
    print("="*60)
    
    tests = [
        ("数据库文件", test_database_exists),
        ("表结构", test_database_structure),
        ("数据完整性", test_data_integrity),
        ("查询性能", test_database_query),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n测试: {name}")
        print("-" * 60)
        result = test_func()
        results.append((name, result))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20} {status}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    print("="*60 + "\n")
    
    return all(r for _, r in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)



