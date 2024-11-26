# Author: zyw
# Date: 2024-09-11
# Description: 利用ffmpg进行双声道分离
import os
import subprocess
from argparse import ArgumentParser

parser = ArgumentParser(description="利用ffmpg进行双声道分离")
parser.add_argument("input_folder", type=str, help="输入文件夹路径")
parser.add_argument("output_folder", type=str, help="输出文件夹路径")

args = parser.parse_args()

input_folder = args.input_folder
output_folder = args.output_folder

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.endswith(".wav"):
        
        input_path = os.path.join(input_folder, filename)       
        
        basename = os.path.splitext(filename)[0]     
        
        output_left = os.path.join(output_folder, f"{basename}_1.wav")
        output_right = os.path.join(output_folder, f"{basename}_2.wav")
              
        subprocess.run(['ffmpeg', '-i', input_path, '-map_channel', '0.0.0', output_left, '-map_channel', '0.0.1', output_right])
        
        print(f"Processed {filename}:")
        print(f"  Left channel saved to {output_left}")
        print(f"  Right channel saved to {output_right}")

print("Batch processing completed.")
