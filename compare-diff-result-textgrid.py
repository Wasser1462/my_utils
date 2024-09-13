# Author: zyw
# Date: 2024-09-12
# Description: 
import os
import re
import string

file_paths = [
    "/data1/zengyongwang/tmp/hefei-result/hefei12345-3-markupfiles-2h",   
    "/data1/zengyongwang/tmp/hefei-result/hefei12345-3-transcribefiles",
    "/data1/zengyongwang/tmp/hefei-result/hefei12345-3-model-tuning-20240908"
]

out_dir = "/data1/zengyongwang/tmp/hefei-result"
out_file_path = os.path.join(out_dir, "compare.txt")

def extract_textgrid_content(content):
    text_lines = []
    start = content.find('name = "内容层"')
    if start == -1:
        return ""
    
    end = content.find('item [2]:', start)
    content = content[start:end]

    intervals = re.findall(r'text = "(.*?)"', content)
    for text in intervals:
        if text.strip():
            # 删除标点符号
            cleaned_text = text.translate(str.maketrans('', '', string.punctuation))
            text_lines.append(cleaned_text)
    
    return ''.join(text_lines)

file_contents = {}

# 遍历每个文件夹，收集相同文件名的TextGrid文件内容
for file_path in file_paths:
    for root, dirs, files in os.walk(file_path):
        for file in files:
            if file.endswith(".TextGrid"):
                file_name = os.path.basename(file).replace(".TextGrid", "")
                file_path = os.path.join(root, file)

                with open(file_path, 'r', encoding='utf-8') as tg:
                    content = tg.read()
                    extracted_content = extract_textgrid_content(content)
                    
                    if file_name not in file_contents:
                        file_contents[file_name] = []
                    file_contents[file_name].append(extracted_content)


with open(out_file_path, 'w', encoding='utf-8') as f:
    for file_name, contents in file_contents.items():
        f.write(f"文件名: {file_name}\n")
        
        if len(contents) == 3:
            f.write(f"  标注文本: {contents[0]}\n")
            f.write(f"v4.6.0模型: {contents[1]}\n")
            f.write(f" 调优后模型: {contents[2]}\n")
        else:
            for idx, content in enumerate(contents):
                f.write(f"部分 {idx + 1}: {content}\n")
        
        f.write('\n')
