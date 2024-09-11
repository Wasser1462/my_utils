# Author: zyw
# Date: 2024-09-11
# Description: Convert all mp3 files in a folder to wav format using ffmpeg

import os
import subprocess

input_folder = "/data1/zengyongwang/dataset/zhinengkefu/mp3"
output_folder = "/data1/zengyongwang/dataset/zhinengkefu/wav"

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