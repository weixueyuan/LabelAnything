"""
模块测试脚本：测试各个模块是否正常工作

运行方式：
    python test_modules.py
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

def test_config():
    """测试配置文件"""
    print("测试 config.py ...")
    try:
        from config import FIELD_CONFIG, UI_CONFIG, PATH_CONFIG
        assert len(FIELD_CONFIG) > 0, "FIELD_CONFIG不能为空"
        assert 'title' in UI_CONFIG, "UI_CONFIG缺少title字段"
        assert 'data_file' in PATH_CONFIG, "PATH_CONFIG缺少data_file字段"
        print("✓ config.py 测试通过")
        return True
    except Exception as e:
        print(f"✗ config.py 测试失败: {e}")
        return False

def test_field_processor():
    """测试字段处理器"""
    print("\n测试 field_processor.py ...")
    try:
        from field_processor import FieldProcessor
        
        # 测试array_to_string
        field_config = {'process': 'array_to_string'}
        result = FieldProcessor.process_load(field_config, ['a', 'b', 'c'])
        assert result == 'a, b, c', f"array_to_string加载失败: {result}"
        
        result = FieldProcessor.process_save(field_config, 'a, b, c')
        assert result == ['a', 'b', 'c'], f"array_to_string保存失败: {result}"
        
        # 测试checkbox key
        result = FieldProcessor.get_checkbox_key('test')
        assert result == 'chk_test', f"checkbox key生成失败: {result}"
        
        print("✓ field_processor.py 测试通过")
        return True
    except Exception as e:
        print(f"✗ field_processor.py 测试失败: {e}")
        return False

def test_data_handler():
    """测试数据处理模块"""
    print("\n测试 data_handler.py ...")
    try:
        from data_handler import DataHandler
        
        # 创建临时测试文件
        test_file = "/tmp/test_data.jsonl"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('{"test-key": {"category": "chair", "description": "A chair", "placement": ["OnFloor"]}}\n')
        
        # 测试加载
        handler = DataHandler(test_file)
        data = handler.load_data()
        assert 'test-key' in data, "数据加载失败"
        
        # 测试解析
        attrs = handler.parse_item(data['test-key'])
        assert attrs['category'] == 'chair', "字段解析失败"
        assert attrs['placement'] == 'OnFloor', "数组字段处理失败"
        
        # 清理
        os.remove(test_file)
        
        print("✓ data_handler.py 测试通过")
        return True
    except Exception as e:
        print(f"✗ data_handler.py 测试失败: {e}")
        return False

def test_ui_builder():
    """测试UI构建模块"""
    print("\n测试 ui_builder.py ...")
    try:
        from ui_builder import UIBuilder
        from config import FIELD_CONFIG
        
        builder = UIBuilder(FIELD_CONFIG)
        
        # 测试组件创建
        keys = builder.get_field_keys()
        assert len(keys) > 0, "字段key列表为空"
        
        # 测试HTML渲染
        html = UIBuilder.render_status_html(True)
        assert '已标注' in html, "状态HTML渲染失败"
        
        html = UIBuilder.render_user_info_html('test_user', 100, 50)
        assert 'test_user' in html, "用户信息HTML渲染失败"
        
        print("✓ ui_builder.py 测试通过")
        return True
    except Exception as e:
        print(f"✗ ui_builder.py 测试失败: {e}")
        return False

def test_imports():
    """测试所有模块导入"""
    print("\n测试模块导入 ...")
    try:
        import config
        import field_processor
        import data_handler
        import ui_builder
        import main
        
        print("✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("="*60)
    print("开始测试模块化版本...")
    print("="*60)
    
    results = []
    results.append(("模块导入", test_imports()))
    results.append(("配置文件", test_config()))
    results.append(("字段处理器", test_field_processor()))
    results.append(("数据处理模块", test_data_handler()))
    results.append(("UI构建模块", test_ui_builder()))
    
    print("\n" + "="*60)
    print("测试结果汇总:")
    print("="*60)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name:20s} {status}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    
    print("="*60)
    print(f"总计: {passed}/{total} 项测试通过")
    print("="*60)
    
    if passed == total:
        print("\n🎉 所有测试通过！模块化版本可以正常使用。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查上面的错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

