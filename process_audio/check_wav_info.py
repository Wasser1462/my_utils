# Author: zyw
# Date: 2024-10-28
# Description: check wav info

import os
import argparse
import wave
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_wav_info(filepath):
    try:
        with wave.open(filepath, 'r') as wav_file:
            channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            frames = wav_file.getnframes()
            duration = frames / float(sample_rate)
            return {
                'channels': channels,
                'sample_rate': sample_rate,
                'duration': duration
            }
    except wave.Error as e:
        logging.error(f"Error reading {filepath}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Check WAV files in a directory and output audio information.")
    parser.add_argument('directory', type=str, help="Path to the directory containing WAV files")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        logging.error(f"The directory '{args.directory}' does not exist.")
        return

    for root, _, files in os.walk(args.directory):
        for file in files:
            if file.lower().endswith('.wav'):
                filepath = os.path.join(root, file)
                info = get_wav_info(filepath)
                if info:
                    logging.info(f"File: {filepath}")
                    logging.info(f"  Channels: {info['channels']}")
                    logging.info(f"  Sample Rate: {info['sample_rate']} Hz")
                    logging.info(f"  Duration: {info['duration']:.2f} seconds")
                    logging.info("-----------------------------------")

if __name__ == "__main__":
    main()