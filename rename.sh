#!/bin/bash
cd /data1/zengyongwang/oupai/wav2  
counter=1  # 设置起始编号

for file in *.wav; do
  mv "$file" "audio${counter}.wav"  # 重命名文件
  ((counter++)) 
done
