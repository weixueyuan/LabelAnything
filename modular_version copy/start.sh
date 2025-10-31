#!/bin/bash
source /root/apps/miniforge3/etc/profile.d/conda.sh
conda activate tool
cd "/root/projects/object_attributes_annotation_tool/modular_version copy/src"
python main.py --data_file ../merged_attributes.jsonl --uid user1 --port 7800
