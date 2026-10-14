from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
import os
import uuid
import traceback

app = FastAPI()
try:
    model = WhisperModel("whisper-large-v3", device="cuda", compute_type="float16")
except Exception as e:
    raise RuntimeError(f"模型加载失败: {e}")

def transcribe_audio(model, audio_path):
    """
    快速转写音频文件，返回文本、segments、info
    """
    segments, info = model.transcribe(audio_path)
    text = "".join([seg.text for seg in segments])
    return text, segments, info

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    # 检查文件类型
    if not file.filename.lower().endswith((".mp3", ".wav", ".m4a", ".flac", ".ogg")):
        raise HTTPException(status_code=400, detail="仅支持音频文件（mp3, wav, m4a, flac, ogg）")
    temp_audio_path = f"temp_{uuid.uuid4().hex}_{file.filename}"
    try:
        with open(temp_audio_path, "wb") as f:
            f.write(await file.read())
        # 调用快速转写函数
        text, segments, info = transcribe_audio(model, temp_audio_path)
        # 保存转写文本到本地 txt 文件
        txt_save_path = f"{file.filename}.txt"
        with open(txt_save_path, "w", encoding="utf-8") as f:
            f.write(text)
        return JSONResponse({
            "text": text,
            "filename": file.filename,
            "language": getattr(info, "language", None),
            "duration": getattr(info, "duration", None)
        })
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"转写失败: {e}")
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path) 