# Author: zyw
# Date: 2025-01-07
# Description: Copy WAV files listed in wav.scp and resample them to 16kHz.
# usage: python /data1/zengyongwang/my_utils/process_audio/extract_wav.py /data1/zengyongwang/dataset/cantonese/test_magicdatacantonese /data1/zengyongwang/dataset/cantonese/test_magicdatacantonese --resample

import os
import shutil
import argparse
import time
import logging
from pathlib import Path
from resample_wav import process_directory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def copy_text(input_folder, output_folder):
    text_path = os.path.join(input_folder, 'text')
    shutil.copy(text_path, output_folder)

def read_wav_scp(input_folder):
    wav_scp_path = os.path.join(input_folder, 'wav.scp')
    wav_files = []
    with open(wav_scp_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) > 1:
                wav_files.append(parts[1])
    return wav_files

def copy_files(wav_files, destination):
    if not os.path.exists(destination):
        os.makedirs(destination)

    for wav_file in wav_files:
        if os.path.exists(wav_file):
            shutil.copy(wav_file, destination)
            logging.info(f"Copied: {wav_file} -> {destination}")
        else:
            logging.info(f"File not found: {wav_file}")

if __name__ == "__main__":
    begin = time.time()
    parser = argparse.ArgumentParser(description="Copy WAV files listed in wav.scp to a specified folder.")
    parser.add_argument("input_folder", type=str, help="Path to include wav.scp file.")
    parser.add_argument("output_folder", type=str, help="Destination folder where WAV files will be copied.")
    parser.add_argument("--resample", action="store_true", help="Control resampling")
    args = parser.parse_args()

    input_folder = Path(args.input_folder)
    output_folder = Path(args.output_folder)
    
    if not output_folder.is_dir():
        raise NotADirectoryError(f"Output folder {output_folder} is not a valid directory.")
    
    wav_files = read_wav_scp(input_folder)
    #copy_text(input_folder, output_folder)

    wav_dir = output_folder / "wav"
    copy_files(wav_files, wav_dir)

    logging.info("Copying completed.")
    
    if args.resample:
        logging.info("Resampling now!")
        process_directory(wav_dir, output_folder / "wav_16k", 16000, 'librosa', 8)
        logging.info("Resampling completed.")

    logging.info(f"Total time: {(time.time() - begin)/60:.2f} minutes")
