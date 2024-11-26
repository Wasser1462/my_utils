# Author: zyw
# Date: 2024-10-09 15:54:10
# Description: Check if the audio file meets the input requirements for WENET.

import argparse
import logging
import os
import re

def calculate_duration_from_key(utterance_id):
    time_match = re.search(r"-(\d+)-(\d+)(?:-[A-Za-z0-9]*)?$", utterance_id)
    if time_match:
        start_time_ms = time_match.group(1)
        end_time_ms = time_match.group(2)
        try:
            start_time = int(start_time_ms) * 0.001  # 转换为秒
            end_time = int(end_time_ms) * 0.001  # 转换为秒
            duration = end_time - start_time
            return duration if duration > 0 else None  
        except ValueError:
            logging.warning(f"时间解析错误: {utterance_id}")
            return None
    else:
        logging.warning(f"无法解析时间信息: {utterance_id}")
        return None

def check_wav_scp(wav_scp, min_length, max_length):
    with open(wav_scp, 'r', encoding="utf-8") as f:
        texts = f.readlines()

    total_time = 0
    invalid_wav = []

    for text in texts:
        text_list = text.strip().split(maxsplit=1) 
        if len(text_list) != 2:
            logging.warning(f"格式不正确: {text}")
            continue

        utterance_id = text_list[0]
        wav_path = text_list[1]
        duration = calculate_duration_from_key(utterance_id)
        
        if duration is None:
            continue 

        total_time += duration

        if duration < min_length or duration > max_length:
            invalid_wav.append((utterance_id, duration))

    logging.info(f"统计结果: {len(texts)}条, 总时长: {total_time:.3f}s / {total_time / 3600:.3f}h.")
    if invalid_wav:
        logging.warning(f"不符合音频时长要求的记录: {len(invalid_wav)}条")
        for wav_id, length in invalid_wav:
            logging.warning(f"音频 {wav_id} 长度为 {length:.3f}s，不在范围 [{min_length}, {max_length}] 秒内.")
    return len(invalid_wav) == 0

def check_text_file(text_file, token_min_length, token_max_length):
    with open(text_file, 'r', encoding="utf-8") as f:
        texts = f.readlines()

    invalid_texts = []    
    format_errors = []    
    total_texts = len(texts)  

    for idx, text in enumerate(texts, start=1):  
        text_list = text.strip().split(maxsplit=1)  
        
        if len(text_list) != 2:
            #logging.warning(f"格式不正确: 第 {idx} 行 - {text.strip()}")
            format_errors.append((idx, text.strip()))
            continue

        utterance_id = text_list[0]
        transcript = text_list[1].split()  
        token_length = len(transcript)  

        if token_length < token_min_length or token_length > token_max_length:
            invalid_texts.append((utterance_id, token_length))

    if format_errors:
        #logging.warning(f"格式不符合要求的记录: {len(format_errors)} 条")
        for line_number, text in format_errors:
            logging.warning(f"第 {line_number} 行 - 内容: {text}")

    if invalid_texts:
        #logging.warning(f"文本长度不符合要求的记录: {len(invalid_texts)} 条")
        for text_id, length in invalid_texts:
            logging.warning(f"文本 {text_id} 长度为 {length}，不在范围 [{token_min_length}, {token_max_length}] 字符内.")

    logging.info(f"总共处理文本条目: {total_texts}")
    logging.info(f"格式不正确的文本条目: {len(format_errors)}")
    logging.info(f"文本长度不符合要求的条目: {len(invalid_texts)}")

    return len(format_errors) == 0 and len(invalid_texts) == 0
def main(input_dir, min_length, max_length, token_min_length, token_max_length):
    logging.basicConfig(level=logging.INFO)

    wav_scp_file = os.path.join(input_dir, 'wav.scp')
    text_file = os.path.join(input_dir, 'text')

    if not os.path.exists(wav_scp_file):
        logging.error(f"未找到 {wav_scp_file} 文件，请确认路径是否正确。")
        return
    if not os.path.exists(text_file):
        logging.error(f"未找到 {text_file} 文件，请确认路径是否正确。")
        return

    valid_wav = check_wav_scp(wav_scp_file, min_length, max_length)

    valid_text = check_text_file(text_file, token_min_length, token_max_length)

    if valid_wav and valid_text:
        logging.info("所有数据都符合要求！")
    else:
        logging.warning("部分数据不符合要求，请检查。")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='检查文件夹中的 wav.scp 和 text 文件是否符合要求')
    parser.add_argument('input_dir', type=str, help='包含 wav.scp 和 text 文件的文件夹路径')
    parser.add_argument('min_length', type=float, default=0.1, nargs='?', help='音频最小长度（秒）')
    parser.add_argument('max_length', type=float, default=102.4, nargs='?', help='音频最大长度（秒）')
    parser.add_argument('token_min_length', type=int, default=1, nargs='?', help='文本最小长度（字符）')
    parser.add_argument('token_max_length', type=int, default=200, nargs='?', help='文本最大长度（字符）')

    args = parser.parse_args()

    main(args.input_dir, args.min_length, args.max_length, args.token_min_length, args.token_max_length)
