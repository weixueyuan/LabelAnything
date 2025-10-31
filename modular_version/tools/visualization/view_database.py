#!/usr/bin/env python
"""
数据库查看工具

使用方式:
    python tools/view_database.py                    # 查看前10条
    python tools/view_database.py --limit 20         # 查看前20条
    python tools/view_database.py --search chair    # 搜索包含chair的数据
    python tools/view_database.py --model-id xxx    # 查看特定model_id
"""

import sqlite3
import json
import argparse
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'databases' / 'annotation.db'


def view_all(limit=10, offset=0):
    """查看所有数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取总数
    cursor.execute("SELECT COUNT(*) FROM annotations")
    total = cursor.fetchone()[0]
    
    # 查询数据
    cursor.execute(f"SELECT model_id, annotated, uid, score, data FROM annotations LIMIT {limit} OFFSET {offset}")
    rows = cursor.fetchall()
    
    print("="*80)
    print(f"📊 数据库查看工具 - 总数: {total} 条，显示: {offset+1}-{min(offset+limit, total)} 条")
    print("="*80)
    
    for idx, (model_id, annotated, uid, score, data_json) in enumerate(rows, offset+1):
        data = json.loads(data_json)
        status = "✅ 已标注" if annotated else "❌ 未标注"
        
        print(f"\n【记录 {idx}】")
        print(f"  Model ID:  {model_id}")
        print(f"  状态:      {status}")
        print(f"  标注者:    {uid if uid else '(无)'}")
        print(f"  分数:      {score}")
        print(f"  字段:")
        for key, value in sorted(data.items()):
            if isinstance(value, str) and len(value) > 60:
                value = value[:60] + "..."
            print(f"    {key:15} = {value}")
    
    print(f"\n{'='*80}\n")
    conn.close()


def search_data(keyword):
    """搜索数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 搜索 model_id 或 data JSON
    cursor.execute("""
        SELECT model_id, annotated, uid, score, data 
        FROM annotations 
        WHERE model_id LIKE ? OR data LIKE ?
        LIMIT 20
    """, (f'%{keyword}%', f'%{keyword}%'))
    
    rows = cursor.fetchall()
    
    print("="*80)
    print(f"🔍 搜索结果: '{keyword}' - 找到 {len(rows)} 条")
    print("="*80)
    
    if not rows:
        print("\n❌ 没有找到匹配的数据\n")
        conn.close()
        return
    
    for idx, (model_id, annotated, uid, score, data_json) in enumerate(rows, 1):
        data = json.loads(data_json)
        status = "✅" if annotated else "❌"
        
        print(f"\n【{idx}】{status} {model_id}")
        print(f"    Category: {data.get('category', 'N/A')}")
        print(f"    Material: {data.get('material', 'N/A')[:50]}...")
        if uid:
            print(f"    标注者: {uid}")
    
    print(f"\n{'='*80}\n")
    conn.close()


def view_by_id(model_id):
    """查看特定ID的详细数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT model_id, annotated, uid, score, data FROM annotations WHERE model_id = ?", (model_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"\n❌ 找不到 model_id: {model_id}\n")
        conn.close()
        return
    
    model_id, annotated, uid, score, data_json = row
    data = json.loads(data_json)
    
    print("="*80)
    print("📄 详细数据")
    print("="*80)
    print(f"\nModel ID:  {model_id}")
    print(f"状态:      {'✅ 已标注' if annotated else '❌ 未标注'}")
    print(f"标注者:    {uid if uid else '(无)'}")
    print(f"分数:      {score}")
    print(f"\n业务数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\n{'='*80}\n")
    
    conn.close()


def statistics():
    """统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 总数
    cursor.execute("SELECT COUNT(*) FROM annotations")
    total = cursor.fetchone()[0]
    
    # 已标注
    cursor.execute("SELECT COUNT(*) FROM annotations WHERE annotated = 1")
    annotated = cursor.fetchone()[0]
    
    # 按用户统计
    cursor.execute("SELECT uid, COUNT(*) FROM annotations WHERE uid != '' GROUP BY uid")
    user_stats = cursor.fetchall()
    
    # 按category统计（从JSON中提取）
    cursor.execute("SELECT json_extract(data, '$.category') as cat, COUNT(*) FROM annotations GROUP BY cat ORDER BY COUNT(*) DESC LIMIT 10")
    category_stats = cursor.fetchall()
    
    print("="*80)
    print("📊 数据库统计")
    print("="*80)
    print(f"\n总记录数:    {total}")
    print(f"已标注:      {annotated} ({annotated/total*100:.1f}%)")
    print(f"未标注:      {total - annotated} ({(total-annotated)/total*100:.1f}%)")
    
    if user_stats:
        print(f"\n按用户统计:")
        for uid, count in user_stats:
            print(f"  {uid:20} {count:6} 条")
    
    print(f"\n前10个类别:")
    for cat, count in category_stats:
        print(f"  {cat:20} {count:6} 条")
    
    print(f"\n{'='*80}\n")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description='数据库查看工具')
    parser.add_argument('--limit', '-l', type=int, default=10, help='显示条数')
    parser.add_argument('--offset', '-o', type=int, default=0, help='偏移量')
    parser.add_argument('--search', '-s', type=str, help='搜索关键词')
    parser.add_argument('--model-id', '-m', type=str, help='查看特定model_id')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    
    args = parser.parse_args()
    
    if args.stats:
        statistics()
    elif args.model_id:
        view_by_id(args.model_id)
    elif args.search:
        search_data(args.search)
    else:
        view_all(args.limit, args.offset)


if __name__ == "__main__":
    main()

