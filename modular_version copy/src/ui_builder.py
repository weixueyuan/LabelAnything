"""
UI构建模块：根据配置动态生成UI组件

支持根据配置文件自动创建字段组件
"""

import gradio as gr
from typing import Dict, List, Tuple, Any
from config import FIELD_CONFIG, UI_CONFIG


class UIBuilder:
    """UI构建器类"""
    
    def __init__(self, field_configs: List[Dict]):
        """
        初始化UI构建器
        
        Args:
            field_configs: 字段配置列表
        """
        self.field_configs = field_configs
        self.components = {}  # 存储输入框组件
        self.checkbox_components = {}  # 存储勾选框组件
    
    def build_field_components(self):
        """
        根据配置动态构建字段组件
        
        Returns:
            构建的组件列表
        """
        components = []
        
        for idx, field in enumerate(self.field_configs):
            with gr.Column():
                # 勾选框
                if field.get('has_checkbox', False) and UI_CONFIG.get('enable_checkboxes', True):
                    chk = gr.Checkbox(
                        label=f"{UI_CONFIG.get('checkbox_label', '✗')} {field['label']}", 
                        value=False, 
                        container=False
                    )
                    self.checkbox_components[field['key']] = chk
                else:
                    chk = None
                
                # 输入框
                if field['type'] == 'textbox':
                    comp = gr.Textbox(
                        label="",
                        lines=field.get('lines', 1),
                        placeholder=field.get('placeholder', ''),
                        show_label=False
                    )
                    self.components[field['key']] = comp
                elif field['type'] == 'textarea':
                    # 可以扩展支持其他类型
                    comp = gr.Textbox(
                        label="",
                        lines=field.get('lines', 3),
                        placeholder=field.get('placeholder', ''),
                        show_label=False
                    )
                    self.components[field['key']] = comp
                else:
                    raise ValueError(f"不支持的字段类型: {field['type']}")
                
                components.append((comp, chk))
        
        return components
    
    def get_all_input_components(self) -> List:
        """
        获取所有输入框组件（按配置顺序）
        
        Returns:
            输入框组件列表
        """
        return [self.components[f['key']] for f in self.field_configs]
    
    def get_all_checkbox_components(self) -> List:
        """
        获取所有勾选框组件（按配置顺序）
        
        Returns:
            勾选框组件列表
        """
        result = []
        for f in self.field_configs:
            if f.get('has_checkbox', False):
                result.append(self.checkbox_components.get(f['key']))
        return result
    
    def get_all_components(self) -> List:
        """
        获取所有组件列表（输入框 + 勾选框，用于事件绑定）
        
        Returns:
            所有组件列表
        """
        return self.get_all_input_components() + self.get_all_checkbox_components()
    
    def get_component(self, field_key: str) -> Any:
        """
        获取指定字段的输入框组件
        
        Args:
            field_key: 字段key
            
        Returns:
            组件对象
        """
        return self.components.get(field_key)
    
    def get_checkbox(self, field_key: str) -> Any:
        """
        获取指定字段的勾选框组件
        
        Args:
            field_key: 字段key
            
        Returns:
            勾选框组件对象
        """
        return self.checkbox_components.get(field_key)
    
    def get_field_keys(self) -> List[str]:
        """
        获取所有字段key列表
        
        Returns:
            字段key列表
        """
        return [f['key'] for f in self.field_configs]
    
    @staticmethod
    def render_status_html(annotated: bool) -> str:
        """
        渲染标注状态HTML
        
        Args:
            annotated: 是否已标注
            
        Returns:
            HTML字符串
        """
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
    
    @staticmethod
    def render_user_info_html(user_uid: str, visible: int, others: int) -> str:
        """
        渲染用户信息栏HTML
        
        Args:
            user_uid: 用户ID
            visible: 可见数据数量
            others: 其他用户数据数量
            
        Returns:
            HTML字符串
        """
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
            👤 当前用户：<span style="font-size: 18px; text-decoration: underline;">{user_uid}</span> 
            &nbsp;&nbsp;|&nbsp;&nbsp; 
            📊 可见数据：{visible} 个 (你的标注 + 未标注)
            &nbsp;&nbsp;|&nbsp;&nbsp;
            🔒 其他用户：{others} 个
        </div>
        """

