# Author: zyw
# Date: 2024-11-28
# Description: Generate wav.scp file from wav folder and text file.
import os
import argparse

def generate_wav_scp(input_path):
    wav_folder = os.path.join(input_path, 'wav')
    text_file = os.path.join(input_path, 'text')
    
    if not os.path.exists(wav_folder) or not os.path.isdir(wav_folder):
        raise FileNotFoundError(f"The specified wav folder {wav_folder} does not exist.")
    
    if not os.path.exists(text_file):
        raise FileNotFoundError(f"The specified text file {text_file} does not exist.")
    
    with open(text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    wav_scp_lines = []
    missing_files = []
    
    for line in lines:
        parts = line.strip().split(' ', 1)
        if len(parts) == 2:
            utt_id, _ = parts
            wav_path = os.path.join(wav_folder, utt_id + '.wav')
            if os.path.exists(wav_path):
                wav_scp_lines.append(f"{utt_id} {wav_path}")
            else:
                missing_files.append(utt_id)
    
    if missing_files:
        print(f"Warning: The following files were listed in the text file but could not be found in the wav folder:")
        for utt_id in missing_files:
            print(f"  - {utt_id}")
    
    wav_scp_path = os.path.join(input_path, 'wav.scp')
    with open(wav_scp_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(wav_scp_lines))
    
    print(f"wav.scp has been written to {wav_scp_path}")
    print(f"Total entries processed: {len(lines)}")
    print(f"Total entries successfully matched: {len(wav_scp_lines)}")
    print(f"Total missing files: {len(missing_files)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate wav.scp file from wav folder and text file.")
    parser.add_argument('input_path', type=str, help="Path to the folder containing the wav folder and text file.")
    
    args = parser.parse_args()
    generate_wav_scp(args.input_path)
