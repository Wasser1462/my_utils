#!/bin/bash

source_dir="/data1/zengyongwang/oupai/vad-result/vad_segments"
target_dir="/data1/zengyongwang/oupai/wav-test-train/train/wav"

count=0

for file in "$source_dir"/*; do
    filename=$(basename "$file")
    
    if [ -f "$target_dir/$filename" ]; then
        cp "$file" "$target_dir/$filename"
        echo "Replaced: $filename"
        ((count++))
    fi
done

echo "替换成功，共替换了 $count 个文件。"
