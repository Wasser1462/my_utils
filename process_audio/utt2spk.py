# Author: zyw
# Date: 2025-01-02
# Description: Generate utt2spk file from audio files in a directory.
import os
import argparse

def generate_utt2spk(audio_dir, output_file):
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".wav")]
    if not audio_files:
        print("No .wav files found in the specified directory.")
        return

    with open(output_file, "w") as utt2spk_file:
        for audio_file in audio_files:
            utt_id = os.path.splitext(audio_file)[0]
            spk_id = utt_id
            utt2spk_file.write(f"{utt_id} {spk_id}\n")

    print(f"utt2spk file generated at: {output_file}")

def speaker_recognition(audio_dir, output_file):
    try:
        from pyAudioAnalysis import audioSegmentation as aS
    except ImportError:
        print("pyAudioAnalysis library not found. Please install it to use speaker recognition mode.")
        return

    audio_files = [os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.endswith(".wav")]
    if not audio_files:
        print("No .wav files found in the specified directory.")
        return

    with open(output_file, "w") as utt2spk_file:
        for audio_file in audio_files:
            segments, _ = aS.speaker_diarization(audio_file, 2)  # Assume 2 speakers for simplicity
            utt_id = os.path.splitext(os.path.basename(audio_file))[0]
            spk_id = f"speaker_{segments[0]}"  # Assign the first detected speaker
            utt2spk_file.write(f"{utt_id} {spk_id}\n")

    print(f"utt2spk file generated with speaker recognition at: {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_dir", help="Path to the directory containing audio files.")
    parser.add_argument("output_file", help="Path to the output utt2spk file.")
    parser.add_argument("--mode", choices=["1", "2"], default="1", help="Mode: 1 for direct mapping, 2 for speaker recognition.")
    args = parser.parse_args()

    if args.mode == "1":
        generate_utt2spk(args.audio_dir, args.output_file)
    elif args.mode == "2":
        speaker_recognition(args.audio_dir, args.output_file)

if __name__ == "__main__":
    main()
