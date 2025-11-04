#!/bin/bash
# 项目清理脚本 - 只清理 modular_version/ 目录

echo "🧹 开始清理 modular_version 目录..."
echo "================================"

cd "$(dirname "$0")"

# 清理计数
REMOVED_COUNT=0

# 函数：安全删除
safe_remove() {
    if [ -e "$1" ]; then
        echo "  🗑️  删除: $1"
        rm -rf "$1"
        ((REMOVED_COUNT++))
    fi
}

echo ""
echo "📦 清理 modular_version 目录..."

# 1. Python缓存
echo "  🗑️  删除 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
((REMOVED_COUNT++))

# 2. 测试文件（保留）
# safe_remove "test.jsonl"  # 保留
# safe_remove "database_jsonl"  # 保留

# 3. 旧备份
safe_remove "backups"

# 4. 重复脚本（保留start_server.sh）
safe_remove "run.sh"
safe_remove "run_ui.sh"

# 5. 过时文档
safe_remove "ANALYSIS.md"
safe_remove "STRUCTURE.md"

# 6. 清理文档列表（临时文件）
safe_remove "CLEANUP_LIST.md"

# 7. 旧导出文件（保留最新的）
echo ""
echo "📂 清理旧导出文件..."
if [ -d "exports" ]; then
    cd exports
    # 保留最新的1个导出文件
    FILE_COUNT=$(ls -t export_*.jsonl 2>/dev/null | wc -l)
    if [ $FILE_COUNT -gt 1 ]; then
        ls -t export_*.jsonl | tail -n +2 | xargs rm
        echo "  ✓ 保留最新的导出文件，删除 $((FILE_COUNT - 1)) 个旧文件"
    else
        echo "  ✓ 只有1个或0个导出文件，无需清理"
    fi
    cd ..
fi

# 8. 清理测试脚本（保留有用的）
safe_remove "test_multi_user.sh"

# 9. zhaoyang配置（保留）
# safe_remove "ui_configs/zhaoyang_config.py"  # 保留

echo ""
echo "================================"
echo "✅ 清理完成！"
echo "   删除项目: $REMOVED_COUNT 项"
echo ""
echo "🎯 保留的核心文件:"
echo "  ✅ src/ - 核心代码"
echo "  ✅ tools/ - 工具脚本"
echo "  ✅ config/ - 配置文件"
echo "  ✅ databases/ - 数据库"
echo "  ✅ ui_configs/ - UI配置"
echo "  ✅ importers/ - 数据导入器"
echo "  ✅ docs/ - 文档目录"
echo "  ✅ exports/ - 导出目录（最新）"
echo "  ✅ merged_attributes.jsonl - 源数据"
echo "  ✅ start_server.sh - 启动脚本"
echo "  ✅ 标注说明.md - 用户文档"
echo "  ✅ README.md, QUICKSTART.md - 项目文档"
echo ""
echo "💡 提示: 根目录文件未被修改"
echo ""

