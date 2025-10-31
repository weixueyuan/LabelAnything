# src/ 目录文件分析

## 使用情况

| 文件 | 大小 | 被调用情况 | 状态 |
|------|------|-----------|------|
| **db_models.py** | 4.7K | base_importer.py, db_handler.py 使用 | ✅ **必需** |
| **db_handler.py** | 7.8K | main_multi.py 使用 | ✅ **必需** |
| **field_processor.py** | 3.0K | main_multi.py, db_handler.py 使用 | ✅ **必需** |
| **main_multi.py** | 10K | 主程序入口 | ✅ **必需** |
| **ui_builder.py** | 6.6K | ❌ **没有任何地方使用** | ❌ **可删除** |
| **__init__.py** | 21B | 包初始化 | ✅ 保留 |

## 调用链

```
主程序:
  main_multi.py
    ├─ db_handler.py
    │   ├─ db_models.py
    │   └─ field_processor.py
    └─ field_processor.py

导入工具:
  annotation_importer.py
    └─ base_importer.py
        └─ db_models.py
```

## 建议

1. **删除 ui_builder.py** - 没有被使用
2. **简化 importers/** - 不需要 base_importer.py，直接在 annotation_importer.py 实现
3. **保留其他文件** - 都有实际用途



