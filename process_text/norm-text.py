# Author: zyw
# Date: 2024-11-27
# Description: norm text.
import os
import argparse

def clean_text(text):
    cleaned_text = text.replace(" ", "")
    return cleaned_text

def process_file(wav_scp_path, text_file, output_file):
    with open(wav_scp_path, 'r', encoding='utf-8') as wav_file, open(text_file, 'r', encoding='utf-8') as text_file:
        wav_dict = {}
        for line in wav_file:
            parts = line.strip().split()
            if len(parts) == 2:
                key, wav_path = parts
                wav_dict[key] = wav_path

        with open(output_file, 'w', encoding='utf-8') as out_file:
            for line in text_file:
                parts = line.strip().split(maxsplit=1)
                if len(parts) != 2:
                    continue

                key, text = parts
                cleaned_text = clean_text(text)
                
                key = key.replace(".wav", "")
                
                if key in wav_dict:
                    out_file.write(f"{key} {cleaned_text}\n")
def main():

    parser = argparse.ArgumentParser(description="Process wav.scp and text files to generate Kaldi formatted text.")
    parser.add_argument("input_path", type=str, help="Directory containing wav.scp and text files")
    
    args = parser.parse_args()

    wav_scp_path = os.path.join(args.input_path, "wav.scp")
    text_file = os.path.join(args.input_path, "ref")
    output_file = os.path.join(args.input_path, "kaldi_text")

    if not os.path.exists(wav_scp_path) or not os.path.exists(text_file):
        print(f"Error: wav.scp or text file not found in {args.input_path}")
        return

    process_file(wav_scp_path, text_file, output_file)
    print(f"Kaldi formatted text file has been generated: {output_file}")

if __name__ == "__main__":
    main()
