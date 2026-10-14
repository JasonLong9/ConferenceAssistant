#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速验证改进版系统是否在运行
"""

import requests
import json

def verify_improved_system():
    """验证8080端口是否运行改进版系统"""
    
    print("=== 验证改进版系统 ===")
    
    # 测试根路径，查看是否包含改进版信息
    try:
        response = requests.get("http://localhost:8080/")
        data = response.json()
        
        print(f"服务状态: {data.get('status')}")
        print(f"消息: {data.get('message')}")
        
        # 检查是否包含改进版信息
        if 'version' in data:
            print(f"版本: {data.get('version')}")
        
        if 'improvements' in data:
            print("改进列表:")
            for improvement in data.get('improvements', []):
                print(f"  - {improvement}")
                
        # 检查健康接口
        health_response = requests.get("http://localhost:8080/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"\n健康检查:")
            print(f"  状态: {health_data.get('status')}")
            print(f"  版本: {health_data.get('version')}")
            print(f"  改进激活: {health_data.get('improvements_active')}")
            
            if health_data.get('version') and 'improved' in health_data.get('version', ''):
                print("✅ 确认：运行改进版系统")
                return True
            else:
                print("❌ 当前运行标准版系统")
                return False
        else:
            print("⚠️ 健康检查接口不可用")
            return False
            
    except Exception as e:
        print(f"验证失败: {e}")
        return False

def check_core_system():
    """检查核心系统是否支持改进版"""
    
    print("\n=== 检查核心系统 ===")
    
    try:
        # 尝试导入改进版
        from core import IMPROVED_SPEAKER_ID_AVAILABLE
        print(f"改进版声纹识别可用: {IMPROVED_SPEAKER_ID_AVAILABLE}")
        
        if IMPROVED_SPEAKER_ID_AVAILABLE:
            from improved_speaker_id import ImprovedSpeakerIdentifier
            print("✅ 改进版声纹识别模块导入成功")
            return True
        else:
            print("❌ 改进版声纹识别不可用")
            return False
            
    except Exception as e:
        print(f"核心系统检查失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 验证改进版ConferenceAssistant系统")
    
    # 1. 检查Web服务
    web_improved = verify_improved_system()
    
    # 2. 检查核心系统
    core_improved = check_core_system()
    
    print("\n📊 验证结果:")
    print(f"  Web服务改进版: {'✅' if web_improved else '❌'}")
    print(f"  核心系统改进版: {'✅' if core_improved else '❌'}")
    
    if web_improved and core_improved:
        print("\n🎉 系统已正确部署改进版!")
        print("可以进行完整测试以验证声纹识别改进效果")
    elif core_improved and not web_improved:
        print("\n⚠️ 核心系统已改进，但Web服务需要重启")
        print("建议重启Web服务以加载改进版系统")
    else:
        print("\n❌ 系统需要部署改进版")
        print("请检查改进版文件是否正确部署")