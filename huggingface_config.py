#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HuggingFace 清华镜像配置
解决模型下载网络问题
"""

import os
import warnings
from typing import Optional

def setup_huggingface_mirror():
    """
    设置 HuggingFace 清华镜像源
    解决模型下载速度慢或连接失败的问题
    """
    # 设置清华大学镜像源
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    
    # 设置缓存目录（可选）
    cache_dir = os.path.join(os.path.dirname(__file__), 'hf_cache')
    os.makedirs(cache_dir, exist_ok=True)
    os.environ['HF_HOME'] = cache_dir
    os.environ['HUGGINGFACE_HUB_CACHE'] = cache_dir
    
    print(f"已配置 HuggingFace 清华镜像: {os.environ['HF_ENDPOINT']}")
    print(f"缓存目录: {cache_dir}")

def check_network_connection() -> bool:
    """
    检查网络连接状态
    """
    import requests
    try:
        # 先测试清华镜像
        response = requests.get('https://hf-mirror.com', timeout=10)
        if response.status_code == 200:
            print("网络连接正常，清华镜像可访问")
            return True
    except:
        pass
    
    try:
        # 测试原始HuggingFace
        response = requests.get('https://huggingface.co', timeout=5)
        if response.status_code == 200:
            print("网络连接正常，原始HuggingFace可访问")
            return True
    except:
        pass
    
    print("网络连接异常，可能影响模型下载")
    return False

def download_model_with_retry(model_name: str, max_retries: int = 3):
    """
    带重试机制的模型下载
    """
    from huggingface_hub import snapshot_download
    
    for attempt in range(max_retries):
        try:
            print(f"正在下载模型 {model_name} (第 {attempt + 1}/{max_retries} 次尝试)...")
            
            cache_dir = os.environ.get('HUGGINGFACE_HUB_CACHE', './hf_cache')
            local_dir = snapshot_download(
                repo_id=model_name,
                cache_dir=cache_dir,
                local_files_only=False
            )
            
            print(f"模型下载成功: {local_dir}")
            return local_dir
            
        except Exception as e:
            print(f"第 {attempt + 1} 次下载失败: {e}")
            if attempt < max_retries - 1:
                print("等待10秒后重试...")
                import time
                time.sleep(10)
            else:
                print("所有重试均失败")
                raise e
    
    return None

def verify_model_exists(model_name: str) -> bool:
    """
    验证模型是否已下载到本地
    """
    try:
        from huggingface_hub import snapshot_download
        
        # 尝试仅从本地加载
        local_dir = snapshot_download(
            repo_id=model_name,
            local_files_only=True
        )
        print(f"模型已存在于本地: {local_dir}")
        return True
        
    except Exception as e:
        print(f"模型不存在于本地: {e}")
        return False

# 自动执行配置
setup_huggingface_mirror()

if __name__ == "__main__":
    print("=" * 50)
    print("HuggingFace 清华镜像配置测试")
    print("=" * 50)
    
    # 检查网络连接
    network_ok = check_network_connection()
    
    # 检查声纹识别模型
    speaker_model = "pyannote/speaker-diarization-3.1"
    model_exists = verify_model_exists(speaker_model)
    
    if not model_exists and network_ok:
        print(f"\n尝试下载模型: {speaker_model}")
        try:
            download_model_with_retry(speaker_model)
        except Exception as e:
            print(f"模型下载失败: {e}")
            print("建议手动配置网络代理或使用离线模式")
    
    print("\n配置完成！")