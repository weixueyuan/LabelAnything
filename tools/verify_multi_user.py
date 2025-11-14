#!/usr/bin/env python
"""
多用户标注功能验证工具

检查数据库中的用户分配情况,验证多人标注功能是否正常工作
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def verify_multi_user(db_path="databases/annotation.db"):
    """验证数据库中的多用户数据"""
    
    db_file = project_root / db_path
    if not db_file.exists():
        print(f"❌ 数据库不存在: {db_file}")
        print(f"   请先运行: python -m importers.generic_importer")
        return
    
    print("🔍 多用户标注验证")
    print("=" * 60)
    
    # 连接数据库
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 1. 统计总体情况
    cursor.execute("SELECT COUNT(*) FROM annotations")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM annotations WHERE uid IS NULL OR uid = ''")
    unassigned = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM annotations WHERE uid IS NOT NULL AND uid != ''")
    assigned = cursor.fetchone()[0]
    
    print(f"\n📊 数据统计:")
    print(f"  总数据量: {total}")
    print(f"  未分配: {unassigned} ({unassigned/total*100:.1f}%)")
    print(f"  已分配: {assigned} ({assigned/total*100:.1f}%)")
    
    # 2. 各用户标注情况
    cursor.execute("""
        SELECT uid, COUNT(*) 
        FROM annotations 
        WHERE uid IS NOT NULL AND uid != ''
        GROUP BY uid
        ORDER BY COUNT(*) DESC
    """)
    user_stats = cursor.fetchall()
    
    if user_stats:
        print(f"\n👥 各用户标注量:")
        for uid, count in user_stats:
            percentage = count / total * 100
            bar_length = int(percentage / 2)
            bar = "█" * bar_length
            print(f"  {uid:15s}: {count:4d} ({percentage:5.1f}%) {bar}")
    else:
        print(f"\n⚠️  暂无用户标注数据")
    
    # 3. 检查重复标注(理论上不应该发生)
    cursor.execute("""
        SELECT model_id, COUNT(DISTINCT uid) as user_count
        FROM annotations
        WHERE uid IS NOT NULL AND uid != ''
        GROUP BY model_id
        HAVING user_count > 1
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\n⚠️  发现重复标注 (同一数据被多人标注):")
        for model_id, count in duplicates[:10]:
            print(f"  {model_id}: {count} 个用户")
        if len(duplicates) > 10:
            print(f"  ... 还有 {len(duplicates) - 10} 条")
    else:
        print(f"\n✅ 无重复标注 (数据隔离正常)")
    
    # 4. 最近标注活动
    cursor.execute("""
        SELECT uid, model_id, updated_at
        FROM annotations
        WHERE uid IS NOT NULL AND uid != ''
        ORDER BY updated_at DESC
        LIMIT 10
    """)
    recent = cursor.fetchall()
    
    if recent:
        print(f"\n📝 最近标注活动:")
        for uid, model_id, updated_at in recent:
            print(f"  {updated_at} | {uid:15s} | {model_id[:30]}")
    
    # 5. 验证数据隔离逻辑
    print(f"\n🔒 验证数据隔离逻辑:")
    
    # 模拟用户1视角
    test_user = "weixueyuan"
    cursor.execute("""
        SELECT COUNT(*) 
        FROM annotations 
        WHERE uid IS NULL OR uid = '' OR uid = ?
    """, (test_user,))
    visible_to_user = cursor.fetchone()[0]
    print(f"  用户 '{test_user}' 可见数据: {visible_to_user}")
    
    # 模拟用户2视角
    test_user2 = "annotator2"
    cursor.execute("""
        SELECT COUNT(*) 
        FROM annotations 
        WHERE uid IS NULL OR uid = '' OR uid = ?
    """, (test_user2,))
    visible_to_user2 = cursor.fetchone()[0]
    print(f"  用户 '{test_user2}' 可见数据: {visible_to_user2}")
    
    if visible_to_user == visible_to_user2 == total:
        print(f"  ⚠️  两用户可见数据相同且等于总量,可能还没开始标注")
    elif visible_to_user + visible_to_user2 - unassigned == total:
        print(f"  ✅ 数据隔离正常 (两用户可见数据总和 = 总量 + 未分配)")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ 验证完成")
    print("\n💡 提示:")
    print("  - 使用不同用户登录标注,观察数据变化")
    print("  - 再次运行本脚本查看更新后的统计")

def show_user_view(db_path="databases/annotation.db", username=None):
    """显示特定用户的视角"""
    
    db_file = project_root / db_path
    if not db_file.exists():
        print(f"❌ 数据库不存在: {db_file}")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    if username:
        cursor.execute("""
            SELECT model_id, uid, annotated, updated_at
            FROM annotations
            WHERE uid IS NULL OR uid = '' OR uid = ?
            ORDER BY updated_at DESC
            LIMIT 20
        """, (username,))
        print(f"\n👤 用户 '{username}' 视角 (最近20条):")
    else:
        cursor.execute("""
            SELECT model_id, uid, annotated, updated_at
            FROM annotations
            ORDER BY updated_at DESC
            LIMIT 20
        """)
        print(f"\n📋 全局视角 (最近20条):")
    
    print("-" * 80)
    print(f"{'Model ID':<40} {'User':<15} {'Status':<10} {'Updated'}")
    print("-" * 80)
    
    results = cursor.fetchall()
    for model_id, uid, annotated, updated_at in results:
        uid_display = uid if uid else "(未分配)"
        status = "✅ 已标注" if annotated else "❌ 未标注"
        print(f"{model_id[:40]:<40} {uid_display:<15} {status:<10} {updated_at}")
    
    conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='验证多用户标注功能')
    parser.add_argument('--db', default='databases/annotation.db', help='数据库路径')
    parser.add_argument('--user', help='查看特定用户视角')
    parser.add_argument('--view', action='store_true', help='显示数据列表')
    
    args = parser.parse_args()
    
    if args.view:
        show_user_view(args.db, args.user)
    else:
        verify_multi_user(args.db)

