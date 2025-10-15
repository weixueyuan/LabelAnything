#!/bin/bash

# 物体属性检查工具启动脚本

# 默认用户ID（可通过命令行参数修改）
USER_ID=${1:-"default_user"}

echo "==================================="
echo "物体属性检查工具"
echo "==================================="
echo ""
echo "👤 当前用户: $USER_ID"
echo "启动中..."
echo "访问地址: http://localhost:7800"
echo "或外部访问: http://服务器IP:7800"
echo ""
echo "💡 使用说明:"
echo "   - 默认启动: ./run_check_tool.sh"
echo "   - 指定用户: ./run_check_tool.sh user1"
echo "   - 不同用户只能看到自己的和未标注的数据"
echo ""

python /root/projects/object_attributes_annotation_tool/attributes_check_tool.py \
  --data_file /root/projects/object_attributes_annotation_tool/test.json \
  --base_path /mnt/data/GRScenes-100/instances/renderings \
  --port 7800 \
  --uid "$USER_ID"

