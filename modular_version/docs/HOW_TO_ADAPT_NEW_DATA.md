# 如何适配新数据

## 🎯 概述

本指南教你如何将新的数据源适配到标注系统。

---

## 📝 步骤总览

1. 创建 UI 配置
2. 创建导入器
3. 添加路由（可选）
4. 导入数据
5. 启动程序

---

## 1️⃣ 创建 UI 配置

创建 `ui_configs/your_task_config.py`：

```python
"""
你的任务配置
"""

TASK_INFO = {
    "task_id": "your_task",
    "task_name": "你的任务名称",
    "description": "任务描述"
}

# 字段配置（key名与数据库一致）
FIELD_CONFIG = [
    {
        "key": "field1",              # 数据库字段名
        "label": "字段1",              # 界面显示
        "type": "textbox",
        "lines": 1,
        "has_checkbox": True,
        "flex": 1,
        "process": None               # 处理类型：None, 'array_to_string'
    },
    {
        "key": "field2",
        "label": "字段2",
        "type": "textbox",
        "lines": 3,
        "has_checkbox": True,
        "flex": 2
    },
]

UI_CONFIG = {
    "title": "你的标注工具",
    "enable_checkboxes": True,
    "show_user_info": True,
    "show_status": True,
}

PATH_CONFIG = {
    "base_path": "/path/to/your/images",
    "gif_filename_pattern": "{model_id}.gif",
}
```

---

## 2️⃣ 创建导入器

创建 `importers/your_task_importer.py`：

```python
#!/usr/bin/env python
"""
你的任务导入器
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from importers.base_importer import BaseImporter


class YourTaskImporter(BaseImporter):
    """你的任务导入器"""
    
    def parse_source(self, source: str) -> List[Dict]:
        """
        解析数据源
        
        返回格式: [{"model_id": {...}}, ...]
        """
        records = []
        
        # 示例1: 读取JSONL
        import json
        with open(source, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                records.append(data)
        
        # 示例2: 读取CSV
        # import csv
        # with open(source, 'r') as f:
        #     reader = csv.DictReader(f)
        #     for row in reader:
        #         records.append({row['id']: row})
        
        # 示例3: 读取Excel
        # import pandas as pd
        # df = pd.read_excel(source)
        # for _, row in df.iterrows():
        #     records.append({row['id']: row.to_dict()})
        
        return records
    
    def transform_record(self, attrs: Dict) -> Dict:
        """
        转换记录：原始格式 → 标准格式
        
        返回格式:
        {
            'annotated': bool,
            'uid': str,
            'score': int,
            'field1': ...,  # 业务字段
            'field2': ...,
        }
        """
        result = {
            'annotated': attrs.get('annotated', False),
            'uid': attrs.get('uid', ''),
            'score': attrs.get('score', 1),
        }
        
        # 转换业务字段（根据你的原始数据格式）
        result['field1'] = attrs.get('原始字段名1', '')
        result['field2'] = attrs.get('原始字段名2', '')
        
        # 处理特殊类型
        # 数组 → 字符串
        if isinstance(result['field1'], list):
            result['field1'] = ', '.join(result['field1'])
        
        # 数字 → 字符串
        if isinstance(result['field2'], (int, float)):
            result['field2'] = str(result['field2'])
        
        return result


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='导入你的任务数据')
    
    default_source = os.path.join(project_root, 'your_data.jsonl')
    default_db = os.path.join(project_root, 'databases/your_task.db')
    
    parser.add_argument('--source', '-s', type=str, default=default_source)
    parser.add_argument('--db', '-d', type=str, default=default_db)
    parser.add_argument('--clean', '-c', action='store_true')
    
    args = parser.parse_args()
    
    importer = YourTaskImporter()
    importer.import_to_db(
        source=args.source,
        db_path=args.db,
        clean=args.clean
    )
    
    print(f"\n✅ 导入完成！")
    print(f"▶️  启动: python src/main_multi.py --uid user1\n")


if __name__ == "__main__":
    main()
```

---

## 3️⃣ 添加路由（可选）

编辑 `routes.py`：

```python
ROUTES = [
    # ... 现有任务
    {
        "url": "/your_task",
        "task": "your_task",      # 自动关联上面的文件
        "port": 7801,
        "description": "你的任务"
    }
]
```

---

## 4️⃣ 导入数据

```bash
python -m importers.your_task_importer --source your_data.jsonl
```

---

## 5️⃣ 启动程序

```bash
python src/main_multi.py --uid user1
```

---

## 📚 常见数据格式示例

### JSONL 格式

```jsonl
{"id1": {"field1": "value1", "field2": "value2"}}
{"id2": {"field1": "value3", "field2": "value4"}}
```

### CSV 格式

```csv
id,field1,field2
id1,value1,value2
id2,value3,value4
```

### Excel 格式

| id  | field1 | field2 |
|-----|--------|--------|
| id1 | value1 | value2 |
| id2 | value3 | value4 |

---

## 💡 提示

1. **字段名一致**：UI配置中的 `key` 必须与导入器的 `transform_record` 返回的字段名一致
2. **类型转换**：确保数据类型正确（字符串、数字、布尔值）
3. **测试数据**：先用小数据集测试，确认无误后再导入全量
4. **备份原数据**：导入前备份原始数据文件

---

**相关文档**：
- [DATABASE_GUIDE.md](DATABASE_GUIDE.md) - 数据库操作指南
- [DATA_FORMAT.md](DATA_FORMAT.md) - 数据格式说明
