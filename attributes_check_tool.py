import os
import argparse
import json
import re
import gradio as gr

parser = argparse.ArgumentParser()
parser.add_argument('--data_file', type=str, default="/root/projects/object_attributes_annotation_tool/test.json")
parser.add_argument('--base_path', type=str, default="/mnt/data/GRScenes-100/instances/renderings")
parser.add_argument('--port', type=int, default=7800)
parser.add_argument('--uid', type=str, default="default_user", help="用户唯一标识符，用于多人标注")
args = parser.parse_args()

DATA_FILE = args.data_file
BASE_PATH = args.base_path
SERVER_PORT = args.port
USER_UID = args.uid

# -------------------------
# Utils
# -------------------------
def load_data():
    with open(DATA_FILE, 'r') as f:
        data_list = json.load(f)
    data_dict = {}
    for item in data_list:
        data_dict.update(item)
    return data_dict

def parse_attributes(value_data):
    if isinstance(value_data, dict):
        value_str = value_data.get('data', '')
        annotated = value_data.get('annotated', False)
        uid = value_data.get('uid', '')  # 获取uid
        score = value_data.get('score', 1)  # 获取score，默认为1
    else:
        value_str = value_data
        annotated = False
        uid = ''
        score = 1
    json_match = re.search(r'```json\s*\n(.*?)\n```', value_str, re.DOTALL)
    if json_match:
        try:
            attrs = json.loads(json_match.group(1))
        except Exception:
            attrs = {}
        attrs['annotated'] = annotated
        attrs['uid'] = uid
        attrs['score'] = score
        return attrs
    return {'annotated': annotated, 'uid': uid, 'score': score}

def build_gif_path(key):
    parts = key.split('-')
    if len(parts) >= 4:
        type_folder = f"{parts[0]}_objects"
        subtype_folder = parts[1]
        category_folder = parts[2]
        model_id = parts[3]
        return os.path.join(
            BASE_PATH, type_folder, subtype_folder, category_folder,
            "thumbnails/merged_views", model_id, f"{model_id}_original.gif"
        )
    return None

def save_data(data_dict):
    import shutil
    from datetime import datetime
    if os.path.exists(DATA_FILE):
        backup_dir = os.path.join(os.path.dirname(DATA_FILE), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DATA_FILE, os.path.join(backup_dir, f"test_backup_{ts}.json"))
    data_list = [{k: v} for k, v in data_dict.items()]
    with open(DATA_FILE, 'w') as f:
        json.dump(data_list, f, indent=4, ensure_ascii=False)
    print(f"💾 已保存到: {DATA_FILE}")

def render_status_html(annotated: bool):
    # 使用单层div，背景色直接填充
    if annotated:
        return '''
        <div style="
            height: 100%;
            min-height: 56px;
            background-color: #d4edda;
            border: 2px solid #c3e6cb;
            padding: 8px;
            font-size: 14px;
            text-align: center;
            font-weight: 600;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
            color: #155724;
        ">✅ 已标注</div>
        '''
    else:
        return '''
        <div style="
            height: 100%;
            min-height: 56px;
            background-color: #f8d7da;
            border: 2px solid #f5c6cb;
            padding: 8px;
            font-size: 14px;
            text-align: center;
            font-weight: 600;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
            color: #721c24;
        ">❌ 未标注</div>
        '''

# -------------------------
# Main App
# -------------------------
def start_annotation(server_port):
    ALL_DATA = load_data()
    
    # 过滤数据：只保留当前用户可见的数据（自己的uid + 无uid的）
    DATA_DICT = {}
    for key, value in ALL_DATA.items():
        attrs = parse_attributes(value)
        item_uid = attrs.get('uid', '')
        # 如果没有uid或者uid是当前用户，则可见
        if not item_uid or item_uid == USER_UID:
            DATA_DICT[key] = value
    
    KEYS_LIST = list(DATA_DICT.keys())
    total_count = len(ALL_DATA)
    visible_count = len(DATA_DICT)
    
    print("="*60)
    print(f"👤 当前用户: {USER_UID}")
    print(f"📂 加载的数据文件: {DATA_FILE}")
    print(f"📊 数据总数: {total_count} 个模型")
    print(f"👁️  可见数据: {visible_count} 个模型 (你的 + 未标注的)")
    print(f"🔒 被其他用户标注: {total_count - visible_count} 个模型")
    print("🔑 示例:", KEYS_LIST[:3])
    print("="*60)

    def get_parts(k):
        p = k.split('-')
        return {'type': p[0], 'subtype': p[1], 'category': p[2], 'model_id': p[3]} if len(p)>=4 else {}

    def get_uniques():
        t,s,c,m = set(),set(),set(),set()
        for k in KEYS_LIST:
            p = get_parts(k)
            if p: t.add(p['type']); s.add(p['subtype']); c.add(p['category']); m.add(p['model_id'])
        return dict(types=sorted(t),subtypes=sorted(s),categories=sorted(c),model_ids=sorted(m))

    def build_key(t,st,cat,mid):
        return f"{t}-{st}-{cat}-{mid}" if all([t,st,cat,mid]) else None

    def load_all_data(k):
        """
        统一的数据加载函数，返回所有需要更新的组件
        返回顺序：
        1. key (模型检索框)
        2. gif (物体渲染视频)
        3-7. ci, di, mi, di2, pl (5个属性框)
        8-12. chk_ci, chk_di, chk_mi, chk_di2, chk_pl (5个勾选框)
        13. is_mod (修改标记)
        14. status (已标注状态)
        15. user_info (用户信息栏)
        16-19. t, st, c, mid (4个下拉框)
        """
        if not k or k not in DATA_DICT:
            # 空数据状态
            return (
                gr.update(value=""),  # key
                None,  # gif
                "","","","","",  # 5个属性框
                False,False,False,False,False,  # 5个勾选框
                gr.update(value=False),  # is_mod
                render_status_html(False),  # status
                render_user_info(),  # user_info
                gr.update(value=""),gr.update(value=""),gr.update(value=""),gr.update(value="")  # 4个下拉框
            )
        
        # 加载GIF和属性
        gif = build_gif_path(k)
        a = parse_attributes(DATA_DICT[k])
        
        # 解析key的各个部分
        parts = get_parts(k)
        
        return (
            gr.update(value=k),  # key - 更新模型检索框
            gif if gif and os.path.exists(gif) else None,  # gif
            a.get('category',''),  # ci
            a.get('description',''),  # di
            a.get('material',''),  # mi
            a.get('dimensions',''),  # di2
            a.get('placement',''),  # pl
            a.get('chk_category',False),  # chk_ci
            a.get('chk_description',False),  # chk_di
            a.get('chk_material',False),  # chk_mi
            a.get('chk_dimensions',False),  # chk_di2
            a.get('chk_placement',False),  # chk_pl
            gr.update(value=False),  # is_mod - 重置修改标记
            render_status_html(a.get('annotated',False)),  # status
            render_user_info(),  # user_info
            gr.update(value=parts.get('type','')),  # t
            gr.update(value=parts.get('subtype','')),  # st
            gr.update(value=parts.get('category','')),  # c
            gr.update(value=parts.get('model_id',''))  # mid
        )

    def modified(k,c,d,m,dim,p,chk_c,chk_d,chk_m,chk_dim,chk_p):
        if not k or k not in DATA_DICT: return False
        o=parse_attributes(DATA_DICT[k])
        return any([c!=o.get('category',''),d!=o.get('description',''),m!=o.get('material',''),
                    dim!=o.get('dimensions',''),p!=o.get('placement',''),
                    chk_c!=o.get('chk_category',False),chk_d!=o.get('chk_description',False),
                    chk_m!=o.get('chk_material',False),chk_dim!=o.get('chk_dimensions',False),
                    chk_p!=o.get('chk_placement',False)])

    def save_one(k,c,d,m,dim,p,chk_c,chk_d,chk_m,chk_dim,chk_p):
        if not k: return gr.update(),render_status_html(False),gr.update()
        # 计算score：如果任意一个勾选框被选中，score=0；否则score=1
        score = 0 if any([chk_c,chk_d,chk_m,chk_dim,chk_p]) else 1
        # 保存数据，添加uid标识和score
        saved_data = {
            "annotated": True,
            "uid": USER_UID,  # 记录标注者的UID
            "score": score,  # 保存score
            "data": f"```json\n{json.dumps(dict(category=c,description=d,material=m,dimensions=dim,placement=p,chk_category=chk_c,chk_description=chk_d,chk_material=chk_m,chk_dimensions=chk_dim,chk_placement=chk_p),indent=2,ensure_ascii=False)}\n```"
        }
        DATA_DICT[k] = saved_data
        ALL_DATA[k] = saved_data  # 同时更新总数据
        save_data(ALL_DATA)  # 保存完整数据
        return gr.update(value=False),render_status_html(True),render_user_info()

    def neighbor(k,dir):
        if not k or k not in KEYS_LIST: return ""
        i=KEYS_LIST.index(k)
        return KEYS_LIST[(i+1)%len(KEYS_LIST)] if dir=="next" else KEYS_LIST[(i-1)%len(KEYS_LIST)]

    uniq=get_uniques()
    
    # 计算统计信息的函数
    def get_stats():
        """计算当前用户的数据统计"""
        visible = 0
        others = 0
        for value in ALL_DATA.values():
            attrs = parse_attributes(value)
            item_uid = attrs.get('uid', '')
            if not item_uid or item_uid == USER_UID:
                visible += 1
            else:
                others += 1
        return visible, others, len(ALL_DATA)
    
    # 生成用户信息栏HTML的函数
    def render_user_info():
        """生成用户信息栏的HTML"""
        visible, others, _ = get_stats()
        return f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 12px 20px; 
                    border-radius: 8px; 
                    text-align: center; 
                    margin-bottom: 15px;
                    font-size: 16px;
                    font-weight: 600;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
            👤 当前用户：<span style="font-size: 18px; text-decoration: underline;">{USER_UID}</span> 
            &nbsp;&nbsp;|&nbsp;&nbsp; 
            📊 可见数据：{visible} 个 (你的标注 + 未标注)
            &nbsp;&nbsp;|&nbsp;&nbsp;
            🔒 其他用户：{others} 个
        </div>
        """
    
    with gr.Blocks(title="物体属性检查工具", css="""
        /* 搜索行：模型检索和状态框高度对齐 */
        #search_row {
            display: flex !important;
            align-items: stretch !important;
        }
        #search_row .gradio-column {
            display: flex !important;
            align-items: stretch !important;
        }
        #search_row .gradio-textbox {
            display: flex !important;
            flex-direction: column !important;
        }
        #search_row .gradio-html {
            flex: 1 !important;
            display: flex !important;
            flex-direction: column !important;
        }
        #search_row .gradio-html > div {
            flex: 1 !important;
            display: flex !important;
        }
        
        /* 主内容行的两个列等高 */
        #main_content_row {
            display: flex !important;
            align-items: stretch !important;
        }
        #main_content_row > .gradio-column {
            display: flex !important;
            flex-direction: column !important;
        }
        
        /* GIF容器样式：图片居中显示，超出则缩放 */
        #gif_container .gradio-image {
            height: 580px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        #gif_container .gradio-image img {
            max-width: 100% !important;
            max-height: 100% !important;
            width: auto !important;
            height: auto !important;
            object-fit: contain !important;
            margin: auto !important;
        }
        
        /* 右侧信息列：移除背景，让textbox自动填充空间 */
        #info_column {
            height: 580px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 4px !important;
        }
        #info_column > .gradio-column {
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
        }
        #info_column .gradio-checkbox {
            margin-bottom: 0px !important;
        }
        #info_column .gradio-textbox {
            flex: 1 1 0 !important;
            min-height: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            width: 100% !important;
        }
        #info_column .gradio-textbox textarea {
            flex: 1 !important;
            min-height: 0 !important;
        }
        /* 让description输入框占据2倍空间 */
        #info_column > div:nth-child(2) {
            flex: 2 1 0 !important;
        }
        
        #confirm_modal {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.6);
            z-index: 9999;
            display: flex !important;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(3px);
            animation: fadeIn 0.15s ease;
        }

        /* 弹窗主体卡片 */
        #confirm_card {
            width: min(400px, 80vw);
            max-height: min(280px, 45vh);
            overflow-y: auto;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.25);
            padding: 28px 24px 24px;
            animation: slideIn 0.2s ease;
        }

        /* 标题文字 */
        #confirm_card h2 {
            font-size: 20px !important;
            margin: 0 0 10px;
            color: #222;
            text-align: center;
            font-weight: 600;
            line-height: 1.3;
        }

        /* 正文文字 */
        #confirm_card p {
            font-size: 20px !important;
            margin: 0 0 10px;
            color: #222;
            text-align: center;
            font-weight: 600;
            line-height: 1.3;
        }

        /* 🔥 关键修复：强制覆盖按钮样式 */
        #confirm_card button,
        #confirm_card .gradio-button,
        #confirm_card .gradio-button > span {
            font-size: 14px !important;
            font-weight: 600 !important;
            min-height: 48px !important;
            padding: 12px 20px !important;
            border-radius: 8px !important;
            line-height: 1.2 !important;
        }

        /* 按钮行/列间距 */
        #confirm_card .gradio-row {
            gap: 14px !important;
            margin-bottom: 12px;
        }
        #confirm_card .gradio-column {
            gap: 12px !important;
        }

        /* 动画：淡入 + 滑入 */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideIn {
            from { transform: translateY(-30px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        /* 📱 小屏自适应 */
        @media (max-width: 600px) {
            #confirm_card {
                width: 92vw;
                max-height: 65vh;
            }
            #confirm_card h2 { 
                font-size: 14px !important; 
            }
            #confirm_card p { 
                font-size: 14px !important; 
            }
            #confirm_card button,
            #confirm_card .gradio-button,
            #confirm_card .gradio-button > span { 
                font-size: 14px !important;
                min-height: 44px !important;
            }
        }
    """) as demo:

        gr.Markdown("# 物体属性检查工具")
        
        # 动态用户信息栏
        user_info = gr.HTML(render_user_info())

        is_mod = gr.State(value=False)
        nav_dir = gr.State(value="next")

        with gr.Row(equal_height=True):
            t=gr.Dropdown(choices=uniq['types'],label="类型 (Type)")
            st=gr.Dropdown(choices=uniq['subtypes'],label="子类型 (Subtype)")
            c=gr.Dropdown(choices=uniq['categories'],label="类别 (Category)")
            mid=gr.Dropdown(choices=uniq['model_ids'],label="模型ID (Model ID)")

        with gr.Row(equal_height=True, elem_id="search_row"):
            key=gr.Textbox(label="模型检索",interactive=True,placeholder="输入模型ID快速检索...",scale=3,container=True)
            with gr.Column(scale=1,min_width=120):
                status=gr.HTML(render_status_html(False))

        with gr.Row(elem_id="main_content_row"):
            with gr.Column(scale=1, elem_id="gif_container"):
                gif=gr.Image(label="物体渲染视频",height=580,container=True,show_download_button=False)
            with gr.Column(scale=1, elem_id="info_column"):
                with gr.Column():
                    chk_ci=gr.Checkbox(label="✗ Category (类别)",value=False,container=False)
                    ci=gr.Textbox(label="",lines=1,show_label=False)
                with gr.Column():
                    chk_di=gr.Checkbox(label="✗ Description (描述)",value=False,container=False)
                    di=gr.Textbox(label="",lines=3,show_label=False)
                with gr.Column():
                    chk_mi=gr.Checkbox(label="✗ Material (材质)",value=False,container=False)
                    mi=gr.Textbox(label="",lines=1,show_label=False)
                with gr.Column():
                    chk_di2=gr.Checkbox(label="✗ Dimensions (尺寸)",value=False,container=False)
                    di2=gr.Textbox(label="",lines=1,show_label=False)
                with gr.Column():
                    chk_pl=gr.Checkbox(label="✗ Placement (放置位置)",value=False,container=False)
                    pl=gr.Textbox(label="",lines=1,show_label=False)

        with gr.Row(equal_height=True):
            prev=gr.Button("⬅️ 上一个",variant="secondary",size="lg")
            save=gr.Button("💾 保存",variant="primary",size="lg")
            nxt=gr.Button("➡️ 下一个",variant="secondary",size="lg")

        # 伪Modal整块
        with gr.Column(visible=False,elem_id="confirm_modal") as confirm:
            with gr.Column(elem_id="confirm_card"):
                gr.HTML("<h2>⚠️ 有未保存的修改</h2><p>是否继续？</p>")
                with gr.Row():
                    save_next=gr.Button("💾 保存继续",variant="primary",size="sm")
                    cancel=gr.Button("❌ 取消",variant="secondary",size="sm")
                skip=gr.Button("⚠️ 放弃更改",variant="stop",size="sm")

        # 定义统一的输出组件列表（顺序必须与load_all_data返回值一致）
        ALL_OUTPUTS = [key, gif, ci, di, mi, di2, pl, chk_ci, chk_di, chk_mi, chk_di2, chk_pl, is_mod, status, user_info, t, st, c, mid]
        
        # 事件绑定
        def on_dropdown_change(t,st,c,mid):
            """下拉框改变时，只更新模型检索框"""
            k=build_key(t,st,c,mid)
            if k and k in KEYS_LIST:
                return gr.update(value=k)
            return gr.update(value="")
        
        for dd in (t,st,c,mid):
            dd.change(on_dropdown_change,inputs=[t,st,c,mid],outputs=[key])

        # 搜索功能：支持输入模型ID或完整Key
        def on_search(search_text):
            """搜索框回车时，加载完整数据"""
            if not search_text:
                return load_all_data("")
            
            # 精确匹配完整Key
            if search_text in KEYS_LIST:
                return load_all_data(search_text)
            
            # 模糊匹配：查找包含该ID的Key
            matched = [k for k in KEYS_LIST if search_text in k]
            if matched:
                return load_all_data(matched[0])
            
            # 无匹配
            return load_all_data("")

        # Enter键触发搜索
        key.submit(on_search, inputs=[key], outputs=ALL_OUTPUTS)
        
        # 失焦时自动补全完整Key
        def on_key_blur(search_text):
            if search_text in KEYS_LIST:
                return gr.update(value=search_text)
            matched = [k for k in KEYS_LIST if search_text in k]
            if matched:
                return gr.update(value=matched[0])
            return gr.update()
        
        key.blur(on_key_blur, inputs=[key], outputs=[key])
        
        # 模型检索框内容变化时，加载完整数据
        def on_key_change(k):
            """模型检索框内容变化时，更新所有组件"""
            return load_all_data(k)
        
        key.change(on_key_change, inputs=[key], outputs=ALL_OUTPUTS)

        # 输入框和勾选框变化时，标记为已修改
        def mark(): 
            return gr.update(value=True)
        for f in (ci,di,mi,di2,pl,chk_ci,chk_di,chk_mi,chk_di2,chk_pl): 
            f.change(mark, inputs=[], outputs=[is_mod])

        # 保存按钮 - 只更新状态和用户信息
        save.click(save_one, inputs=[key,ci,di,mi,di2,pl,chk_ci,chk_di,chk_mi,chk_di2,chk_pl], outputs=[is_mod,status,user_info])

        # 导航函数：上一个/下一个
        def on_nav(k,c,d,m,dim,p,chk_c,chk_d,chk_m,chk_dim,chk_p,direction):
            """导航到上一个或下一个，如果有修改则弹出确认框"""
            if modified(k,c,d,m,dim,p,chk_c,chk_d,chk_m,chk_dim,chk_p):
                # 有修改，显示确认弹窗
                return gr.update(), gr.update(visible=True), gr.update(value=direction)
            # 无修改，直接跳转（只更新key，触发key.change加载完整数据）
            next_key = neighbor(k, direction)
            return gr.update(value=next_key), gr.update(visible=False), gr.update(value=direction)

        nxt.click(on_nav, inputs=[key,ci,di,mi,di2,pl,chk_ci,chk_di,chk_mi,chk_di2,chk_pl,gr.State("next")], outputs=[key,confirm,nav_dir])
        prev.click(on_nav, inputs=[key,ci,di,mi,di2,pl,chk_ci,chk_di,chk_mi,chk_di2,chk_pl,gr.State("prev")], outputs=[key,confirm,nav_dir])

        # 保存并继续
        def on_save_and_go(k,c,d,m,dim,p,chk_c,chk_d,chk_m,chk_dim,chk_p,direction):
            """保存当前数据并跳转到下一个"""
            save_one(k,c,d,m,dim,p,chk_c,chk_d,chk_m,chk_dim,chk_p)
            next_key = neighbor(k, direction)
            return gr.update(value=next_key), gr.update(visible=False), gr.update(value=False), render_user_info()
        save_next.click(on_save_and_go, inputs=[key,ci,di,mi,di2,pl,chk_ci,chk_di,chk_mi,chk_di2,chk_pl,nav_dir], outputs=[key,confirm,is_mod,user_info])

        # 放弃修改并继续
        def on_skip_and_go(k, direction): 
            next_key = neighbor(k, direction)
            return gr.update(value=next_key), gr.update(visible=False)
        skip.click(on_skip_and_go, inputs=[key,nav_dir], outputs=[key,confirm])

        # 取消弹窗
        cancel.click(lambda: gr.update(visible=False), inputs=[], outputs=[confirm])

        # 页面加载时，自动加载第一个数据
        demo.load(lambda: KEYS_LIST[0] if KEYS_LIST else "", inputs=[], outputs=[key])

    demo.queue()
    demo.launch(server_name='0.0.0.0',server_port=server_port,allowed_paths=[BASE_PATH])

if __name__=="__main__":
    start_annotation(SERVER_PORT)