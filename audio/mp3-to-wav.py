# Author: zyw
# Date: 2024-09-11
# Description: Convert all mp3 files in a folder to wav format using ffmpeg

import os
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Convert MP3 files to WAV format')
parser.add_argument('input_dir', help='input dir')
parser.add_argument('output_dir', help='output dir')

args = parser.parse_args()

input_folder = args.input_dir
output_folder = args.output_dir

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for filename in os.listdir(input_folder):
    if filename.endswith(".mp3"):
        mp3_path = os.path.join(input_folder, filename)
        wav_filename = filename.replace(".mp3", ".wav")
        wav_path = os.path.join(output_folder, wav_filename)
        
        # Use ffmpeg to convert mp3 to wav
        command = ['ffmpeg', '-i', mp3_path, wav_path]
        subprocess.run(command)

        print(f"Converted: {mp3_path} to {wav_path}")

print("All MP3 files have been converted to WAV format.")
