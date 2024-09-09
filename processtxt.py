import os
import re

file_path = "/data1/zengyongwang/tmp/hefei12345-wav-and-textgrid/textgrid/12315-jiaotong-shijian-3"
out_dir = "/data1/zengyongwang/tmp/hefei123-wav-train-test/train"
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
