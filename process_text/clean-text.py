# Author: zyw
# Date: 2024-11-25
# Description: clean text file by removing lines with empty or single-character content

import argparse

def clean_text_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            parts = line.strip().split(maxsplit=1)
            if len(parts) < 2 or len(parts[1]) <= 1:
                continue
            outfile.write(line)

def main():

    parser = argparse.ArgumentParser(description='Clean text file by removing lines with empty or single-character content.')
    parser.add_argument('input_file', type=str, help='Path to the input text file')
    parser.add_argument('output_file', type=str, help='Path to save the cleaned text file')
    args = parser.parse_args() 
    clean_text_file(args.input_file, args.output_file)

if __name__ == '__main__':
    main()
