import argparse
import os
from core import MeetingProcessor

def main():
    parser = argparse.ArgumentParser(description="会议音频转写与纪要自动化（本地批量处理，默认启用声纹识别）")
    parser.add_argument("audio", nargs='+', help="音频文件路径（支持批量）")
    parser.add_argument("--meeting_name", type=str, default=None, help="会议主题（可选，若不指定则自动提取）")
    parser.add_argument("--output_dir", type=str, default="outputs", help="输出目录")
    parser.add_argument("--device", type=str, default="auto", help="推理设备（auto/cuda/cpu）")
    args = parser.parse_args()

    processor = MeetingProcessor(device=args.device)
    for audio_path in args.audio:
        if not os.path.exists(audio_path):
            print(f"文件不存在: {audio_path}")
            continue
        print(f"\n处理音频: {audio_path}")
        # 默认启用声纹识别功能
        result = processor.process_with_speaker_id(audio_path, meeting_name=args.meeting_name, output_dir=args.output_dir)
        print(f"识别发言人数: {result['speaker_count']}")
        print(f"转写内容已保存: {result['transcript_markdown_path']}")
        print(f"会议纪要已保存: {result['minutes_markdown_path']}")
        print(f"转写文本片段（前200字）：{result['transcript'][:200]}...")

if __name__ == "__main__":
    main()
