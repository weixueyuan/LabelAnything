# 数据库指南

## 📊 数据库设计

### 表结构

```sql
CREATE TABLE annotations (
    model_id TEXT PRIMARY KEY,       -- 模型ID
    annotated BOOLEAN DEFAULT 0,     -- 是否已标注
    uid TEXT DEFAULT '',             -- 标注者ID
    score INTEGER DEFAULT 1,         -- 质量分数
    data JSON DEFAULT '{}',          -- 业务数据（JSON格式）
    created_at DATETIME,             -- 创建时间
    updated_at DATETIME              -- 更新时间
);
```

### 为什么使用 JSON 字段？

✅ **灵活性**：不同任务可以有不同字段，无需修改表结构
✅ **扩展性**：添加新字段无需迁移数据
✅ **简洁性**：一个表支持所有任务

### 数据示例

```json
{
  "model_id": "type-subtype-category-001",
  "annotated": true,
  "uid": "user1",
  "score": 1,
  "data": {
    "category": "chair",
    "description": "A modern office chair",
    "material": "leather",
    "placement": "OnFloor",
    "chk_category": false,
    "chk_description": false
  }
}
```

---

## 🔧 常用操作

### 查询数据

```bash
# 进入数据库
sqlite3 databases/annotation.db

# 查询总数
SELECT COUNT(*) FROM annotations;

# 查询已标注数量
SELECT COUNT(*) FROM annotations WHERE annotated=1;

# 查看特定用户的标注
SELECT COUNT(*) FROM annotations WHERE uid='user1';

# 查看具体数据
SELECT model_id, json_extract(data, '$.category') as category, annotated 
FROM annotations LIMIT 10;

# 查询未标注的
SELECT model_id FROM annotations WHERE annotated=0 LIMIT 5;

# 导出为CSV
.mode csv
.output output.csv
SELECT model_id, 
       json_extract(data, '$.category') as category,
       json_extract(data, '$.description') as description,
       annotated, uid
FROM annotations;
.output stdout
```

### 备份与恢复

```bash
# 备份数据库
cp databases/annotation.db databases/annotation_backup_$(date +%Y%m%d).db

# 导出为SQL
sqlite3 databases/annotation.db .dump > backup.sql

# 从SQL恢复
sqlite3 databases/annotation_new.db < backup.sql
```

### 清空数据

```bash
# 方式1：重新导入（推荐）
python -m importers.annotation_importer --clean

# 方式2：直接删除
rm databases/annotation.db
python -m importers.annotation_importer
```

---

## 📈 数据统计

### Python 脚本

```python
import sqlite3
import json

conn = sqlite3.connect('databases/annotation.db')
cursor = conn.cursor()

# 总数统计
cursor.execute("SELECT COUNT(*) FROM annotations")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM annotations WHERE annotated=1")
annotated = cursor.fetchone()[0]

print(f"总数: {total}")
print(f"已标注: {annotated}")
print(f"未标注: {total - annotated}")
print(f"完成率: {annotated/total*100:.1f}%")

# 按用户统计
cursor.execute("SELECT uid, COUNT(*) FROM annotations WHERE uid != '' GROUP BY uid")
for uid, count in cursor.fetchall():
    print(f"用户 {uid}: {count} 条")

conn.close()
```

---

## 🔄 数据迁移

### 从旧数据库迁移

```python
import sqlite3
import json

# 连接旧数据库
old_conn = sqlite3.connect('old.db')
old_cursor = old_conn.cursor()

# 连接新数据库
new_conn = sqlite3.connect('databases/annotation.db')
new_cursor = new_conn.cursor()

# 读取旧数据
old_cursor.execute("SELECT * FROM old_table")
for row in old_cursor.fetchall():
    model_id = row[0]
    # ... 提取字段
    
    # 构建JSON数据
    data = {
        "category": row[1],
        "description": row[2],
        # ...
    }
    
    # 插入新数据库
    new_cursor.execute("""
        INSERT INTO annotations (model_id, annotated, uid, score, data)
        VALUES (?, ?, ?, ?, ?)
    """, (model_id, False, '', 1, json.dumps(data)))

new_conn.commit()
old_conn.close()
new_conn.close()
```

---

## 🛠️ 维护

### 优化数据库

```bash
sqlite3 databases/annotation.db "VACUUM;"
sqlite3 databases/annotation.db "ANALYZE;"
```

### 检查完整性

```bash
sqlite3 databases/annotation.db "PRAGMA integrity_check;"
```

---

## 💡 最佳实践

1. **定期备份**：每天备份一次数据库
2. **版本控制**：备份时加上日期标识
3. **测试环境**：使用复制的数据库测试新功能
4. **监控大小**：定期检查数据库文件大小
5. **清理旧数据**：定期归档或删除过期数据

---

**相关文档**：
- [HOW_TO_ADAPT_NEW_DATA.md](HOW_TO_ADAPT_NEW_DATA.md) - 如何适配新数据
- [DATA_FORMAT.md](DATA_FORMAT.md) - 数据格式说明
