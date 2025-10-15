import os
import argparse
import json
import re

import gradio as gr


parser = argparse.ArgumentParser()
parser.add_argument('--data_file', type=str, default="/root/projects/object_attributes_annotation_tool/test.json")
parser.add_argument('--base_path', type=str, default="/mnt/data/GRScenes-100/instances/renderings")
parser.add_argument('--port', type=int, default=7800)
args = parser.parse_args()

DATA_FILE = args.data_file
BASE_PATH = args.base_path
SERVER_PORT = args.port

# Load data
def load_data():
    with open(DATA_FILE, 'r') as f:
        data_list = json.load(f)
    
    # Convert list of dicts to single dict
    data_dict = {}
    for item in data_list:
        data_dict.update(item)
    
    return data_dict

def parse_attributes(value_data):
    """Parse the JSON string from the value"""
    # Handle new format with annotated field
    if isinstance(value_data, dict):
        value_str = value_data.get('data', '')
        annotated = value_data.get('annotated', False)
    else:
        # Old format compatibility
        value_str = value_data
        annotated = False
    
    # Extract JSON from markdown code block
    json_match = re.search(r'```json\s*\n(.*?)\n```', value_str, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        attrs = json.loads(json_str)
        attrs['annotated'] = annotated
        return attrs
    return {'annotated': annotated}

def build_gif_path(key):
    """Build GIF path from key"""
    # Split key by '-' to get folder structure
    parts = key.split('-')
    
    if len(parts) >= 4:
        # commercial-articulated-basket-02f563c8720e209efec34199dd999a53
        # -> commercial_objects/articulated/basket/thumbnails/merged_views/02f563c8720e209efec34199dd999a53/
        type_folder = f"{parts[0]}_objects"  # commercial -> commercial_objects
        subtype_folder = parts[1]  # articulated
        category_folder = parts[2]  # basket
        model_id = parts[3]  # 02f563c8720e209efec34199dd999a53
        
        gif_path = os.path.join(
            BASE_PATH,
            type_folder,
            subtype_folder,
            category_folder,
            "thumbnails/merged_views",
            model_id,
            f"{model_id}_original.gif"
        )
        return gif_path
    return None

def save_data(data_dict):
    """Save data back to file"""
    # Create backup before saving
    import shutil
    from datetime import datetime
    
    if os.path.exists(DATA_FILE):
        backup_dir = os.path.join(os.path.dirname(DATA_FILE), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"test_backup_{timestamp}.json")
        shutil.copy2(DATA_FILE, backup_file)
        print(f"📦 已创建备份: {backup_file}")
    
    # Convert back to list of dicts format
    data_list = [{key: value} for key, value in data_dict.items()]
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data_list, f, indent=4, ensure_ascii=False)
    
    print(f"💾 已保存到: {DATA_FILE}")

def start_annotation(server_port):
    
    # Load initial data
    DATA_DICT = load_data()
    KEYS_LIST = list(DATA_DICT.keys())
    
    # Debug: Print loaded data
    print("=" * 60)
    print(f"📂 加载的数据文件: {DATA_FILE}")
    print(f"📊 总共加载了 {len(DATA_DICT)} 个模型")
    print(f"🔑 模型列表:")
    for i, key in enumerate(KEYS_LIST, 1):
        gif_path = build_gif_path(key)
        gif_exists = "✅" if gif_path and os.path.exists(gif_path) else "❌"
        print(f"   {i}. {key}")
        print(f"      GIF路径: {gif_path}")
        print(f"      文件存在: {gif_exists}")
    print("=" * 60)
    
    # Track modifications
    current_modifications = {}
    
    def get_key_parts(key):
        """Parse key into parts for dropdowns"""
        parts = key.split('-')
        if len(parts) >= 4:
            return {
                'type': parts[0],
                'subtype': parts[1],
                'category': parts[2],
                'model_id': parts[3]
            }
        return {}
    
    def get_all_unique_parts():
        """Get all unique values for each part"""
        types = set()
        subtypes = set()
        categories = set()
        model_ids = set()
        
        for key in KEYS_LIST:
            parts = get_key_parts(key)
            if parts:
                types.add(parts['type'])
                subtypes.add(parts['subtype'])
                categories.add(parts['category'])
                model_ids.add(parts['model_id'])
        
        return {
            'types': sorted(list(types)),
            'subtypes': sorted(list(subtypes)),
            'categories': sorted(list(categories)),
            'model_ids': sorted(list(model_ids))
        }
    
    def build_key_from_parts(type_val, subtype_val, category_val, model_id_val):
        """Build key from dropdown values"""
        if all([type_val, subtype_val, category_val, model_id_val]):
            return f"{type_val}-{subtype_val}-{category_val}-{model_id_val}"
        return None
    
    def load_model_data(key):
        """Load GIF and attributes for a model"""
        if not key or key not in DATA_DICT:
            return None, "", "", "", "", "", "", False
        
        # Get GIF path
        gif_path = build_gif_path(key)
        
        # Parse attributes
        attrs = parse_attributes(DATA_DICT[key])
        
        category = attrs.get('category', '')
        description = attrs.get('description', '')
        material = attrs.get('material', '')
        dimensions = attrs.get('dimensions', '')
        mass = attrs.get('mass', '')
        placement = attrs.get('placement', '')
        annotated = attrs.get('annotated', False)
        
        if os.path.exists(gif_path):
            return gif_path, category, description, material, dimensions, mass, placement, annotated
        else:
            return None, category, description, material, dimensions, mass, placement, annotated
    
    def update_current_key(type_val, subtype_val, category_val, model_id_val):
        """Update current key based on dropdown selections"""
        key = build_key_from_parts(type_val, subtype_val, category_val, model_id_val)
        if key and key in KEYS_LIST:
            return gr.update(value=key)
        return gr.update()
    
    def load_data_for_key(current_key):
        """Load all data when key changes"""
        if not current_key:
            return None, "", "", "", "", "", "", gr.update(value=False), ""
        
        gif_path, category, description, material, dimensions, mass, placement, annotated = load_model_data(current_key)
        
        # Create annotation status HTML (compact version with fixed height to match textbox)
        if annotated:
            status_html = '''
            <div style='background-color: #d4edda; border: 2px solid #28a745; border-radius: 5px; padding: 10px 15px; text-align: center; display: flex; align-items: center; justify-content: center; height: 58px;'>
                <span style='color: #155724; font-size: 16px; font-weight: bold;'>✅ 已标注</span>
            </div>
            '''
        else:
            status_html = '''
            <div style='background-color: #f8d7da; border: 2px solid #dc3545; border-radius: 5px; padding: 10px 15px; text-align: center; display: flex; align-items: center; justify-content: center; height: 58px;'>
                <span style='color: #721c24; font-size: 16px; font-weight: bold;'>❌ 未标注</span>
            </div>
            '''
        
        # Parse key parts for dropdowns
        parts = get_key_parts(current_key)
        
        return (
            gif_path,
            category,
            description,
            material,
            dimensions,
            mass,
            placement,
            gr.update(value=False),  # Reset modified flag
            status_html  # Annotation status
        )
    
    def check_modifications(current_key, category, description, material, dimensions, mass, placement):
        """Check if current data has been modified"""
        if not current_key or current_key not in DATA_DICT:
            return False
        
        original_attrs = parse_attributes(DATA_DICT[current_key])
        
        return (
            category != original_attrs.get('category', '') or
            description != original_attrs.get('description', '') or
            material != original_attrs.get('material', '') or
            dimensions != original_attrs.get('dimensions', '') or
            mass != original_attrs.get('mass', '') or
            placement != original_attrs.get('placement', '')
        )
    
    def save_current(current_key, category, description, material, dimensions, mass, placement):
        """Save current modifications"""
        if not current_key:
            return gr.update(), ""
        
        # Build new JSON string
        new_attrs = {
            "category": category,
            "description": description,
            "material": material,
            "dimensions": dimensions,
            "mass": mass,
            "placement": placement
        }
        
        # Format as the new format with annotated field
        json_str = json.dumps(new_attrs, indent=2, ensure_ascii=False)
        DATA_DICT[current_key] = {
            "annotated": True,  # Mark as annotated when saved
            "data": f"```json\n{json_str}\n```"
        }
        
        # Save to file
        save_data(DATA_DICT)
        
        # Update status display to green (compact version with better alignment)
        status_html = '''
        <div style='background-color: #d4edda; border: 2px solid #28a745; border-radius: 5px; padding: 10px 15px; text-align: center; display: flex; align-items: center; justify-content: center; height: 58px;'>
            <span style='color: #155724; font-size: 16px; font-weight: bold;'>✅ 已标注</span>
        </div>
        '''
        
        return gr.update(value=False), status_html
    
    def next_model(current_key, category, description, material, dimensions, mass, placement):
        """Go to next model"""
        if not current_key or current_key not in KEYS_LIST:
            return gr.update(), gr.update(visible=False)
        
        # Check for modifications
        if check_modifications(current_key, category, description, material, dimensions, mass, placement):
            return gr.update(), gr.update(visible=True)
        
        # Go to next
        current_index = KEYS_LIST.index(current_key)
        next_index = (current_index + 1) % len(KEYS_LIST)
        next_key = KEYS_LIST[next_index]
        
        return gr.update(value=next_key), gr.update(visible=False)
    
    def prev_model(current_key, category, description, material, dimensions, mass, placement):
        """Go to previous model"""
        if not current_key or current_key not in KEYS_LIST:
            return gr.update(), gr.update(visible=False)
        
        # Check for modifications
        if check_modifications(current_key, category, description, material, dimensions, mass, placement):
            return gr.update(), gr.update(visible=True)
        
        # Go to previous
        current_index = KEYS_LIST.index(current_key)
        prev_index = (current_index - 1) % len(KEYS_LIST)
        prev_key = KEYS_LIST[prev_index]
        
        return gr.update(value=prev_key), gr.update(visible=False)
    
    def confirm_save_and_continue(current_key, category, description, material, dimensions, mass, placement, direction):
        """Save and continue to next/prev"""
        # Save first
        save_current(current_key, category, description, material, dimensions, mass, placement)
        
        # Then navigate
        current_index = KEYS_LIST.index(current_key)
        if direction == "next":
            next_index = (current_index + 1) % len(KEYS_LIST)
        else:  # prev
            next_index = (current_index - 1) % len(KEYS_LIST)
        
        next_key = KEYS_LIST[next_index]
        
        return gr.update(value=next_key), gr.update(visible=False)
    
    def confirm_continue_without_save(current_key, direction):
        """Continue without saving"""
        if not current_key or current_key not in KEYS_LIST:
            return gr.update(), gr.update(visible=False)
        
        current_index = KEYS_LIST.index(current_key)
        if direction == "next":
            next_index = (current_index + 1) % len(KEYS_LIST)
        else:  # prev
            next_index = (current_index - 1) % len(KEYS_LIST)
        
        next_key = KEYS_LIST[next_index]
        
        return gr.update(value=next_key), gr.update(visible=False)
    
    def cancel_navigation():
        """Cancel navigation"""
        return gr.update(visible=False)
    
    def mark_modified():
        """Mark as modified when user edits"""
        return gr.update(value=True)
    
    # Get unique parts for dropdowns
    unique_parts = get_all_unique_parts()
    
    # GUI Structure
    with gr.Blocks(title="物体属性检查工具") as demo:
        gr.Markdown("# 物体属性检查工具")
        
        # Hidden state to track if modified
        is_modified = gr.State(value=False)
        navigation_direction = gr.State(value="next")
        
        # Dropdown selectors
        with gr.Row(equal_height=True):
            type_dropdown = gr.Dropdown(choices=unique_parts['types'], label="类型 (Type)")
            subtype_dropdown = gr.Dropdown(choices=unique_parts['subtypes'], label="子类型 (Subtype)")
            category_dropdown = gr.Dropdown(choices=unique_parts['categories'], label="类别 (Category)")
            model_id_dropdown = gr.Dropdown(choices=unique_parts['model_ids'], label="模型ID (Model ID)")
        
        # Current key and status in one row
        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                current_key = gr.Textbox(label="当前模型Key", interactive=False, container=True)
            with gr.Column(scale=1, min_width=150):
                gr.HTML("<div style='margin-bottom: 8px; font-size: 14px; color: #666;'>标注状态</div>")
                annotation_status = gr.HTML(value="", label=None)
        
        # Main content
        with gr.Row():
            # Left: GIF display
            with gr.Column(scale=1):
                gif_output = gr.Image(label="物体渲染视频", value=None, height=600)
            
            # Right: Attribute fields
            with gr.Column(scale=1):
                category_input = gr.Textbox(label="Category (类别)", lines=1)
                description_input = gr.Textbox(label="Description (描述)", lines=5)
                material_input = gr.Textbox(label="Material (材质)", lines=1)
                dimensions_input = gr.Textbox(label="Dimensions (尺寸)", lines=1, placeholder="例如: 0.30 * 0.20 * 0.25")
                mass_input = gr.Textbox(label="Mass (质量)", lines=1, placeholder="例如: 0.5")
                placement_input = gr.Textbox(label="Placement (放置位置)", lines=1)
        
        # Navigation and save buttons
        with gr.Row(equal_height=True):
            prev_button = gr.Button("⬅️ 上一个", variant="secondary", size="lg")
            save_button = gr.Button("💾 保存", variant="primary", size="lg")
            next_button = gr.Button("➡️ 下一个", variant="secondary", size="lg")
        
        # Confirmation dialog (使用 Row 和 Column 实现兼容所有版本)
        with gr.Column(visible=False) as confirm_dialog:
            gr.HTML(
                """
                <div style='background-color: #fff3cd; border: 3px solid #ffc107; border-radius: 10px; padding: 20px; text-align: center; margin: 10px 0;'>
                <h2 style='color: #856404; margin-top: 0;'>⚠️ 您有未保存的修改，是否要继续？</h2>
                <p style='color: #856404; font-size: 16px;'>请选择以下操作：</p>
                </div>
                """
            )
            with gr.Row():
                save_and_continue_btn = gr.Button("💾 保存并继续", variant="primary")
                cancel_btn = gr.Button("❌ 取消", variant="secondary")
            with gr.Row():
                continue_without_save_btn = gr.Button("⚠️ 不保存并继续")
        
        # Event handlers
        
        # Update current key when dropdowns change
        def on_dropdown_change(type_val, subtype_val, category_val, model_id_val):
            key = build_key_from_parts(type_val, subtype_val, category_val, model_id_val)
            if key and key in KEYS_LIST:
                return gr.update(value=key)
            return gr.update()
        
        type_dropdown.change(
            on_dropdown_change,
            inputs=[type_dropdown, subtype_dropdown, category_dropdown, model_id_dropdown],
            outputs=[current_key]
        )
        subtype_dropdown.change(
            on_dropdown_change,
            inputs=[type_dropdown, subtype_dropdown, category_dropdown, model_id_dropdown],
            outputs=[current_key]
        )
        category_dropdown.change(
            on_dropdown_change,
            inputs=[type_dropdown, subtype_dropdown, category_dropdown, model_id_dropdown],
            outputs=[current_key]
        )
        model_id_dropdown.change(
            on_dropdown_change,
            inputs=[type_dropdown, subtype_dropdown, category_dropdown, model_id_dropdown],
            outputs=[current_key]
        )
        
        # Load data when current key changes
        current_key.change(
            load_data_for_key,
            inputs=[current_key],
            outputs=[gif_output, category_input, description_input, material_input, 
                    dimensions_input, mass_input, placement_input, is_modified, annotation_status]
        )
        
        # Mark as modified when fields change
        category_input.change(mark_modified, inputs=[], outputs=[is_modified])
        description_input.change(mark_modified, inputs=[], outputs=[is_modified])
        material_input.change(mark_modified, inputs=[], outputs=[is_modified])
        dimensions_input.change(mark_modified, inputs=[], outputs=[is_modified])
        mass_input.change(mark_modified, inputs=[], outputs=[is_modified])
        placement_input.change(mark_modified, inputs=[], outputs=[is_modified])
        
        # Save button
        save_button.click(
            save_current,
            inputs=[current_key, category_input, description_input, material_input,
                   dimensions_input, mass_input, placement_input],
            outputs=[is_modified, annotation_status]
        )
        
        # Next button
        def on_next_click(current_key, category, description, material, dimensions, mass, placement):
            result = next_model(current_key, category, description, material, dimensions, mass, placement)
            return result[0], result[1], gr.update(value="next")
        
        next_button.click(
            on_next_click,
            inputs=[current_key, category_input, description_input, material_input,
                   dimensions_input, mass_input, placement_input],
            outputs=[current_key, confirm_dialog, navigation_direction]
        )
        
        # Prev button
        def on_prev_click(current_key, category, description, material, dimensions, mass, placement):
            result = prev_model(current_key, category, description, material, dimensions, mass, placement)
            return result[0], result[1], gr.update(value="prev")
        
        prev_button.click(
            on_prev_click,
            inputs=[current_key, category_input, description_input, material_input,
                   dimensions_input, mass_input, placement_input],
            outputs=[current_key, confirm_dialog, navigation_direction]
        )
        
        # Confirmation dialog buttons
        save_and_continue_btn.click(
            confirm_save_and_continue,
            inputs=[current_key, category_input, description_input, material_input,
                   dimensions_input, mass_input, placement_input, navigation_direction],
            outputs=[current_key, confirm_dialog]
        )
        
        continue_without_save_btn.click(
            confirm_continue_without_save,
            inputs=[current_key, navigation_direction],
            outputs=[current_key, confirm_dialog]
        )
        
        cancel_btn.click(
            cancel_navigation,
            inputs=[],
            outputs=[confirm_dialog]
        )
        
        # Load first model on start
        demo.load(
            lambda: KEYS_LIST[0] if KEYS_LIST else "",
            inputs=[],
            outputs=[current_key]
        )
    
    demo.queue()
    demo.launch(
        server_name='0.0.0.0', 
        server_port=server_port,
        allowed_paths=[BASE_PATH]  # 允许访问 GIF 文件所在的目录
    )


if __name__ == "__main__":
    start_annotation(SERVER_PORT)

