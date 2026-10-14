#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
璁剧疆绂荤嚎pyannote妯″瀷鐨勮剼鏈?
濡傛灉缃戠粶杩炴帴鏀瑰杽鍚庯紝鍙互浣跨敤姝よ剼鏈笅杞藉苟淇濆瓨pyannote妯″瀷渚涚绾夸娇鐢?
"""

import os
import torch
from pathlib import Path

def download_and_save_pyannote_model():
    """涓嬭浇骞朵繚瀛榩yannote妯″瀷鍒版湰鍦?""
    
    try:
        from pyannote.audio import Pipeline
        
        # 璁剧疆妯″瀷淇濆瓨璺緞
        model_dir = Path("models/pyannote")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Hugging Face token
        hf_token = "os.getenv("HF_TOKEN", "your_huggingface_token")"
        os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
        
        print("姝ｅ湪涓嬭浇pyannote妯″瀷...")
        print("杩欏彲鑳介渶瑕佸嚑鍒嗛挓鏃堕棿锛岃鑰愬績绛夊緟...")
        
        # 涓嬭浇妯″瀷
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token,
            cache_dir=str(model_dir)
        )
        
        print(f"鉁?妯″瀷涓嬭浇瀹屾垚锛屼繚瀛樺湪: {model_dir}")
        
        # 娴嬭瘯妯″瀷
        print("姝ｅ湪娴嬭瘯妯″瀷...")
        
        # 鍒涘缓娴嬭瘯闊抽锛?绉掔殑闈欓煶锛?
        import numpy as np
        import soundfile as sf
        
        test_audio = np.zeros(16000)  # 1绉?16kHz闈欓煶
        test_file = "test_audio.wav"
        sf.write(test_file, test_audio, 16000)
        
        # 杩愯娴嬭瘯
        result = pipeline(test_file)
        print("鉁?妯″瀷娴嬭瘯閫氳繃")
        
        # 娓呯悊娴嬭瘯鏂囦欢
        os.remove(test_file)
        
        return True
        
    except Exception as e:
        print(f"鉂?涓嬭浇澶辫触: {e}")
        return False

def load_offline_pyannote_model():
    """鍔犺浇绂荤嚎淇濆瓨鐨刾yannote妯″瀷"""
    
    model_dir = Path("models/pyannote")
    
    if not model_dir.exists():
        print("鉂?绂荤嚎妯″瀷涓嶅瓨鍦紝璇峰厛杩愯涓嬭浇")
        return None
    
    try:
        from pyannote.audio import Pipeline
        
        # 浠庢湰鍦扮紦瀛樺姞杞?
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            cache_dir=str(model_dir)
        )
        
        print("鉁?绂荤嚎妯″瀷鍔犺浇鎴愬姛")
        return pipeline
        
    except Exception as e:
        print(f"鉂?绂荤嚎妯″瀷鍔犺浇澶辫触: {e}")
        return None

def main():
    """涓诲嚱鏁?""
    print("pyannote绂荤嚎妯″瀷璁剧疆宸ュ叿")
    print("=" * 50)
    
    choice = input("""
璇烽€夋嫨鎿嶄綔:
1. 涓嬭浇骞朵繚瀛榩yannote妯″瀷鍒版湰鍦?
2. 娴嬭瘯鍔犺浇绂荤嚎妯″瀷
3. 閫€鍑?

璇疯緭鍏ラ€夋嫨 (1-3): """).strip()
    
    if choice == "1":
        print("\n寮€濮嬩笅杞芥ā鍨?..")
        success = download_and_save_pyannote_model()
        if success:
            print("\n鉁?妯″瀷璁剧疆瀹屾垚锛佺幇鍦ㄥ彲浠ョ绾夸娇鐢╬yannote浜?)
        else:
            print("\n鉂?妯″瀷涓嬭浇澶辫触锛岃妫€鏌ョ綉缁滆繛鎺?)
    
    elif choice == "2":
        print("\n娴嬭瘯绂荤嚎妯″瀷...")
        model = load_offline_pyannote_model()
        if model:
            print("鉁?绂荤嚎妯″瀷鍙互姝ｅ父浣跨敤")
        else:
            print("鉂?绂荤嚎妯″瀷涓嶅彲鐢?)
    
    elif choice == "3":
        print("閫€鍑?)
        return 0
    
    else:
        print("鏃犳晥閫夋嫨")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n鐢ㄦ埛涓柇鎿嶄綔")
        sys.exit(1)
    except Exception as e:
        print(f"\n鍙戠敓閿欒: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
