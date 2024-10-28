import logging
import argparse
import os
import json

logging.basicConfig(level=logging.INFO)

def read_text(text_file, keys_set):
    text_data = {}
    with open(text_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) != 2:
                continue
            key, text = parts
            if key in keys_set:
                text_data[key] = text
    return text_data

def generate_data_list(wav_scp_path, text_dict, output_file, time_limit_hours=None):
    total_time = 0
    time_limit_seconds = time_limit_hours * 3600 if time_limit_hours else None
    entries_written = 0

    with open(wav_scp_path, 'r', encoding='utf-8') as wav_file, \
         open(output_file, 'w', encoding='utf-8') as out_file:
        for line in wav_file:
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            key, wav_path = parts
            if key in text_dict:
                id_sequence = key.strip().split('-')
                if len(id_sequence) < 3:
                    continue  # 无法计算时长
                try:
                    time = (int(id_sequence[-2]) - int(id_sequence[-3])) / 1000
                except ValueError:
                    continue  # 转换失败
                total_time += time
                new_data_entry = {
                    "key": key,
                    "wav": wav_path,
                    "txt": text_dict[key]
                }
                out_file.write(json.dumps(new_data_entry, ensure_ascii=False) + '\n')
                entries_written += 1
                if time_limit_seconds and total_time >= time_limit_seconds:
                    break

    logging.info(f"生成结果: {entries_written} 条, 总时长: {total_time:.3f}s / {total_time / 3600:.3f}h.")

def main():
    parser = argparse.ArgumentParser(description="根据wav.scp文件生成音频时长符合要求的data.list.")
    parser.add_argument('input_path', help='包含wav.scp和text文件的输入路径.')
    parser.add_argument('--hours', type=float, default=None, help='生成音频时长限制 (单位: 小时). 默认为生成所有音频.')

    args = parser.parse_args()

    wav_scp_path = os.path.join(args.input_path, 'wav.scp')
    text_path = os.path.join(args.input_path, 'text')
    output_file = os.path.join(args.input_path, 'data.list')

    if not os.path.exists(wav_scp_path) or not os.path.exists(text_path):
        print(f"Error: wav.scp 或 text 文件在 {args.input_path} 中未找到")
        return

    # 首先获取所有需要的 key
    keys_set = set()
    with open(wav_scp_path, 'r', encoding='utf-8') as wav_file:
        for line in wav_file:
            parts = line.strip().split()
            if len(parts) == 2:
                keys_set.add(parts[0])

    logging.info("开始读取 text 文件...")
    text_dict = read_text(text_path, keys_set)
    logging.info("完成读取 text 文件")

    logging.info("开始生成 data.list 文件...")
    generate_data_list(wav_scp_path, text_dict, output_file, args.hours)
    logging.info("完成生成 data.list 文件")

if __name__ == '__main__':
    main()