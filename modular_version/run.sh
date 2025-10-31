#!/bin/bash
# 启动脚本：物体属性标注工具（新架构）

# 默认参数
PORT=7800
UID="default_user"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --uid)
            UID="$2"
            shift 2
            ;;
        --help)
            echo "用法: ./run.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --port PORT         服务器端口 (默认: $PORT)"
            echo "  --uid UID           用户标识符 (默认: $UID)"
            echo "  --help              显示帮助信息"
            echo ""
            echo "示例:"
            echo "  ./run.sh --port 7800 --uid user1"
            echo ""
            echo "首次使用请先导入数据:"
            echo "  python -m importers.annotation_importer"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 进入脚本所在目录
cd "$(dirname "$0")"

# 检查数据库
if [ ! -f "databases/annotation.db" ]; then
    echo "⚠️  数据库不存在！"
    echo ""
    echo "请先导入数据："
    echo "  python -m importers.annotation_importer"
    echo ""
    exit 1
fi

# 启动程序
echo "======================================"
echo "🚀 物体属性标注工具"
echo "======================================"
echo "端口: $PORT"
echo "用户: $UID"
echo "======================================"
echo ""

python src/main_multi.py --port "$PORT" --uid "$UID"
