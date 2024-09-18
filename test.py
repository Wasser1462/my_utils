# Author: zyw
# Date: 2024-09-12
# Description: test script
import argparse
import os
import json

def read_scp(scp_file):
    scp_data = {}
    with open(scp_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            key, path = parts
            scp_data[key] = path
    return scp_data

def read_text(text_file):
    text_data = {}
    with open(text_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(maxsplit=1)
            if len(parts) != 2:
                continue
            key, text = parts
            text_data[key] = text
    return text_data

def generate_data_list(wav_scp, text, output_file):
    data_list = []
    for key in wav_scp:
        if key in text:
            new_data_entry = {
                "key": key,
                "wav": wav_scp[key],
                "txt": text[key]
            }
            data_list.append(new_data_entry)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in data_list:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def main():
    parser = argparse.ArgumentParser(description="Generate data.list from wav.scp and text files.")
    parser.add_argument('--input_path', required=True, help='Input path containing wav.scp and text files.')
    parser.add_argument('--output_file', required=True, help='Output data.list file path.')

    args = parser.parse_args()

    wav_scp_path = os.path.join(args.input_path, 'wav.scp')
    text_path = os.path.join(args.input_path, 'text')

    if not os.path.exists(wav_scp_path) or not os.path.exists(text_path):
        print(f"Error: wav.scp or text file not found in {args.input_path}")
        return

    wav_scp = read_scp(wav_scp_path)
    text = read_text(text_path)

    generate_data_list(wav_scp, text, args.output_file)

if __name__ == '__main__':
    main()
