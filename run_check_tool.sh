#!/bin/bash

# 物体属性检查工具启动脚本

echo "==================================="
echo "物体属性检查工具"
echo "==================================="
echo ""
echo "启动中..."
echo "访问地址: http://localhost:7800"
echo "或外部访问: http://服务器IP:7800"
echo ""

python /root/projects/object_attributes_annotation_tool/attributes_check_tool.py \
  --data_file /root/projects/object_attributes_annotation_tool/test.json \
  --base_path /mnt/data/GRScenes-100/instances/renderings \
  --port 7800

