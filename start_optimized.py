#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConferenceAssistant 优化版启动脚本
提供简单的命令行界面来启动不同版本的服务
"""

import os
import sys
import argparse
import subprocess
import time
from typing import Optional

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    dependencies = {
        'torch': 'PyTorch',
        'faster_whisper': 'Faster-Whisper',
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydub': 'Pydub',
        'requests': 'Requests',
        'python-dotenv': 'Python-dotenv'
    }
    
    missing = []
    
    for module, name in dependencies.items():
        try:
            __import__(module.replace('-', '_'))
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - 缺失")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  缺少依赖项: {', '.join(missing)}")
        print("请运行: pip install " + " ".join(missing))
        return False
    
    print("✅ 所有依赖项已安装")
    return True

def check_environment():
    """检查环境配置"""
    print("\n🌍 检查环境配置...")
    
    # 检查API密钥
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY 未配置")
        print("请在 .env 文件中设置: DEEPSEEK_API_KEY=your_api_key")
        return False
    else:
        print(f"✅ DEEPSEEK_API_KEY 已配置 ({api_key[:8]}...)")
    
    # 检查GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name()
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"✅ GPU可用: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            print("⚠️  GPU不可用，将使用CPU模式")
    except ImportError:
        print("⚠️  PyTorch不可用，无法检查GPU")
    
    # 检查输出目录
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ 已创建输出目录: {output_dir}")
    else:
        print(f"✅ 输出目录存在: {output_dir}")
    
    return True

def start_optimized_service(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """启动优化版服务"""
    print(f"\n🚀 启动优化版ConferenceAssistant服务...")
    print(f"📡 地址: http://{host}:{port}")
    print(f"📖 文档: http://{host}:{port}/docs")
    
    try:
        import uvicorn
        
        # 显示优化配置
        from core_optimized import OPTIMIZE_CONFIG
        print(f"⚡ 优化配置:")
        for key, value in OPTIMIZE_CONFIG.items():
            print(f"   {key}: {value}")
        
        print("\n" + "="*50)
        print("服务启动中...")
        print("按 Ctrl+C 停止服务")
        print("="*50)
        
        # 启动服务
        uvicorn.run(
            "web_service_optimized:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except ImportError:
        print("❌ uvicorn未安装，请运行: pip install uvicorn")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def start_original_service(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """启动原版服务"""
    print(f"\n🔄 启动原版ConferenceAssistant服务...")
    print(f"📡 地址: http://{host}:{port}")
    print(f"📖 文档: http://{host}:{port}/docs")
    
    try:
        import uvicorn
        
        print("\n" + "="*50)
        print("服务启动中...")
        print("按 Ctrl+C 停止服务")
        print("="*50)
        
        # 启动原版服务
        uvicorn.run(
            "web_service:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except ImportError:
        print("❌ uvicorn未安装，请运行: pip install uvicorn")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def run_performance_test():
    """运行性能测试"""
    print("\n🧪 运行性能测试...")
    
    try:
        subprocess.run([sys.executable, "test_optimization.py"], check=True)
    except FileNotFoundError:
        print("❌ 测试脚本不存在: test_optimization.py")
    except subprocess.CalledProcessError as e:
        print(f"❌ 测试失败: {e}")

def interactive_mode():
    """交互模式"""
    print("🎛️  ConferenceAssistant 启动器")
    print("=" * 40)
    
    while True:
        print("\n请选择操作:")
        print("1. 启动优化版服务 (推荐)")
        print("2. 启动原版服务")
        print("3. 运行性能测试")
        print("4. 检查系统状态")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == "1":
            # 获取启动参数
            host = input("主机地址 (默认: 0.0.0.0): ").strip() or "0.0.0.0"
            port_input = input("端口号 (默认: 8080): ").strip()
            port = int(port_input) if port_input else 8080
            reload = input("开发模式/自动重载? (y/N): ").strip().lower() == 'y'
            
            start_optimized_service(host, port, reload)
            
        elif choice == "2":
            host = input("主机地址 (默认: 0.0.0.0): ").strip() or "0.0.0.0"
            port_input = input("端口号 (默认: 8080): ").strip()
            port = int(port_input) if port_input else 8080
            reload = input("开发模式/自动重载? (y/N): ").strip().lower() == 'y'
            
            start_original_service(host, port, reload)
            
        elif choice == "3":
            run_performance_test()
            
        elif choice == "4":
            print("\n🔍 系统状态检查:")
            check_dependencies()
            check_environment()
            
        elif choice == "5":
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效选项，请重新选择")

def main():
    parser = argparse.ArgumentParser(
        description="ConferenceAssistant 优化版启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python start_optimized.py                    # 交互模式
  python start_optimized.py --optimized        # 直接启动优化版
  python start_optimized.py --original         # 直接启动原版
  python start_optimized.py --test            # 运行性能测试
  python start_optimized.py --check           # 检查环境
        """
    )
    
    # 服务选择
    service_group = parser.add_mutually_exclusive_group()
    service_group.add_argument("--optimized", action="store_true", help="启动优化版服务")
    service_group.add_argument("--original", action="store_true", help="启动原版服务")
    service_group.add_argument("--test", action="store_true", help="运行性能测试")
    service_group.add_argument("--check", action="store_true", help="检查环境状态")
    
    # 服务参数
    parser.add_argument("--host", default="0.0.0.0", help="服务主机地址")
    parser.add_argument("--port", type=int, default=8080, help="服务端口号")
    parser.add_argument("--reload", action="store_true", help="启用自动重载（开发模式）")
    parser.add_argument("--skip-check", action="store_true", help="跳过环境检查")
    
    args = parser.parse_args()
    
    # 打印欢迎信息
    print("🤖 ConferenceAssistant 优化版启动器 v2.0")
    print("=" * 50)
    
    # 环境检查（除非跳过）
    if not args.skip_check:
        if not check_dependencies():
            sys.exit(1)
        
        if not check_environment():
            sys.exit(1)
    
    # 根据参数执行相应操作
    if args.optimized:
        start_optimized_service(args.host, args.port, args.reload)
    elif args.original:
        start_original_service(args.host, args.port, args.reload)
    elif args.test:
        run_performance_test()
    elif args.check:
        print("✅ 环境检查完成")
    else:
        # 默认进入交互模式
        interactive_mode()

if __name__ == "__main__":
    main()