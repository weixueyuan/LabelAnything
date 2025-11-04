#!/bin/bash
# 启动标注服务器（生产模式）

cd "$(dirname "$0")"

echo "🚀 启动物体属性标注工具"
echo "================================"
echo ""

# 获取服务器IP
SERVER_IP=$(hostname -I | awk '{print $1}')

# 默认端口
PORT=7860

echo "📋 配置信息:"
echo "  模式: 生产模式（需要登录）"
echo "  端口: $PORT"
echo "  数据库: databases/annotation.db"
echo ""

# 检查数据库是否存在
if [ ! -f "databases/annotation.db" ]; then
    echo "❌ 错误: 数据库不存在"
    echo "   请先运行: python -m importers.annotation_importer"
    exit 1
fi

echo "🌐 访问链接:"
echo "  本机访问: http://localhost:$PORT"
echo "  局域网访问: http://$SERVER_IP:$PORT"
echo ""
echo "👥 已配置用户:"
cat config/user_config.jsonl | grep username | cut -d'"' -f4 | sed 's/^/  - /'
echo ""
echo "================================"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务
python src/main_multi.py --port $PORT

