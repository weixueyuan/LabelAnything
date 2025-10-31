#!/usr/bin/env python
"""
数据库可视化查看工具（Gradio界面）

使用方式:
    python tools/view_database_ui.py
    
然后在浏览器打开显示的地址
"""

import sqlite3
import json
import gradio as gr
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'databases' / 'annotation.db'


def get_statistics():
    """获取统计信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 总数
    cursor.execute("SELECT COUNT(*) FROM annotations")
    total = cursor.fetchone()[0]
    
    # 已标注
    cursor.execute("SELECT COUNT(*) FROM annotations WHERE annotated = 1")
    annotated = cursor.fetchone()[0]
    
    # 按category统计
    cursor.execute("""
        SELECT json_extract(data, '$.category') as cat, COUNT(*) 
        FROM annotations 
        GROUP BY cat 
        ORDER BY COUNT(*) DESC 
        LIMIT 10
    """)
    category_stats = cursor.fetchall()
    
    conn.close()
    
    stats_text = f"""
## 📊 数据库统计

- **总记录数**: {total:,} 条
- **已标注**: {annotated:,} 条 ({annotated/total*100:.1f}%)
- **未标注**: {total-annotated:,} 条 ({(total-annotated)/total*100:.1f}%)

### 前10个类别:
"""
    for cat, count in category_stats:
        stats_text += f"\n- **{cat}**: {count:,} 条"
    
    return stats_text


def view_records(page=1, per_page=10):
    """分页查看记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    
    cursor.execute("SELECT COUNT(*) FROM annotations")
    total = cursor.fetchone()[0]
    
    cursor.execute(f"""
        SELECT model_id, annotated, uid, score, data 
        FROM annotations 
        LIMIT {per_page} OFFSET {offset}
    """)
    rows = cursor.fetchall()
    
    conn.close()
    
    if not rows:
        return "没有更多数据", None
    
    # 构建表格数据
    table_data = []
    for model_id, annotated, uid, score, data_json in rows:
        data = json.loads(data_json)
        status = "✅" if annotated else "❌"
        table_data.append([
            model_id[:40] + "..." if len(model_id) > 40 else model_id,
            status,
            data.get('category', 'N/A'),
            data.get('material', 'N/A')[:30] + "..." if len(data.get('material', '')) > 30 else data.get('material', 'N/A'),
            uid if uid else '-',
            score
        ])
    
    total_pages = (total + per_page - 1) // per_page
    info = f"第 {page}/{total_pages} 页，共 {total:,} 条记录"
    
    return table_data, info


def search_records(keyword):
    """搜索记录"""
    if not keyword:
        return [], "请输入搜索关键词"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT model_id, annotated, uid, score, data 
        FROM annotations 
        WHERE model_id LIKE ? OR data LIKE ?
        LIMIT 50
    """, (f'%{keyword}%', f'%{keyword}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return [], f"没有找到包含 '{keyword}' 的记录"
    
    table_data = []
    for model_id, annotated, uid, score, data_json in rows:
        data = json.loads(data_json)
        status = "✅" if annotated else "❌"
        table_data.append([
            model_id[:40] + "..." if len(model_id) > 40 else model_id,
            status,
            data.get('category', 'N/A'),
            data.get('material', 'N/A')[:30] + "..." if len(data.get('material', '')) > 30 else data.get('material', 'N/A'),
            uid if uid else '-',
            score
        ])
    
    return table_data, f"找到 {len(rows)} 条记录"


def view_detail(model_id):
    """查看详细信息"""
    if not model_id:
        return "请输入 Model ID"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT model_id, annotated, uid, score, data FROM annotations WHERE model_id = ?", (model_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return f"找不到 Model ID: {model_id}"
    
    model_id, annotated, uid, score, data_json = row
    data = json.loads(data_json)
    
    detail_text = f"""
## 📄 详细信息

**Model ID**: `{model_id}`

**状态**: {'✅ 已标注' if annotated else '❌ 未标注'}

**标注者**: {uid if uid else '(无)'}

**分数**: {score}

### 业务数据:

```json
{json.dumps(data, indent=2, ensure_ascii=False)}
```
"""
    return detail_text


# 创建界面
with gr.Blocks(title="数据库查看工具") as demo:
    gr.Markdown("# 🗄️ 数据库可视化查看工具")
    
    with gr.Tabs():
        # Tab 1: 统计信息
        with gr.Tab("📊 统计"):
            stats_output = gr.Markdown(get_statistics())
            gr.Button("🔄 刷新统计").click(
                fn=get_statistics,
                outputs=stats_output
            )
        
        # Tab 2: 浏览数据
        with gr.Tab("📖 浏览"):
            with gr.Row():
                page_num = gr.Number(label="页码", value=1, precision=0)
                per_page = gr.Number(label="每页条数", value=10, precision=0)
            
            browse_btn = gr.Button("📄 查看", variant="primary")
            browse_info = gr.Textbox(label="信息", interactive=False)
            browse_table = gr.Dataframe(
                headers=["Model ID", "状态", "Category", "Material", "标注者", "分数"],
                label="数据列表"
            )
            
            browse_btn.click(
                fn=view_records,
                inputs=[page_num, per_page],
                outputs=[browse_table, browse_info]
            )
            
            # 初始加载
            demo.load(
                fn=view_records,
                inputs=[page_num, per_page],
                outputs=[browse_table, browse_info]
            )
        
        # Tab 3: 搜索
        with gr.Tab("🔍 搜索"):
            search_input = gr.Textbox(label="搜索关键词", placeholder="输入 model_id 或其他关键词")
            search_btn = gr.Button("🔍 搜索", variant="primary")
            search_info = gr.Textbox(label="搜索结果", interactive=False)
            search_table = gr.Dataframe(
                headers=["Model ID", "状态", "Category", "Material", "标注者", "分数"],
                label="搜索结果"
            )
            
            search_btn.click(
                fn=search_records,
                inputs=search_input,
                outputs=[search_table, search_info]
            )
        
        # Tab 4: 详细信息
        with gr.Tab("📄 详情"):
            detail_input = gr.Textbox(
                label="Model ID", 
                placeholder="输入完整的 model_id",
                value="home-others-mirror-31854b50393738c38b46962840048a04"
            )
            detail_btn = gr.Button("🔍 查看详情", variant="primary")
            detail_output = gr.Markdown()
            
            detail_btn.click(
                fn=view_detail,
                inputs=detail_input,
                outputs=detail_output
            )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🗄️  启动数据库可视化查看工具...")
    print("="*60)
    demo.launch(server_port=7900, server_name="0.0.0.0", share=False)

