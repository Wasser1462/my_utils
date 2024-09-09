#!/bin/bash

# 定义源文件夹和目标文件夹
source_dir="/data1/zengyongwang/oupai/wav2"
target_dir1="/data1/zengyongwang/oupai/wav2/part1"
target_dir2="/data1/zengyongwang/oupai/wav2/part2"

# 创建目标文件夹
mkdir -p "$target_dir1"
mkdir -p "$target_dir2"

# 计数器
count=0

# 按文件名顺序遍历源文件夹中的文件
for i in $(seq 1 2823); do
  file="$source_dir/audio$i.wav"
  if [ -f "$file" ]; then
    count=$((count + 1))
    if [ $count -le 2169 ]; then
      cp "$file" "$target_dir1/"
    else
      cp "$file" "$target_dir2/"
    fi
  fi
done

echo "文件已成功复制并且分割。"
