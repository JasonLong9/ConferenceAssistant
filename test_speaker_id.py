#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pyannote鍙戣█浜哄垎绂绘祴璇曡剼鏈?
浣跨敤鏂瑰紡: python test_speaker_id.py [闊抽鏂囦欢璺緞]
"""

import os
import sys
import time
from pathlib import Path

# 娣诲姞褰撳墠鐩綍鍒拌矾寰?
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pyannote.audio import Pipeline
    from pyannote.core import Segment
    import torch
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    print("璀﹀憡: pyannote.audio鏈畨瑁咃紝灏嗕娇鐢ㄥ師鏈夌殑鍙戣█浜鸿瘑鍒姛鑳?)

try:
    from speaker_identification import test_speaker_identification
    from core import MeetingProcessor
    ORIGINAL_AVAILABLE = True
except ImportError:
    ORIGINAL_AVAILABLE = False
    print("璀﹀憡: 鍘熸湁妯″潡鏈壘鍒?)

def test_pyannote_setup():
    """娴嬭瘯pyannote鐜閰嶇疆"""
    if not PYANNOTE_AVAILABLE:
        print("pyannote.audio鏈畨瑁咃紝璇峰厛瀹夎锛歱ip install pyannote.audio")
        return None
        
    print("姝ｅ湪娴嬭瘯pyannote璁剧疆...")
    
    # 璁剧疆Hugging Face token
    hf_token = "os.getenv("HF_TOKEN", "your_huggingface_token")"
    os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
    
    try:
        # 鍔犺浇棰勮缁冪殑鍙戣█浜哄垎绂绘ā鍨?
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        print("鉁?pyannote妯″瀷鍔犺浇鎴愬姛")
        return pipeline
    except Exception as e:
        print(f"鉁?pyannote妯″瀷鍔犺浇澶辫触: {e}")
        return None

def perform_pyannote_diarization(audio_file_path, pipeline):
    """浣跨敤pyannote杩涜鍙戣█浜哄垎绂?""
    try:
        print(f"姝ｅ湪浣跨敤pyannote澶勭悊闊抽鏂囦欢: {audio_file_path}")
        
        # 杩愯鍙戣█浜哄垎绂?
        diarization = pipeline(audio_file_path)
        
        print("\npyannote鍙戣█浜哄垎绂荤粨鏋?")
        print("-" * 50)
        
        # 杈撳嚭缁撴灉
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
        for speaker, segments in speakers_info.items():
            total_duration = sum(seg[2] for seg in segments)
            segment_count = len(segments)
            print(f"  {speaker}: {segment_count}涓墖娈? 鎬绘椂闀縶total_duration:.2f}绉?)
        
        return diarization
        
    except Exception as e:
        print(f"pyannote鍙戣█浜哄垎绂诲鐞嗗け璐? {e}")
        import traceback
        traceback.print_exc()
        return None

def test_basic_speaker_identification():
    """娴嬭瘯鍩虹澹扮汗璇嗗埆鍔熻兘"""
    print("="*60)
    print("娴嬭瘯1: pyannote鍙戣█浜哄垎绂诲姛鑳?)
    print("="*60)
    
    # 娴嬭瘯pyannote璁剧疆
    pipeline = test_pyannote_setup()
    if not pipeline:
        print("pyannote璁剧疆澶辫触锛岃烦杩囨娴嬭瘯")
        return False
    
    # 浣跨敤椤圭洰涓殑娴嬭瘯闊抽
    test_audio_path = "test_file/娌冲寳浜鸿浠茶闇€姹備細-1.mp3"
    
    if not os.path.exists(test_audio_path):
        print(f"閿欒锛氭祴璇曢煶棰戞枃浠朵笉瀛樺湪: {test_audio_path}")
        print("璇风‘淇濇祴璇曟枃浠跺瓨鍦紝鎴栨彁渚涘叾浠栭煶棰戞枃浠惰矾寰?)
        # 璇㈤棶鐢ㄦ埛鎻愪緵闊抽鏂囦欢
        user_audio = input("璇疯緭鍏ラ煶棰戞枃浠惰矾寰? ").strip()
        if user_audio and os.path.exists(user_audio):
            test_audio_path = user_audio
        else:
            return False
    
    try:
        result = perform_pyannote_diarization(test_audio_path, pipeline)
        return result is not None
    except Exception as e:
        print(f"鍩虹娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_processing():
    """娴嬭瘯闆嗘垚鐨勪細璁鐞嗗姛鑳?""
    print("\n" + "="*60)
    print("娴嬭瘯2: 闆嗘垚浼氳澶勭悊鍔熻兘锛堝甫澹扮汗璇嗗埆锛?)
    print("="*60)
    
    test_audio_path = "test_file/娌冲寳浜鸿浠茶闇€姹備細-1.mp3"
    
    if not os.path.exists(test_audio_path):
        print(f"閿欒锛氭祴璇曢煶棰戞枃浠朵笉瀛樺湪: {test_audio_path}")
        return False
    
    try:
        print("鍒濆鍖栦細璁鐞嗗櫒...")
        processor = MeetingProcessor()
        
        print("寮€濮嬪鐞嗭紙鍚敤澹扮汗璇嗗埆锛?..")
        start_time = time.time()
        
        result = processor.process_with_speaker_id(
            audio_path=test_audio_path,
            meeting_name="娴嬭瘯浼氳",
            output_dir="test_output",
            enable_speaker_id=True
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print("\n" + "="*40)
        print("澶勭悊瀹屾垚锛佺粨鏋滄憳瑕?")
        print("="*40)
        print(f"澶勭悊鏃堕棿: {processing_time:.2f}绉?)
        print(f"璇嗗埆鍙戣█浜烘暟: {result['speaker_count']}")
        print(f"浼氳鍚嶇О: {result['meeting_name']}")
        print(f"杞啓鍐呭鏂囦欢: {result['transcript_markdown_path']}")
        print(f"浼氳绾鏂囦欢: {result['minutes_markdown_path']}")
        
        print(f"\n杞啓鍐呭棰勮锛堝墠500瀛楃锛?")
        print("-" * 50)
        print(result['transcript'][:500] + "..." if len(result['transcript']) > 500 else result['transcript'])
        
        print(f"\n浼氳绾棰勮锛堝墠500瀛楃锛?")
        print("-" * 50)
        print(result['minutes'][:500] + "..." if len(result['minutes']) > 500 else result['minutes'])
        
        return True
        
    except Exception as e:
        print(f"闆嗘垚娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comparison():
    """瀵规瘮娴嬭瘯锛氭湁鏃犲０绾硅瘑鍒殑宸紓"""
    print("\n" + "="*60)
    print("娴嬭瘯3: 瀵规瘮娴嬭瘯锛堟湁鏃犲０绾硅瘑鍒殑宸紓锛?)
    print("="*60)
    
    test_audio_path = "test_file/娌冲寳浜鸿浠茶闇€姹備細-1.mp3"
    
    if not os.path.exists(test_audio_path):
        print(f"閿欒锛氭祴璇曢煶棰戞枃浠朵笉瀛樺湪: {test_audio_path}")
        return False
    
    try:
        processor = MeetingProcessor()
        
        print("澶勭悊1: 涓嶄娇鐢ㄥ０绾硅瘑鍒?..")
        start_time = time.time()
        result_without = processor.process_with_speaker_id(
            audio_path=test_audio_path,
            meeting_name="瀵规瘮娴嬭瘯_鏃犲０绾?,
            output_dir="test_output",
            enable_speaker_id=False
        )
        time_without = time.time() - start_time
        
        print("澶勭悊2: 浣跨敤澹扮汗璇嗗埆...")
        start_time = time.time()
        result_with = processor.process_with_speaker_id(
            audio_path=test_audio_path,
            meeting_name="瀵规瘮娴嬭瘯_鏈夊０绾?,
            output_dir="test_output",
            enable_speaker_id=True
        )
        time_with = time.time() - start_time
        
        print("\n" + "="*40)
        print("瀵规瘮缁撴灉:")
        print("="*40)
        print(f"鏃犲０绾硅瘑鍒?- 澶勭悊鏃堕棿: {time_without:.2f}绉?)
        print(f"鏈夊０绾硅瘑鍒?- 澶勭悊鏃堕棿: {time_with:.2f}绉? 璇嗗埆鍙戣█浜? {result_with['speaker_count']}涓?)
        print(f"鏃堕棿澧炲姞: {((time_with - time_without) / time_without * 100):.1f}%")
        
        print(f"\n杞啓鍐呭瀵规瘮:")
        print("-" * 50)
        print("鏃犲０绾硅瘑鍒増鏈紙鍓?00瀛楃锛?")
        print(result_without['transcript'][:200] + "...")
        print("\n鏈夊０绾硅瘑鍒増鏈紙鍓?00瀛楃锛?")
        print(result_with['transcript'][:200] + "...")
        
        return True
        
    except Exception as e:
        print(f"瀵规瘮娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓绘祴璇曞嚱鏁?""
    print("澹扮汗璇嗗埆娴嬭瘯寮€濮?)
    print("=" * 60)
    
    # 鍒涘缓娴嬭瘯杈撳嚭鐩綍
    os.makedirs("test_output", exist_ok=True)
    
    # 濡傛灉鍛戒护琛屾彁渚涗簡闊抽鏂囦欢锛屼娇鐢ㄥ畠
    if len(sys.argv) > 1:
        custom_audio = sys.argv[1]
        if os.path.exists(custom_audio):
            print(f"浣跨敤鑷畾涔夐煶棰戞枃浠? {custom_audio}")
            # 涓存椂鏇挎崲娴嬭瘯鏂囦欢璺緞锛堣繖閲屽彲浠ヤ紭鍖栵級
            global test_audio_path
            test_audio_path = custom_audio
    
    test_results = []
    
    # 杩愯鎵€鏈夋祴璇?
    print("寮€濮嬭繍琛屾祴璇曞浠?..")
    
    # 娴嬭瘯1: 鍩虹澹扮汗璇嗗埆
    try:
        result1 = test_basic_speaker_identification()
        test_results.append(("鍩虹澹扮汗璇嗗埆", result1))
    except Exception as e:
        print(f"娴嬭瘯1寮傚父: {e}")
        test_results.append(("鍩虹澹扮汗璇嗗埆", False))
    
    # 娴嬭瘯2: 闆嗘垚澶勭悊
    try:
        result2 = test_integrated_processing()
        test_results.append(("闆嗘垚澶勭悊", result2))
    except Exception as e:
        print(f"娴嬭瘯2寮傚父: {e}")
        test_results.append(("闆嗘垚澶勭悊", False))
    
    # 娴嬭瘯3: 瀵规瘮娴嬭瘯
    try:
        result3 = test_comparison()
        test_results.append(("瀵规瘮娴嬭瘯", result3))
    except Exception as e:
        print(f"娴嬭瘯3寮傚父: {e}")
        test_results.append(("瀵规瘮娴嬭瘯", False))
    
    # 鎬荤粨娴嬭瘯缁撴灉
    print("\n" + "="*60)
    print("娴嬭瘯缁撴灉鎬荤粨")
    print("="*60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
    
    print(f"\n鎬讳綋缁撴灉: {passed}/{total} 閫氳繃")
    
    if passed == total:
        print("鎵€鏈夋祴璇曢€氳繃锛佸０绾硅瘑鍒姛鑳介泦鎴愭垚鍔燂紒")
        print("\n鎺ヤ笅鏉ヤ綘鍙互:")
        print("1. 浣跨敤 python main.py [闊抽鏂囦欢] --enable_speaker_id 杩涜瀹屾暣娴嬭瘯")
        print("2. 鏌ョ湅 test_output 鐩綍涓殑杈撳嚭鏂囦欢")
        print("3. 鏍规嵁闇€瑕佽皟鏁村弬鏁板拰閰嶇疆")
    else:
        print("璀﹀憡: 閮ㄥ垎娴嬭瘯澶辫触锛岃妫€鏌ラ敊璇俊鎭苟淇")
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
