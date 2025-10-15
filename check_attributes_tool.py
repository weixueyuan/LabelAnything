import os
import argparse
import json

import gradio as gr


parser = argparse.ArgumentParser()
parser.add_argument('--company', type=int, default=1)
parser.add_argument('--test', action="store_true")
parser.add_argument('--type', type=str, default="gr")
parser.add_argument('--user', type=str, default="1")
args = parser.parse_args()

test_mode = args.test
gr_type = args.type
user = args.user

if test_mode:
    assert args.company is not None
    base_server_port = 7900
    server_port = base_server_port + args.company
    DATA_DIR = f"/root/projects/rotation_annotation_tool/data_for_test/company{args.company}"
else:
    base_port = 7900
    if user == "cpz":
        user_id = 23
    else:
        user_id = int(user)
    server_port = base_port + user_id
    if gr_type == "gr":
        DATA_DIR = "/root/data/GRScenes/instances"
    elif gr_type == "gr-100":
        # python rotation_tool.py --type gr-100 --user 1
        DATA_DIR = "/root/data/GRScenes-100/instances/renderings"

PART_LIST = sorted(os.listdir(DATA_DIR))
INDEX_LIST = []
for part in PART_LIST:
    part_path = os.path.join(DATA_DIR, part)
    index_list = [f"{part}/{usd}" for usd in sorted(os.listdir(part_path))]
    INDEX_LIST.extend(index_list)

def start_annotation(server_port):

    MODEL_LIST = []
    SCENE_LIST = []

    # data update
    def update_scene_list(index):
        global SCENE_LIST
        usd_path = os.path.join(DATA_DIR, index)
        scene_list = sorted(os.listdir(usd_path))
        # print(scene_list)
        SCENE_LIST = scene_list
        return gr.update(choices=scene_list, value = scene_list[0])
    
    def update_models_list(index, scene_name, model_name):
        global MODEL_LIST
        scene_path = os.path.join(DATA_DIR, index, scene_name)
        print(scene_path)
        models_folder = os.path.join(scene_path, "thumbnails/merged_views")
        annotated_data_path = os.path.join(scene_path, "human_annotations/rotation_annotation.json")
        if os.path.exists(annotated_data_path):
            with open(annotated_data_path, "r") as f:
                annotated_data = json.load(f)
        else:
            annotated_data = {}
        annotated_number = len(annotated_data)
        model_list = sorted(os.listdir(models_folder))
        MODEL_LIST = model_list
        model_number = len(MODEL_LIST)
        progress = annotated_number / model_number if model_number > 0 else 0

        current_model_name = model_list[0]
        if model_name  and model_name == current_model_name:
            current_model_name = model_list[1]

        return gr.update(choices=model_list, value=current_model_name), round(progress*100, 2), model_number
    
    def load_pngs(index, scene_name, model_name):
        if not all([index, scene_name, model_name]):
            return None  
        model_folder = os.path.join(DATA_DIR, index, scene_name, "thumbnails/merged_views", model_name)
        image_path = os.path.join(model_folder, f"{model_name}.png")
        if os.path.exists(image_path):
            return gr.update(value=image_path)
        else:
            return None
        
    def load_gifs(index, scene_name, model_name):
        
        if not all([index, scene_name, model_name]):
            return None, None
        is_annotated = False
        result = None
        scene_path = os.path.join(DATA_DIR, index, scene_name)
        model_folder = os.path.join(scene_path, "thumbnails/merged_views", model_name)
        annotated_data_path = os.path.join(scene_path, "human_annotations/rotation_annotation.json")
        if os.path.exists(annotated_data_path):
            with open(annotated_data_path, "r") as f:
                annotated_data = json.load(f)
            if model_name in annotated_data:
                is_annotated = True
                result = annotated_data[model_name]
        status = "annotated" if is_annotated else "unannotated"
        image_path = os.path.join(model_folder, f"{model_name}.gif")
        if os.path.exists(image_path):
            return gr.update(value=image_path), update_status(status, result)
        else:
            return None, None

    # switch
    def next_model(index, scene_name, model_name):
        global MODEL_LIST
        model_index = MODEL_LIST.index(model_name)
        next_index = (model_index + 1) % len(MODEL_LIST)
        next_model_name = MODEL_LIST[next_index]

        # first check unannotated model
        scene_path = os.path.join(DATA_DIR, index, scene_name)
        annotated_data_path = os.path.join(scene_path, "human_annotations/rotation_annotation.json")
        if os.path.exists(annotated_data_path):
            with open(annotated_data_path, "r") as f:
                annotated_data = json.load(f)
            # remove annotated models
            undone_models = [model for model in MODEL_LIST if model not in annotated_data]
            if undone_models:
                next_model_name = undone_models[0]

        return gr.update(value=next_model_name)
        pass

    def prev_model(model_name):
        global MODEL_LIST
        model_index = MODEL_LIST.index(model_name)
        prev_index = (model_index - 1) % len(MODEL_LIST)
        prev_model_name = MODEL_LIST[prev_index]
        return gr.update(value=prev_model_name)
        pass

    def next_scene(scene_name):
        global SCENE_LIST
        scene_index = SCENE_LIST.index(scene_name)
        next_index = (scene_index + 1) % len(SCENE_LIST)
        next_scene_name = SCENE_LIST[next_index]
        return gr.update(value=next_scene_name)
        pass

    def prev_scene(scene_name):
        global SCENE_LIST
        scene_index = SCENE_LIST.index(scene_name)
        prev_index = (scene_index - 1) % len(SCENE_LIST)
        prev_scene_name = SCENE_LIST[prev_index]
        return gr.update(value=prev_scene_name)
        pass

    # show status
    def update_status(status, annotation_result):

        common_style = '''
        <div style="
            border: 3px solid #ccc;
            padding: 3px;
            font-size: 20px;
            text-align: center; 
            font-weight: bold;
        ">{}</div>
        '''

        if status == "annotated":
            if annotation_result == -1:
                annotation_result = "跳过"
            elif annotation_result == -2:
                annotation_result = "歪斜物体"
            else:
                annotation_result += 1
            specific_content = '<div style="background-color: #c9f5bf;"><span style="color:green;">' + f"已标注, 标注结果为: {annotation_result}" + '</span>'
        elif status == "unannotated":
            specific_content = '<div style="background-color: #ebbbb4;"><span style="color:red;">' + "未标注" + '</span>'

        return common_style.format(specific_content)
    
    # save the annotation

    def annotate(index, scene_name, model_name, feedback):

        global MODEL_LIST

        # result path
        # print(index, model_name, feedback)
        print(model_name, feedback)
        feedback_fixed = int(feedback) - 1
        result_dir = os.path.join(DATA_DIR, index, scene_name, "human_annotations")
        print(result_dir)
        result_path = os.path.join(result_dir, "rotation_annotation.json")
        os.makedirs(result_dir, exist_ok=True)
        if not os.path.exists(result_path):
            annotation_data = {}
            annotation_data[model_name] = feedback_fixed
        else:
            with open(result_path, "r") as f:
                print("Load existing annotation file")
                annotation_data = json.load(f)
            annotation_data[model_name] = feedback_fixed
        with open(result_path, "w") as f:
            json.dump(annotation_data, f, indent=4)

        annotated_number = len(annotation_data)
        return next_model(index, scene_name, model_name), round(annotated_number / len(MODEL_LIST) * 100, 2)

    def double_check():
        return gr.update(visible=True)
    
    def invisible_button():
        return gr.update(visible=False)

    def setup_buttons(usd_id, scene_name, buttom, feedback):
        buttom.click(
            annotate,
            inputs=[usd_id, scene_name, model_name, gr.State(feedback)],
            outputs=[model_name, progress_bar]
        )



    # GUI Structure
    with gr.Blocks() as demo:
        with gr.Row(equal_height=True):
            usd_id = gr.Dropdown(choices=INDEX_LIST, label="选择文件夹序号")
            scene_name = gr.Dropdown(choices=[], label="选择包序号")
            model_name = gr.Dropdown(choices=[], label="选择模型序号")
        with gr.Row():
            with gr.Column(scale=6):
                # png_output = gr.Image(label="Preview PNG", value=None, height=775)
                png_output = gr.Image(label="同一个物体的24张渲染图", value=None, tool=[])
                with gr.Row(equal_height=True):
                    prev_scene_buttom = gr.Button("上一个包", visible=True)
                    next_scene_buttom = gr.Button("下一个包", visible=True)
            with gr.Column(scale=1):
                gif_output = gr.Image(label="物体渲染视频", value=None)
                status = gr.HTML()
                with gr.Row(equal_height=True):
                    prev_model_buttom = gr.Button("上一个模型", visible=True, min_width=60)
                    next_model_buttom = gr.Button("下一个模型", visible=True, min_width=60)
                model_number = gr.Textbox(value="", label="该数据包中模型的数量", interactive=False)
                progress_bar = gr.Slider(minimum=0, maximum=100, label="标注进度 (%)", interactive=False)
                # index button
                buttons_per_row = 6
                for i in range(4):  
                    with gr.Row(equal_height=True):
                        for j in range(buttons_per_row):
                            index_num = i * buttons_per_row + j + 1
                            button = gr.Button(str(index_num), visible=True, min_width=30)
                            setup_buttons(usd_id, scene_name, button, index_num)
                # special button
                with gr.Row(equal_height=True):
                    skip_button = gr.Button("跳过", visible=True, min_width=30)
                    leaning_button = gr.Button("这个物体是歪的", visible=True, min_width=30)
                with gr.Row(equal_height=True):
                    double_check_button = gr.Button("请再次确认，确认是跳过后点击此按钮", visible=False)
                    double_leaning_button = gr.Button("请再次确认，确认后点击此按钮", visible=False)

                
        usd_id.change(update_scene_list, inputs=usd_id, outputs=scene_name)
        scene_name.change(update_models_list, inputs=[usd_id, scene_name, model_name], outputs=[model_name, progress_bar, model_number])
        model_name.change(load_pngs, inputs=[usd_id, scene_name, model_name], outputs=png_output)
        model_name.change(load_gifs, inputs=[usd_id, scene_name, model_name], outputs=[gif_output, status])

        next_model_buttom.click(next_model, inputs=[usd_id, scene_name, model_name], outputs=model_name)
        prev_model_buttom.click(prev_model, inputs=[model_name], outputs=model_name)

        next_scene_buttom.click(next_scene, inputs=[scene_name], outputs=scene_name)
        prev_scene_buttom.click(prev_scene, inputs=[scene_name], outputs=scene_name)

        skip_button.click(double_check, inputs=[], outputs=[double_check_button])
        setup_buttons(usd_id, scene_name, double_check_button, 0)
        leaning_button.click(double_check, inputs=[], outputs=[double_leaning_button])
        setup_buttons(usd_id, scene_name, double_leaning_button, -1)
        double_check_button.click(invisible_button, inputs=[], outputs=[double_check_button])
        double_leaning_button.click(invisible_button, inputs=[], outputs=[double_leaning_button])

    demo.queue()
    demo.launch(server_name='0.0.0.0',server_port=server_port)
    

start_annotation(server_port)