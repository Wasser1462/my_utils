# Author: zyw
# Date: 2024-12-17
# Description: resample audio file to target sample rate
import os
import argparse
import torch
import torchaudio
from torchaudio.transforms import Resample
import librosa
import soundfile as sf
from time import time
from concurrent.futures import ThreadPoolExecutor


def resample_by_cpu(file_path, target_sample, output_folder):
    base_name = os.path.basename(file_path).split('.')[0]
    start_time = time()
    y, sr = torchaudio.load(file_path)
    resampler = Resample(orig_freq=sr, new_freq=target_sample)
    resample_music = resampler(y)
    output_path = os.path.join(output_folder, f'{base_name}.wav')
    torchaudio.save(output_path, resample_music, target_sample)
    print(f"Processed {file_path} to {output_path}, cost: {time() - start_time:.2f}s")


def resample_use_cuda(file_path, target_sample, output_folder):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    base_name = os.path.basename(file_path).split('.')[0]
    start_time = time()
    y, sr = torchaudio.load(file_path)
    y = y.to(device)
    resampler = Resample(orig_freq=sr, new_freq=target_sample).to(device)
    resample_music = resampler(y)
    output_path = os.path.join(output_folder, f'{base_name}.wav')
    torchaudio.save(output_path, resample_music.to('cpu'), target_sample)
    print(f"Processed {file_path} to {output_path}, cost: {time() - start_time:.2f}s")


def resample_by_librosa(file_path, target_sample, output_folder):
    start_time = time()
    y, sr = librosa.load(file_path)
    base_name = os.path.basename(file_path).split('.')[0]
    y_resampled = librosa.resample(y=y, orig_sr=sr, target_sr=target_sample)
    output_path = os.path.join(output_folder, f'{base_name}.wav')
    sf.write(output_path, data=y_resampled, samplerate=target_sample)
    print(f"Processed {file_path} to {output_path}, cost: {time() - start_time:.2f}s")


def process_file(file_path, output_folder, target_sample, mode):
    if mode == 'cpu':
        resample_by_cpu(file_path, target_sample, output_folder)
    elif mode == 'cuda':
        resample_use_cuda(file_path, target_sample, output_folder)
    elif mode == 'librosa':
        resample_by_librosa(file_path, target_sample, output_folder)
    else:
        print(f"Unknown mode '{mode}' for file {file_path}. Skipping...")


def process_directory(input_folder, output_folder, target_sample, mode, num_workers):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = [os.path.join(input_folder, file_name) for file_name in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, file_name)) and file_name.endswith(".wav")]

    with ThreadPoolExecutor(num_workers) as executor:
        for file_path in files:
            executor.submit(process_file, file_path, output_folder, target_sample, mode)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Resample WAV files in a directory to a target sample rate.")
    parser.add_argument('input_folder', type=str, help="Input folder containing WAV files")
    parser.add_argument('output_folder', type=str, help="Output folder to save the resampled WAV files")
    parser.add_argument('--target_sample', type=int, default=16000, help="Target sample rate (default: 16000)")
    parser.add_argument('--mode', type=str, choices=['cpu', 'cuda', 'librosa'], default='librosa', help="Resampling mode (default: 'librosa')")
    parser.add_argument('--num_workers', type=int, default=8, help="Number of workers for parallel processing (default: 8)")
    args = parser.parse_args()

    process_directory(args.input_folder, args.output_folder, args.target_sample, args.mode, args.num_workers)
    print("All files done!")
