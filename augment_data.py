# Author: zyw
# Date: 2024-09-10
# Description: 
import os
import json
import argparse
from pydub import AudioSegment
import numpy as np
import shutil
from multiprocessing import Pool
import logging
from check_train_data import check_data_consistency

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

def add_noise(audio_segment, noise_factor=0.02):
    samples = np.array(audio_segment.get_array_of_samples())
    noise = np.random.normal(0, 1, len(samples))
    augmented_samples = samples + noise_factor * noise * np.max(samples)
    augmented_audio = audio_segment._spawn(augmented_samples.astype(np.int16).tobytes())
    return augmented_audio

def speed_up(audio_segment, speed=1.5, min_duration=0.15):
    if len(audio_segment) < min_duration * 1000:
        #print(f"音频长度太短，返回原始音频。长度: {len(audio_segment)/1000:.2f}s")
        return audio_segment
    return audio_segment.speedup(playback_speed=speed)

def slow_down(audio_segment, speed=0.85):
    new_frame_rate = int(audio_segment.frame_rate * speed)
    return audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_frame_rate}).set_frame_rate(audio_segment.frame_rate)

def copy_dev_folder(source_dir, output_dir):
    dev_folder_path = os.path.join(source_dir, "dev")
    dest_path = os.path.join(output_dir, "dev")

    if os.path.exists(dev_folder_path):
        shutil.copytree(dev_folder_path, dest_path) 
    else:
        print(f"源文件夹 {dev_folder_path} 不存在")

def process_audio(input_wav, output_wav_dir, key, augment_types):
    audio = AudioSegment.from_wav(input_wav)

    if len(audio) < 1000:
        #print(f"跳过音频：{input_wav}, 长度小于1秒, 长度: {len(audio)/1000:.2f}s")
        return {}

    output_files = {}
    if 'noise' in augment_types:
        noisy_audio = add_noise(audio)
        output_noise_path = os.path.join(output_wav_dir, f'noise_{key}.wav')
        noisy_audio.export(output_noise_path, format="wav")
        output_files['noise'] = output_noise_path

    if 'fast' in augment_types:
        fast_audio = speed_up(audio)
        output_fast_path = os.path.join(output_wav_dir, f'fast_{key}.wav')
        fast_audio.export(output_fast_path, format="wav")
        output_files['fast'] = output_fast_path

    if 'slow' in augment_types:
        slow_audio = slow_down(audio)
        output_slow_path = os.path.join(output_wav_dir, f'slow_{key}.wav')
        slow_audio.export(output_slow_path, format="wav")
        output_files['slow'] = output_slow_path

    return output_files

def handle_line(wav_scp_line, text_line, data_list_line, output_wav_dir, augment_types):
    try:        
        parts = wav_scp_line.strip().split(maxsplit=1)
        logger.info(f"处理音频文件: {wav_scp_line.strip()}")
        if len(parts) != 2:
            print(f"跳过格式错误的行: {wav_scp_line.strip()}")
            return None

        wav_key, wav_path = parts
        try:
            _, text = text_line.strip().split(maxsplit=1)
            data_list_entry = json.loads(data_list_line.strip())
        except (ValueError, json.JSONDecodeError) as e:
            print(f"跳过无效行: {data_list_line.strip()}，错误: {e}")
            return None

        key = data_list_entry['key']
        wav_file = data_list_entry['wav']
        txt = data_list_entry['txt']

        output_files = process_audio(wav_file, output_wav_dir, key, augment_types)

        # 确保每个增强的音频都写入 wav.scp 和 text 文件
        wav_scp_entries = []
        text_entries = []
        for aug_type, aug_wav_path in output_files.items():
            wav_scp_entries.append(f"{aug_type}_{wav_key} {aug_wav_path}\n")
            text_entries.append(f"{aug_type}_{wav_key} {txt}\n")  # 添加每个增强音频的文本

        # 处理原始音频，未进行增强的数据也要写入
        wav_scp_entries.append(f"{wav_key} {wav_path}\n")
        text_entries.append(f"{wav_key} {txt}\n")

        return wav_key, txt, wav_path, wav_scp_entries, text_entries, output_files  # 返回 wav_path 和其他信息

    except Exception as e:
        print(f"处理 {wav_scp_line.strip()} 时发生错误: {e}")
        return None


def augment_data(input_dir, output_dir, augment_types=['noise', 'fast', 'slow'], num_processes=4):
    wav_scp_path = os.path.join(input_dir, 'wav.scp')
    text_path = os.path.join(input_dir, 'text')
    data_list_path = os.path.join(input_dir, 'data.list')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    train_folder = os.path.join(output_dir, "train")
    os.makedirs(train_folder, exist_ok=True)

    output_wav_dir = os.path.join(output_dir, 'wav')
    os.makedirs(output_wav_dir, exist_ok=True)

    output_wav_scp = os.path.join(train_folder, 'wav.scp')
    output_text = os.path.join(train_folder, 'text')
    output_data_list = os.path.join(train_folder, 'data.list')

    copy_dev_folder("/data2/cuidc/data/data_20231123", output_dir)

    with open(wav_scp_path, 'r') as wav_scp_file, open(text_path, 'r') as text_file, open(data_list_path, 'r') as data_list_file:
        wav_scp_lines = wav_scp_file.readlines()
        text_lines = text_file.readlines()
        data_list_lines = data_list_file.readlines()
        check_data_consistency(wav_scp_lines, text_lines, data_list_lines)

        with Pool(num_processes) as pool, open(output_wav_scp, 'w') as wav_scp_out, open(output_text, 'w') as text_out, open(output_data_list, 'w') as data_list_out:
            tasks = [(wav_scp_line, text_line, data_list_line, output_wav_dir, augment_types)
                     for wav_scp_line, text_line, data_list_line in zip(wav_scp_lines, text_lines, data_list_lines)]

            for result in pool.starmap(handle_line, tasks):
                if result is None:
                    continue
                wav_key, txt, wav_path, wav_scp_entries, text_entries, output_files = result  # 获取 wav_path 和 output_files

                # 写入 wav.scp 相关数据
                for entry in wav_scp_entries:
                    wav_scp_out.write(entry)

                # 写入 text 相关数据
                for text_entry in text_entries:
                    text_out.write(text_entry)

                # 写入 data.list 相关数据，包括原始文件
                data_list_out.write(json.dumps({"key": wav_key, "wav": wav_path, "txt": txt}, ensure_ascii=False) + "\n")
                
                for aug_type, aug_wav_path in output_files.items():
                    new_data_entry = {"key": f"{aug_type}_{wav_key}", "wav": aug_wav_path, "txt": txt}
                    data_list_out.write(json.dumps(new_data_entry, ensure_ascii=False) + "\n")

    print(f"数据增强处理完成, WAV文件保存在 {output_wav_dir}, data.list, wav.scp, text 文件保存在 {train_folder}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="处理ASR数据增强,生成新的wav.scp, text, data.list文件")
    parser.add_argument('input_dir', help='输入文件目录,包含wav.scp, text, data.list文件')
    parser.add_argument('output_dir', help='输出目录，保存增强后的文件')
    parser.add_argument('--augment_types', nargs='+', default=['noise', 'fast', 'slow'], help='选择要进行的数据增强类型')
    parser.add_argument('--num_processes', type=int, default=4, help='并行处理的进程数量,默认为4')

    args = parser.parse_args()

    augment_data(args.input_dir, args.output_dir, args.augment_types, args.num_processes)
