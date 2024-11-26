import os
import re
import string
import argparse

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

def main():
    parser = argparse.ArgumentParser(description='对比不同模型的识别结果，并输出比较结果。')
    parser.add_argument('input_path', help='包含多个模型子文件夹的输入目录')
    parser.add_argument('output_dir', help='输出目录')
    args = parser.parse_args()

    input_path = args.input_path
    out_dir = args.output_dir if args.output_dir else input_path
    out_file_path = os.path.join(out_dir, "compare.txt")

    # 获取子文件夹列表，每个子文件夹代表一个模型的结果
    subfolders = [f for f in os.scandir(input_path) if f.is_dir()]

    if not subfolders:
        print("输入路径中没有找到任何子文件夹。")
        return

    file_contents = {}

    # 遍历每个子文件夹，收集相同文件名的 TextGrid 文件内容
    for subfolder in subfolders:
        model_name = os.path.basename(subfolder.path)  # 使用子文件夹名字作为模型名
        for root, dirs, files in os.walk(subfolder.path):
            for file in files:
                if file.endswith(".TextGrid"):
                    file_name = os.path.basename(file).replace(".TextGrid", "")
                    file_full_path = os.path.join(root, file)

                    with open(file_full_path, 'r', encoding='utf-8') as tg:
                        content = tg.read()
                        extracted_content = extract_textgrid_content(content)
                        
                        if file_name not in file_contents:
                            file_contents[file_name] = []
                        file_contents[file_name].append((model_name, extracted_content))  # 使用模型名替换编号

    # 写入结果到输出文件
    with open(out_file_path, 'w', encoding='utf-8') as f:
        for file_name, contents in file_contents.items():
            f.write(f"文件名: {file_name}\n")
            
            if len(contents) == len(subfolders):
                # 按模型名顺序输出
                contents.sort(key=lambda x: x[0])
                for model_name, content in contents:
                    f.write(f" {model_name}: {content}\n")
            else:
                for model_name, content in contents:
                    f.write(f" {model_name}: {content}\n")
            
            f.write('\n')

if __name__ == "__main__":
    main()
