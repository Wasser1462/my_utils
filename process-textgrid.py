# Author: zyw
# Date: 2024-09-11
# Description: Process TextGrid files and WAV files, extract information and save for ASR task.

import os
import argparse
from textgrid import TextGrid
from pydub import AudioSegment

def process_textgrid_and_wav(textgrid_path, wav_dir, output_dir, stats):
    print(f"Processing TextGrid: {textgrid_path}")
    
    try:
        tg = TextGrid.fromFile(textgrid_path)
    except Exception as e:
        print(f"Error reading TextGrid file {textgrid_path}: {e}")
        stats['failed'] += 1
        return

    wav_filename = os.path.basename(textgrid_path).replace(".TextGrid", ".wav")
    wav_filepath = os.path.join(wav_dir, wav_filename)
    print(f"Corresponding WAV file: {wav_filepath}")
    
    if not os.path.exists(wav_filepath):
        print(f"WAV file not found for: {textgrid_path}")
        stats['failed'] += 1
        return
    
    try:
        audio = AudioSegment.from_wav(wav_filepath)
    except Exception as e:
        print(f"Error loading WAV file {wav_filepath}: {e}")
        stats['failed'] += 1
        return
    
    tier = None
    for t in tg.tiers:
        if t.name == "内容层":
            tier = t
            break

    if tier is None:
        print(f"No '内容层' tier found in: {textgrid_path}")
        stats['failed'] += 1
        return

    print(f"'内容层' tier found, processing intervals...")

    wav_scp_lines = []
    text_lines = []
    segment_count = 0  # 记录成功处理的片段数量

    for interval in tier.intervals:
        if interval.mark.strip():  # 如果 text 不为空
            start_time = interval.minTime * 1000  # 转为毫秒
            end_time = interval.maxTime * 1000  # 转为毫秒
            text = interval.mark.strip()
            
            # 文件命名规则，将时间格式化为7位数
            segment_filename = f"{wav_filename.replace('.wav', '')}-{start_time:07.0f}-{end_time:07.0f}"
            segment_wav_path = os.path.join(output_dir, "wav", f"{segment_filename}.wav")
            
            print(f"Exporting segment {segment_filename} from {start_time}ms to {end_time}ms")
            
            # 切割音频并保存
            try:
                segment_audio = audio[start_time:end_time]
                segment_audio.export(segment_wav_path, format="wav")
                segment_count += 1
            except Exception as e:
                print(f"Error exporting segment {segment_filename}: {e}")
                continue
            
            # 生成 wav.scp 和 text
            wav_scp_lines.append(f"{segment_filename} {segment_wav_path}")
            text_lines.append(f"{segment_filename} {text}")

    if segment_count > 0:
        # 保存 wav.scp 和 text 文件
        wav_scp_path = os.path.join(output_dir, "wav.scp")
        text_path = os.path.join(output_dir, "text")

        print(f"Writing wav.scp and text files...")

        try:
            with open(wav_scp_path, "a") as wav_scp_file:
                wav_scp_file.write("\n".join(wav_scp_lines) + "\n")

            with open(text_path, "a") as text_file:
                text_file.write("\n".join(text_lines) + "\n")
            
            stats['successful'] += 1
        except Exception as e:
            print(f"Error writing wav.scp or text file: {e}")
            stats['failed'] += 1
    else:
        stats['failed'] += 1

    print("Processing complete for: ", textgrid_path)

def main():

    parser = argparse.ArgumentParser(description="Process TextGrid and WAV files for ASR task.")
    parser.add_argument('textgrid_dir', type=str, help="Directory containing TextGrid files")
    parser.add_argument('wav_dir', type=str, help="Directory containing WAV files")
    parser.add_argument('output_dir', type=str, help="Output directory for processed files (wav.scp, text)")
    
    args = parser.parse_args()

    print(f"Starting to process TextGrid files from: {args.textgrid_dir}")
    
    os.makedirs(os.path.join(args.output_dir, "wav"), exist_ok=True)
    
    stats = {
        'successful': 0,
        'failed': 0
    }

    for textgrid_file in os.listdir(args.textgrid_dir):
        if textgrid_file.endswith(".TextGrid"):
            textgrid_path = os.path.join(args.textgrid_dir, textgrid_file)
            process_textgrid_and_wav(textgrid_path, args.wav_dir, args.output_dir, stats)

    print(f"Processing complete. Successful: {stats['successful']}, Failed: {stats['failed']}")

if __name__ == "__main__":
    main()
