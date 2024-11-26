# Author: zyw
# Date: 2024-09-11
# Description: This script is used to prepare tuning data for the ASR model.

import argparse
import os
import random
import re
import logging
from pathlib import Path
import shutil  
import json

def get_wav_scp_and_text(folder_path):
    wav_scp_path = os.path.join(folder_path, 'wav.scp')
    text_path = os.path.join(folder_path, 'text')

    if not os.path.exists(wav_scp_path):
        raise FileNotFoundError(f"无法找到 {wav_scp_path} 文件")
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"无法找到 {text_path} 文件")

    return wav_scp_path, text_path

def statis_project_data_length_0(wav_scp_path):
    print(f"正在处理 {wav_scp_path} 文件的总时长计算...")
    total_duration = 0
    durations = []
    with open(wav_scp_path, 'r', encoding="utf-8") as f:
        for line in f:
            utterance_id, wav_path = line.strip().split(" ", maxsplit=1)
            time_match = re.search(r"-(\d+)-(\d+)$", utterance_id)
            if time_match:
                start_time_ms = time_match.group(1)
                end_time_ms = time_match.group(2)
                start_time = int(start_time_ms) * 0.001
                end_time = int(end_time_ms) * 0.001
                duration = end_time - start_time
                total_duration += duration
                durations.append((utterance_id, wav_path, duration))
            else:
                logging.warning(f"无法解析时间信息: {utterance_id}")
    print(f"{wav_scp_path} 总时长为: {total_duration / 3600:.3f} 小时")
    return total_duration, durations

def statis_project_data_length_1(wav_scp_path):
    print(f"正在处理 {wav_scp_path} 文件的音频片段信息...")
    durations = []
    with open(wav_scp_path, 'r', encoding="utf-8") as f:
        for line in f:
            utterance_id, wav_path = line.strip().split(" ", maxsplit=1)
            time_match = re.search(r"-(\d+)-(\d+)-[A-Za-z0-9]+$", utterance_id)
            if time_match:
                start_time_ms = time_match.group(1)
                end_time_ms = time_match.group(2)
                start_time = int(start_time_ms) * 0.001
                end_time = int(end_time_ms) * 0.001
                duration = end_time - start_time
                durations.append((utterance_id, wav_path, duration))
            else:
                logging.warning(f"无法解析时间信息: {utterance_id}")
    print(f"已完成 {wav_scp_path} 的音频片段信息提取")
    return durations

def load_text_as_dict(text_path):
    text_dict = {}
    with open(text_path, 'r', encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if len(line.split(" ", 1)) == 2:
                utterance_id, text_content = line.split(" ", 1)
                text_dict[utterance_id] = text_content
            else:
                logging.warning(f"无法解析文本行: {line}")
    print(f"已完成 {text_path} 文件的加载")
    return text_dict


def match_durations_and_generate_text(wav_scp_0, wav_scp_1, total_duration_0, tolerance_seconds=720):
    durations_1 = statis_project_data_length_1(wav_scp_1)
    
    matched_durations = []
    random.shuffle(durations_1) 

    selected_duration = 0
    target_duration = total_duration_0  

    print(f"开始匹配目标时长 {target_duration / 3600:.3f} 小时 (误差范围: {tolerance_seconds / 3600:.3f} 小时)...")

    for utterance_id, wav_path, duration in durations_1:
        if selected_duration + duration <= target_duration + tolerance_seconds:
            matched_durations.append((utterance_id, wav_path, duration))
            selected_duration += duration
        if selected_duration >= target_duration - tolerance_seconds:
            break
    
    print(f"匹配完成，总时长为: {selected_duration / 3600:.3f} 小时")
    return matched_durations, selected_duration

def merge_and_shuffle(original_wav_scp, original_text, new_durations, text_dict, output_dir):
    combined_wav_scp = []
    combined_text = []

    with open(original_wav_scp, 'r', encoding="utf-8") as f:
        combined_wav_scp.extend(f.readlines())

    with open(original_text, 'r', encoding="utf-8") as f:
        combined_text.extend(f.readlines())

    for utterance_id, wav_path, _ in new_durations:
        combined_wav_scp.append(f"{utterance_id} {wav_path}\n")
        if utterance_id in text_dict:
            combined_text.append(f"{utterance_id} {text_dict[utterance_id]}\n")
    
    random.shuffle(combined_wav_scp)
    random.shuffle(combined_text)

    output_wav_scp = os.path.join(output_dir, "wav.scp")
    output_text = os.path.join(output_dir, "text")


    with open(output_wav_scp, 'w', encoding="utf-8") as f:
        f.writelines(combined_wav_scp)
    
    with open(output_text, 'w', encoding="utf-8") as f:
        f.writelines(combined_text)

def copy_dev_folder(source_dir, output_dir):
    dev_folder_path = os.path.join(source_dir, "dev")
    dest_path = os.path.join(output_dir, "dev")

    if os.path.exists(dev_folder_path):
        shutil.copytree(dev_folder_path, dest_path)
    else:
        print(f"源文件夹 {dev_folder_path} 不存在")

def generate_data_list(wav_scp, text, output_dir):
    text_dict = load_text_as_dict(text)
    data_list_path = os.path.join(output_dir, "data.list")

    with open(wav_scp, 'r', encoding="utf-8") as wav_file, open(data_list_path, 'w', encoding="utf-8") as data_list:
        missing_count = 0  
        total_count = 0  
        for line in wav_file:
            utterance_id, wav_path = line.strip().split(" ", 1)
            total_count += 1
            if utterance_id in text_dict:
                entry = {
                    "key": utterance_id,
                    "wav": wav_path,
                    "txt": text_dict[utterance_id]
                }
                data_list.write(json.dumps(entry, ensure_ascii=False) + "\n")
            else:
                missing_count += 1
                logging.warning(f"未找到匹配的文本: {utterance_id}")
        
        print(f"总条目数: {total_count}, 未匹配条目数: {missing_count}")
        print(f"已生成 {data_list_path} 文件")


def generate_new_wav_scp_and_text(wav_folder_0, wav_folder_1, output_dir, tolerance_seconds=100):
    wav_scp_0, text_0 = get_wav_scp_and_text(wav_folder_0)
    wav_scp_1, text_1 = get_wav_scp_and_text(wav_folder_1)
    
    total_duration_0, _ = statis_project_data_length_0(wav_scp_0)
    matched_durations, selected_duration = match_durations_and_generate_text(wav_scp_0, wav_scp_1, total_duration_0, tolerance_seconds)
  
    text_dict = load_text_as_dict(text_1)

    train_folder = os.path.join(output_dir, "train")
    os.makedirs(train_folder, exist_ok=True)

    merge_and_shuffle(wav_scp_0, text_0, matched_durations, text_dict, train_folder)
    generate_data_list(os.path.join(train_folder, "wav.scp"), os.path.join(train_folder, "text"), train_folder)

    copy_dev_folder("/data2/cuidc/data/data_20231123", output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数据回流,生成最终的训练数据")
    
    parser.add_argument("wav_folder_0", type=Path, help="新的需要微调的数据路径")
    parser.add_argument("wav_folder_1", type=Path, help="数据库回流数据路径")
    parser.add_argument("output_dir", type=Path, help="输出文件夹路径, train/wav.scp 和 train/text 将保存到此文件夹")
    parser.add_argument("--tolerance_seconds", type=int, default=100, help="匹配时长的容差秒数 (默认: 100 秒)")
    
    args = parser.parse_args()

    generate_new_wav_scp_and_text(
        args.wav_folder_0, 
        args.wav_folder_1, 
        args.output_dir, 
        args.tolerance_seconds
    )
