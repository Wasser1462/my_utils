# Author: zyw
# Date: 2025-01-07
# Description:

import opencc
import argparse

def convert_file(input_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            content = infile.read()
        simplified_content = opencc.OpenCC('t2s').convert(content)
        with open(input_file, 'w', encoding='utf-8') as outfile:
            outfile.write(simplified_content)
        print(f"File successfully converted and saved to {input_file}")
    except Exception as e:
        print(f"Error processing file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Convert traditional Chinese text to simplified Chinese.')
    parser.add_argument('input_file', help='Path to the input file')
    args = parser.parse_args()

    convert_file(args.input_file)

if __name__ == '__main__':
    main()
