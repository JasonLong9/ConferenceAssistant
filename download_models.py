#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模型预下载脚本
使用清华镜像加速下载HuggingFace模型
"""

import os
import sys
from huggingface_config import setup_huggingface_mirror, download_model_with_retry, check_network_connection

def download_speaker_model():
    """下载声纹识别模型"""
    model_name = "pyannote/speaker-diarization-3.1"
    
    print("=" * 60)
    print("声纹识别模型下载")
    print("=" * 60)
    print(f"模型名称: {model_name}")
    print("使用清华镜像加速: https://hf-mirror.com")
    print()
    
    try:
        # 检查网络连接
        if not check_network_connection():
            print("网络连接异常，请检查网络设置")
            return False
        
        # 下载模型
        local_dir = download_model_with_retry(model_name, max_retries=3)
        
        if local_dir:
            print(f"✓ 声纹识别模型下载成功!")
            print(f"  本地路径: {local_dir}")
            return True
        else:
            print("✗ 声纹识别模型下载失败")
            return False
            
    except Exception as e:
        print(f"✗ 下载过程中发生错误: {e}")
        return False

def test_model_loading():
    """测试模型加载"""
    print("\n" + "=" * 60)
    print("测试模型加载")
    print("=" * 60)
    
    try:
        from speaker_identification import SpeakerIdentifier
        
        print("正在初始化声纹识别器...")
        identifier = SpeakerIdentifier()
        
        if identifier.available:
            print("✓ 声纹识别模型加载成功!")
            print("✓ 系统已准备好处理声纹识别任务")
            return True
        else:
            print("✗ 声纹识别模型加载失败")
            return False
            
    except Exception as e:
        print(f"✗ 模型加载测试失败: {e}")
        return False

def setup_environment():
    """设置运行环境"""
    print("=" * 60)
    print("环境设置")
    print("=" * 60)
    
    # 创建缓存目录
    cache_dir = os.path.join(os.path.dirname(__file__), 'hf_cache')
    os.makedirs(cache_dir, exist_ok=True)
    print(f"✓ 缓存目录已创建: {cache_dir}")
    
    # 设置环境变量
    setup_huggingface_mirror()
    print("✓ HuggingFace镜像配置完成")
    
    # 检查依赖包
    try:
        import torch
        print(f"✓ PyTorch 版本: {torch.__version__}")
        
        cuda_available = torch.cuda.is_available()
        print(f"✓ CUDA 可用: {cuda_available}")
        if cuda_available:
            print(f"  GPU 设备数: {torch.cuda.device_count()}")
    except ImportError:
        print("✗ PyTorch 未安装")
    
    try:
        import pyannote.audio
        print("✓ pyannote.audio 已安装")
    except ImportError:
        print("✗ pyannote.audio 未安装")
        print("  请运行: pip install pyannote.audio")
    
    return True

def main():
    """主函数"""
    print("HuggingFace模型下载工具")
    print("使用清华镜像加速下载")
    print("=" * 60)
    
    success_count = 0
    total_count = 3
    
    # 1. 环境设置
    try:
        setup_environment()
        success_count += 1
        print("✓ 环境设置完成")
    except Exception as e:
        print(f"✗ 环境设置失败: {e}")
    
    # 2. 下载模型
    try:
        if download_speaker_model():
            success_count += 1
    except Exception as e:
        print(f"✗ 模型下载异常: {e}")
    
    # 3. 测试加载
    try:
        if test_model_loading():
            success_count += 1
    except Exception as e:
        print(f"✗ 模型测试异常: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    print("下载总结")
    print("=" * 60)
    print(f"完成进度: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有步骤完成!")
        print("\n接下来可以:")
        print("1. 运行 python main.py [音频文件] 进行测试")
        print("2. 启动 Web 服务: uvicorn web_service:app --port 8080")
        print("3. 声纹识别功能现在可以正常使用")
        return 0
    else:
        print("⚠️ 部分步骤失败，请检查上述错误信息")
        
        print("\n常见问题解决:")
        print("1. 网络问题: 检查网络连接，考虑使用VPN")
        print("2. 依赖缺失: pip install pyannote.audio torch torchaudio")
        print("3. 磁盘空间: 确保有足够空间下载模型(~1GB)")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n用户取消下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)