#!/bin/bash
# 启动标注UI界面

source /root/apps/miniforge3/etc/profile.d/conda.sh
conda activate tool

cd "$(dirname "$0")"

# 检查数据库
if [ ! -f "databases/annotation.db" ]; then
    echo "❌ 数据库不存在！"
    echo ""
    echo "请先导入数据："
    echo "  python -m importers.annotation_importer"
    echo ""
    exit 1
fi

# 解析参数
PORT=7800
UID="default_user"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --uid) UID="$2"; shift 2 ;;
        --help)
            echo "用法: ./run_ui.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --port PORT    服务器端口 (默认: 7800)"
            echo "  --uid UID      用户ID (默认: default_user)"
            echo "  --help         显示帮助"
            exit 0
            ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

echo "======================================"
echo "🚀 启动标注工具"
echo "======================================"
echo "用户: $UID"
echo "端口: $PORT"
echo "地址: http://localhost:$PORT"
echo "======================================"
echo ""

python src/main_multi.py --uid "$UID" --port "$PORT"

