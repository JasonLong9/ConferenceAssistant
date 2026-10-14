#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pyannote鍙戣█浜哄垎绂绘祴璇曡剼鏈?
"""

import os
import sys
import torch
from pathlib import Path

# 妫€鏌ヤ緷璧?
try:
    from pyannote.audio import Pipeline
    from pyannote.core import Segment
    print("pyannote.audio 宸插畨瑁?)
except ImportError:
    print("閿欒: pyannote.audio 鏈畨瑁咃紝璇疯繍琛? pip install pyannote.audio")
    sys.exit(1)

def test_pyannote():
    """娴嬭瘯pyannote鍙戣█浜哄垎绂?""
    print("=" * 60)
    print("pyannote 鍙戣█浜哄垎绂绘祴璇?)
    print("=" * 60)
    
    # 璁剧疆Hugging Face token
    hf_token = "os.getenv("HF_TOKEN", "your_huggingface_token")"
    os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
    
    print("姝ｅ湪鍔犺浇pyannote妯″瀷...")
    try:
        # 鍔犺浇棰勮缁冪殑鍙戣█浜哄垎绂绘ā鍨?
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        print("妯″瀷鍔犺浇鎴愬姛!")
    except Exception as e:
        print(f"妯″瀷鍔犺浇澶辫触: {e}")
        return False
    
    # 妫€鏌ラ煶棰戞枃浠?
    test_audio_path = "test_file/娌冲寳浜鸿浠茶闇€姹備細-1.mp3"
    if not os.path.exists(test_audio_path):
        print(f"娴嬭瘯闊抽鏂囦欢涓嶅瓨鍦? {test_audio_path}")
        # 璇㈤棶鐢ㄦ埛鎻愪緵闊抽鏂囦欢
        user_audio = input("璇疯緭鍏ラ煶棰戞枃浠惰矾寰?(鏀寔 .wav, .mp3, .m4a 绛夋牸寮?: ").strip()
        if user_audio and os.path.exists(user_audio):
            test_audio_path = user_audio
        else:
            print("鏈彁渚涙湁鏁堢殑闊抽鏂囦欢璺緞")
            return False
    
    print(f"姝ｅ湪澶勭悊闊抽鏂囦欢: {test_audio_path}")
    
    try:
        # 杩愯鍙戣█浜哄垎绂?
        diarization = pipeline(test_audio_path)
        
        print("\n鍙戣█浜哄垎绂荤粨鏋?")
        print("-" * 50)
        
        # 鏀堕泦鍜屾樉绀虹粨鏋?
        speakers_info = {}
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start_time = turn.start
            end_time = turn.end
            duration = end_time - start_time
            
            if speaker not in speakers_info:
                speakers_info[speaker] = []
            speakers_info[speaker].append((start_time, end_time, duration))
            
            print(f"鍙戣█浜?{speaker}: {start_time:.2f}s - {end_time:.2f}s (鏃堕暱: {duration:.2f}s)")
        
        # 缁熻淇℃伅
        print(f"\n缁熻淇℃伅:")
        print(f"妫€娴嬪埌 {len(speakers_info)} 涓彂瑷€浜?)
        
        total_speech_time = 0
        for speaker, segments in speakers_info.items():
            total_duration = sum(seg[2] for seg in segments)
            segment_count = len(segments)
            total_speech_time += total_duration
            print(f"  {speaker}: {segment_count}涓墖娈? 鎬诲彂瑷€鏃堕暱 {total_duration:.2f}绉?)
        
        print(f"\n鎬诲彂瑷€鏃堕暱: {total_speech_time:.2f}绉?)
        print("鍙戣█浜哄垎绂绘祴璇曞畬鎴?")
        
        return True
        
    except Exception as e:
        print(f"鍙戣█浜哄垎绂诲鐞嗗け璐? {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓诲嚱鏁?""
    print("妫€鏌ョ郴缁熺幆澧?..")
    print(f"Python鐗堟湰: {sys.version}")
    print(f"PyTorch鐗堟湰: {torch.__version__}")
    print(f"CUDA鍙敤: {torch.cuda.is_available()}")
    print()
    
    success = test_pyannote()
    
    if success:
        print("\n娴嬭瘯鎴愬姛! pyannote鍙戣█浜哄垎绂诲姛鑳芥甯稿伐浣?)
    else:
        print("\n娴嬭瘯澶辫触! 璇锋鏌ラ敊璇俊鎭?)
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n鐢ㄦ埛涓柇娴嬭瘯")
        sys.exit(1)
    except Exception as e:
        print(f"\n娴嬭瘯杩囩▼涓彂鐢熸湭棰勬湡閿欒: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
