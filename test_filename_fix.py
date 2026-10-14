#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试文件名清理功能
"""

from core import clean_filename, extract_meeting_name, save_to_local_markdown
import os

def test_clean_filename():
    """测试文件名清理函数"""
    print("=== 测试文件名清理功能 ===")
    
    test_cases = [
        ("正常文件名", "正常文件名"),
        ("包含*星号的文件名", "包含_星号的文件名"),
        ("包含**多个星号**的文件名", "包含_多个星号_的文件名"),
        ("包含?问号的文件名", "包含_问号的文件名"),
        ("包含<>尖括号的文件名", "包含_尖括号的文件名"),
        ("包含:冒号的文件名", "包含_冒号的文件名"),
        ('包含"引号的文件名', "包含_引号的文件名"),
        ("包含|竖线的文件名", "包含_竖线的文件名"),
        ("包含/斜杠\\反斜杠的文件名", "包含_斜杠_反斜杠的文件名"),
        ("", "会议纪要"),
        ("   ", "会议纪要"),
        ("___", "会议纪要"),
        ("很长的文件名" * 10, "很长的文件名很长的文件名很长的文件名很长的文件名很长的文件名很长的文件名很长的文件名很长的文件名很长"),
    ]
    
    for i, (input_name, expected) in enumerate(test_cases, 1):
        result = clean_filename(input_name)
        status = "PASS" if result == expected else "FAIL"
        print(f"{i:2d}. {status} '{input_name}' -> '{result}'")
        if result != expected:
            print(f"     期望: '{expected}'")

def test_extract_meeting_name():
    """测试会议名称提取"""
    print("\\n=== 测试会议名称提取 ===")
    
    test_cases = [
        ("# 会议主题: AI技术讨论会", "AI技术讨论会"),
        ("# 会议主题：包含*特殊字符*的会议", "包含_特殊字符_的会议"),
        ("# 会议主题: 项目规划**重要**会议", "项目规划_重要_会议"),
        ("没有会议主题的文档", "会议纪要"),
        ("会议主题：", "会议纪要"),
    ]
    
    for i, (minutes_text, expected) in enumerate(test_cases, 1):
        result = extract_meeting_name(minutes_text)
        status = "PASS" if result == expected else "FAIL"
        print(f"{i}. {status} 提取结果: '{result}'")
        if result != expected:
            print(f"   期望: '{expected}'")

def test_save_markdown():
    """测试保存markdown文件"""
    print("\\n=== 测试文件保存功能 ===")
    
    test_dir = "test_output"
    test_content = "# 测试内容\\n\\n这是一个测试文件。"
    
    try:
        # 测试正常文件名
        result1 = save_to_local_markdown(test_content, "正常会议", test_dir)
        print(f"PASS 正常保存: {result1}")
        
        # 测试包含特殊字符的文件名
        result2 = save_to_local_markdown(test_content, "包含**特殊字符**的会议", test_dir)
        print(f"PASS 特殊字符保存: {result2}")
        
        # 测试很长的文件名
        long_name = "这是一个非常长的会议名称" * 5
        result3 = save_to_local_markdown(test_content, long_name, test_dir)
        print(f"PASS 长文件名保存: {result3}")
        
        print(f"\\n保存的文件:")
        for file in os.listdir(test_dir):
            if file.endswith('.md'):
                print(f"  - {file}")
                
    except Exception as e:
        print(f"FAIL 保存测试失败: {e}")

def cleanup_test_files():
    """清理测试文件"""
    test_dir = "test_output"
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            if file.endswith('.md'):
                os.remove(os.path.join(test_dir, file))
        try:
            os.rmdir(test_dir)
            print("\\n清理 测试文件已清理")
        except:
            print("\\n警告 部分测试文件清理失败")

def main():
    """主测试函数"""
    print("测试 文件名修复功能测试")
    print("=" * 50)
    
    try:
        test_clean_filename()
        test_extract_meeting_name()
        test_save_markdown()
        
        print("\\n" + "=" * 50)
        print("PASS 所有测试完成")
        print("\\n修复说明:")
        print("1. 所有Windows非法字符(*<>:\"|?/\\)都会被替换为_")
        print("2. 连续的下划线会被合并为一个")
        print("3. 文件名长度限制在50个字符以内")
        print("4. 空白或无效文件名会使用默认名称'会议纪要'")
        
    except Exception as e:
        print(f"\\nFAIL 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cleanup_test_files()

if __name__ == "__main__":
    main()