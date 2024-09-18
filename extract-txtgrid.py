# Author: zyw
# Date: 2024-09-11
# Description: 提取TextGrid文件中的文本内容，并保存到指定文件中

import os
import re
import argparse

parser = argparse.ArgumentParser(description='Extract text from TextGrid files')
parser.add_argument('file_path', type=str, help='Path to the TextGrid floder')
parser.add_argument('out_dir', type=str, help='Path to the output directory')

args = parser.parse_args()

file_path = args.file_path
out_dir = args.out_dir

out_file_path = os.path.join(out_dir, "text")

def extract_textgrid_content(content):
    text_lines = []

    start = content.find('name = "内容层"')
    if start == -1:
        return ""
    
    end = content.find('item [2]:', start)
    content = content[start:end]

    intervals = re.findall(r'text = "(.*?)"', content)
    for text in intervals:
        if text.strip():  # 跳过空白文本
            text = re.sub(r'[，。？！,.!?]', '', text)           
            text_lines.append(text)
    
    return ''.join(text_lines)

tg_files = []
for root, dirs, files in os.walk(file_path):
    for file in files:
        if file.endswith(".TextGrid"):
            tg_files.append(os.path.join(root, file))

with open(out_file_path, 'w', encoding='utf-8') as f:
    for tg_file in tg_files:
        with open(tg_file, 'r', encoding='utf-8') as tg:
            content = tg.read()
            extracted_content = extract_textgrid_content(content)
            file_name = os.path.basename(tg_file).replace(".TextGrid", " ")
            f.write(file_name + "" + extracted_content + '\n')
