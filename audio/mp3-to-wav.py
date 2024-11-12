# Author: zyw
# Date: 2024-09-11
# Description: Convert all mp3 files in a folder and its subfolders to wav format using ffmpeg with multiprocessing

import os
import subprocess
import argparse
from concurrent.futures import ProcessPoolExecutor

def convert_to_wav(mp3_path, output_folder):
    wav_filename = os.path.basename(mp3_path).replace(".mp3", ".wav")
    wav_path = os.path.join(output_folder, wav_filename)
    
    command = ['ffmpeg', '-i', mp3_path, wav_path]
    subprocess.run(command, check=True)
    
    print(f"Converted: {mp3_path} to {wav_path}")

def main():
    parser = argparse.ArgumentParser(description='Convert MP3 files to WAV format')
    parser.add_argument('input_dir', help='input directory')
    parser.add_argument('output_dir', help='output directory')
    
    args = parser.parse_args()
    
    input_folder = args.input_dir
    output_folder = args.output_dir
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    mp3_files = []
    for root, _, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith(".mp3"):
                mp3_path = os.path.join(root, filename)
                mp3_files.append(mp3_path)
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        for mp3_path in mp3_files:
            executor.submit(convert_to_wav, mp3_path, output_folder)
    
    print("All MP3 files have been converted to WAV format.")

if __name__ == "__main__":
    main()
