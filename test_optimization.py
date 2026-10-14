#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化效果测试脚本
比较原版和优化版的性能差异
"""

import os
import time
import json
import tempfile
from typing import Dict, List
import argparse

def test_whisper_loading():
    """测试Whisper模型加载速度"""
    print("🧪 测试1: Whisper模型加载速度对比")
    
    # 测试原版
    print("📦 测试原版模型加载...")
    start_time = time.time()
    try:
        from core import WhisperModelSingleton
        model = WhisperModelSingleton.get_instance()
        original_load_time = time.time() - start_time
        print(f"✅ 原版加载时间: {original_load_time:.2f}秒")
    except Exception as e:
        print(f"❌ 原版加载失败: {e}")
        original_load_time = float('inf')
    
    # 测试优化版
    print("⚡ 测试优化版模型加载...")
    start_time = time.time()
    try:
        from core_optimized import OptimizedWhisperModel
        model = OptimizedWhisperModel.get_instance()
        optimized_load_time = time.time() - start_time
        print(f"✅ 优化版加载时间: {optimized_load_time:.2f}秒")
    except Exception as e:
        print(f"❌ 优化版加载失败: {e}")
        optimized_load_time = float('inf')
    
    # 对比结果
    if original_load_time != float('inf') and optimized_load_time != float('inf'):
        improvement = ((original_load_time - optimized_load_time) / original_load_time) * 100
        print(f"📊 模型加载性能提升: {improvement:.1f}%")
    
    return {
        "original_load_time": original_load_time,
        "optimized_load_time": optimized_load_time
    }

def test_audio_processing_speed(test_audio_path: str = None):
    """测试音频处理速度"""
    print("🧪 测试2: 音频处理速度对比")
    
    # 如果没有提供测试音频，创建一个简单的测试文件
    if not test_audio_path or not os.path.exists(test_audio_path):
        print("🎵 创建测试音频文件...")
        try:
            from pydub import AudioSegment
            from pydub.generators import Sine
            
            # 创建3分钟的测试音频（正弦波）
            duration = 3 * 60 * 1000  # 3分钟
            test_tone = Sine(440).to_audio_segment(duration=duration)  # A音，440Hz
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            test_tone.export(temp_file.name, format="wav")
            test_audio_path = temp_file.name
            print(f"✅ 测试音频已创建: {test_audio_path}")
        except Exception as e:
            print(f"❌ 创建测试音频失败: {e}")
            return None
    
    if not test_audio_path:
        print("❌ 无法获取测试音频，跳过处理速度测试")
        return None
    
    results = {}
    
    # 测试原版处理
    print("📦 测试原版音频处理...")
    try:
        from core import MeetingProcessor
        
        processor = MeetingProcessor()
        start_time = time.time()
        
        result = processor.process_with_speaker_id(test_audio_path)
        
        original_time = time.time() - start_time
        results['original'] = {
            'processing_time': original_time,
            'transcript_length': len(result.get('transcript', '')),
            'speaker_count': result.get('speaker_count', 0)
        }
        print(f"✅ 原版处理完成: {original_time:.2f}秒")
        print(f"   转写长度: {results['original']['transcript_length']} 字符")
        print(f"   发言人数: {results['original']['speaker_count']}")
        
    except Exception as e:
        print(f"❌ 原版处理失败: {e}")
        results['original'] = None
    
    # 测试优化版处理
    print("⚡ 测试优化版音频处理...")
    try:
        from core_optimized import OptimizedMeetingProcessor
        
        processor = OptimizedMeetingProcessor()
        start_time = time.time()
        
        result = processor.process_with_optimization(test_audio_path)
        
        optimized_time = time.time() - start_time
        results['optimized'] = {
            'processing_time': optimized_time,
            'transcript_length': len(result.get('transcript', '')),
            'speaker_count': result.get('speaker_count', 0),
            'stats': result.get('processing_stats', {})
        }
        print(f"✅ 优化版处理完成: {optimized_time:.2f}秒")
        print(f"   转写长度: {results['optimized']['transcript_length']} 字符")
        print(f"   发言人数: {results['optimized']['speaker_count']}")
        print(f"   详细统计: {results['optimized']['stats']}")
        
    except Exception as e:
        print(f"❌ 优化版处理失败: {e}")
        import traceback
        traceback.print_exc()
        results['optimized'] = None
    
    # 对比结果
    if results.get('original') and results.get('optimized'):
        original_time = results['original']['processing_time']
        optimized_time = results['optimized']['processing_time']
        
        if original_time > 0:
            improvement = ((original_time - optimized_time) / original_time) * 100
            speed_ratio = original_time / optimized_time
            
            print(f"\n📊 音频处理性能对比:")
            print(f"   原版处理时间: {original_time:.2f}秒")
            print(f"   优化版处理时间: {optimized_time:.2f}秒")
            print(f"   性能提升: {improvement:.1f}%")
            print(f"   速度比: {speed_ratio:.2f}x")
    
    # 清理测试文件
    try:
        if test_audio_path and os.path.exists(test_audio_path):
            os.unlink(test_audio_path)
            print("🗑️ 测试文件已清理")
    except:
        pass
    
    return results

def test_memory_usage():
    """测试内存使用情况"""
    print("🧪 测试3: 内存使用对比")
    
    try:
        import psutil
        import gc
        
        # 获取初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"📊 初始内存使用: {initial_memory:.2f} MB")
        
        # 测试原版内存使用
        print("📦 测试原版内存使用...")
        try:
            from core import MeetingProcessor
            processor = MeetingProcessor()
            
            # 强制垃圾回收
            gc.collect()
            original_memory = process.memory_info().rss / 1024 / 1024
            original_delta = original_memory - initial_memory
            
            print(f"✅ 原版内存使用: {original_memory:.2f} MB (+{original_delta:.2f} MB)")
            
        except Exception as e:
            print(f"❌ 原版内存测试失败: {e}")
            original_memory = None
        
        # 清理
        del processor if 'processor' in locals() else None
        gc.collect()
        
        # 测试优化版内存使用
        print("⚡ 测试优化版内存使用...")
        try:
            from core_optimized import OptimizedMeetingProcessor
            processor = OptimizedMeetingProcessor()
            
            gc.collect()
            optimized_memory = process.memory_info().rss / 1024 / 1024
            optimized_delta = optimized_memory - initial_memory
            
            print(f"✅ 优化版内存使用: {optimized_memory:.2f} MB (+{optimized_delta:.2f} MB)")
            
        except Exception as e:
            print(f"❌ 优化版内存测试失败: {e}")
            optimized_memory = None
        
        # 对比结果
        if original_memory and optimized_memory:
            memory_improvement = ((original_delta - optimized_delta) / original_delta) * 100 if original_delta > 0 else 0
            print(f"\n📊 内存使用对比:")
            print(f"   原版增量: +{original_delta:.2f} MB")
            print(f"   优化版增量: +{optimized_delta:.2f} MB")
            print(f"   内存优化: {memory_improvement:.1f}%")
        
        return {
            "initial": initial_memory,
            "original": original_memory,
            "optimized": optimized_memory
        }
        
    except ImportError:
        print("❌ psutil不可用，跳过内存测试")
        return None

def test_gpu_optimization():
    """测试GPU优化效果"""
    print("🧪 测试4: GPU优化效果")
    
    try:
        import torch
        
        if not torch.cuda.is_available():
            print("❌ GPU不可用，跳过GPU测试")
            return None
        
        print(f"✅ GPU可用: {torch.cuda.get_device_name()}")
        print(f"📊 GPU内存总量: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        
        # 测试优化配置的GPU内存管理
        from core_optimized import OPTIMIZE_CONFIG
        
        print(f"⚙️ GPU优化配置:")
        print(f"   内存优化启用: {OPTIMIZE_CONFIG.get('enable_gpu_memory_optimization', False)}")
        
        # 检查当前GPU内存使用
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        
        print(f"📊 当前GPU内存:")
        print(f"   已分配: {allocated:.2f} GB")
        print(f"   已保留: {reserved:.2f} GB")
        
        return {
            "gpu_available": True,
            "gpu_name": torch.cuda.get_device_name(),
            "total_memory_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
            "allocated_gb": allocated,
            "reserved_gb": reserved,
            "optimization_enabled": OPTIMIZE_CONFIG.get('enable_gpu_memory_optimization', False)
        }
        
    except ImportError:
        print("❌ PyTorch不可用，跳过GPU测试")
        return None

def generate_performance_report(results: Dict):
    """生成性能测试报告"""
    print("\n" + "="*60)
    print("📋 ConferenceAssistant 优化效果报告")
    print("="*60)
    
    # 模型加载报告
    if 'model_loading' in results and results['model_loading']:
        data = results['model_loading']
        print(f"\n🚀 模型加载性能:")
        if data['original_load_time'] != float('inf'):
            print(f"   原版: {data['original_load_time']:.2f}秒")
        if data['optimized_load_time'] != float('inf'):
            print(f"   优化版: {data['optimized_load_time']:.2f}秒")
            
            if data['original_load_time'] != float('inf'):
                improvement = ((data['original_load_time'] - data['optimized_load_time']) / data['original_load_time']) * 100
                print(f"   提升: {improvement:.1f}%")
    
    # 音频处理报告
    if 'audio_processing' in results and results['audio_processing']:
        data = results['audio_processing']
        print(f"\n🎵 音频处理性能:")
        
        if data.get('original'):
            print(f"   原版处理时间: {data['original']['processing_time']:.2f}秒")
        
        if data.get('optimized'):
            print(f"   优化版处理时间: {data['optimized']['processing_time']:.2f}秒")
            
            if data.get('original'):
                improvement = ((data['original']['processing_time'] - data['optimized']['processing_time']) / data['original']['processing_time']) * 100
                speed_ratio = data['original']['processing_time'] / data['optimized']['processing_time']
                print(f"   性能提升: {improvement:.1f}%")
                print(f"   速度比: {speed_ratio:.2f}x")
    
    # 内存使用报告
    if 'memory_usage' in results and results['memory_usage']:
        data = results['memory_usage']
        print(f"\n💾 内存使用:")
        print(f"   初始内存: {data['initial']:.2f} MB")
        if data['original']:
            print(f"   原版峰值: {data['original']:.2f} MB")
        if data['optimized']:
            print(f"   优化版峰值: {data['optimized']:.2f} MB")
    
    # GPU优化报告
    if 'gpu_optimization' in results and results['gpu_optimization']:
        data = results['gpu_optimization']
        print(f"\n🎮 GPU优化:")
        if data['gpu_available']:
            print(f"   GPU: {data['gpu_name']}")
            print(f"   总内存: {data['total_memory_gb']:.1f} GB")
            print(f"   当前使用: {data['allocated_gb']:.2f} GB")
            print(f"   优化启用: {'是' if data['optimization_enabled'] else '否'}")
        else:
            print("   GPU不可用")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="ConferenceAssistant 优化效果测试")
    parser.add_argument("--audio", help="测试音频文件路径（可选）")
    parser.add_argument("--skip-model", action="store_true", help="跳过模型加载测试")
    parser.add_argument("--skip-audio", action="store_true", help="跳过音频处理测试")
    parser.add_argument("--skip-memory", action="store_true", help="跳过内存测试")
    parser.add_argument("--skip-gpu", action="store_true", help="跳过GPU测试")
    parser.add_argument("--output", help="保存结果到JSON文件")
    
    args = parser.parse_args()
    
    print("🧪 ConferenceAssistant 优化效果测试")
    print("=" * 50)
    
    results = {}
    
    # 1. 模型加载测试
    if not args.skip_model:
        results['model_loading'] = test_whisper_loading()
    
    # 2. 音频处理测试
    if not args.skip_audio:
        results['audio_processing'] = test_audio_processing_speed(args.audio)
    
    # 3. 内存使用测试
    if not args.skip_memory:
        results['memory_usage'] = test_memory_usage()
    
    # 4. GPU优化测试
    if not args.skip_gpu:
        results['gpu_optimization'] = test_gpu_optimization()
    
    # 生成报告
    generate_performance_report(results)
    
    # 保存结果
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"📄 结果已保存到: {args.output}")
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")

if __name__ == "__main__":
    main()