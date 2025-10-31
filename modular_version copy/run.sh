#!/bin/bash
# 启动脚本：物体属性标注工具 - 模块化版本

# 默认参数
DATA_FILE="/root/projects/object_attributes_annotation_tool/merged_attributes.jsonl"
BASE_PATH="/mnt/data/GRScenes-100/instances/renderings"
PORT=7801
UID="default_user"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --data_file)
            DATA_FILE="$2"
            shift 2
            ;;
        --base_path)
            BASE_PATH="$2"
            shift 2
            ;;
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
            echo "  --data_file PATH    数据文件路径 (默认: $DATA_FILE)"
            echo "  --base_path PATH    GIF文件基础路径 (默认: $BASE_PATH)"
            echo "  --port PORT         服务器端口 (默认: $PORT)"
            echo "  --uid UID           用户标识符 (默认: $UID)"
            echo "  --help              显示帮助信息"
            echo ""
            echo "示例:"
            echo "  ./run.sh --port 8000 --uid user1"
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

# 启动程序
echo "正在启动物体属性标注工具..."
echo "数据文件: $DATA_FILE"
echo "基础路径: $BASE_PATH"
echo "端口: $PORT"
echo "用户: $UID"
echo ""

# 从src目录启动
cd src
python main.py \
    --data_file "$DATA_FILE" \
    --base_path "$BASE_PATH" \
    --port "$PORT" \
    --uid "$UID"

