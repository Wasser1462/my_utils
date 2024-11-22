# Author: zyw
# Date: 2024-09-11
# Description: Convert all mp3 files in a folder and its subfolders to wav format using ffmpeg with multiprocessing

import os
import subprocess
import argparse
from concurrent.futures import ProcessPoolExecutor

def repair_or_reencode(mp3_path, fixed_mp3_path):
    """
    Repair or re-encode the MP3 file to make it compatible with ffmpeg.
    """
    try:
        # Try repairing the MP3 file
        repair_command = ['ffmpeg', '-i', mp3_path, '-acodec', 'copy', fixed_mp3_path]
        subprocess.run(repair_command, check=True)
        print(f"Repaired: {mp3_path} -> {fixed_mp3_path}")
        return fixed_mp3_path
    except subprocess.CalledProcessError:
        # If repair fails, re-encode the MP3 file
        reencode_command = ['ffmpeg', '-i', mp3_path, '-ac', '2', '-ar', '16000', fixed_mp3_path]
        subprocess.run(reencode_command, check=True)
        print(f"Re-encoded: {mp3_path} -> {fixed_mp3_path}")
        return fixed_mp3_path

def convert_to_wav(mp3_path, output_folder):
    """
    Convert an MP3 file to WAV format.
    """
    wav_filename = os.path.basename(mp3_path).replace(".mp3", ".wav")
    wav_path = os.path.join(output_folder, wav_filename)
    
    try:
        # Attempt to convert MP3 to WAV
        command = ['ffmpeg', '-i', mp3_path, '-ar', '16000', '-ac', '2', wav_path]
        subprocess.run(command, check=True)
        print(f"Converted: {mp3_path} -> {wav_path}")
    except subprocess.CalledProcessError:
        # Handle conversion errors
        print(f"Error converting {mp3_path}, attempting to repair or re-encode.")
        fixed_mp3_path = mp3_path.replace(".mp3", "_fixed.mp3")
        fixed_mp3_path = os.path.join(output_folder, os.path.basename(fixed_mp3_path))
        repaired_mp3 = repair_or_reencode(mp3_path, fixed_mp3_path)
        
        # Retry conversion with the repaired or re-encoded file
        retry_command = ['ffmpeg', '-i', repaired_mp3, '-ar', '16000', '-ac', '2', wav_path]
        subprocess.run(retry_command, check=True)
        print(f"Converted after repair/re-encode: {repaired_mp3} -> {wav_path}")

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
