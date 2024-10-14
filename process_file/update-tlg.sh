#!/bin/bash

source_dir="/data1/zengyongwang/model/asr_model_v4.7.0/data"
target_dir="/data1/zengyongwang/model/asr_model_v4.7.0-hefei-20241011"


replaced_files=()


find "$source_dir" -type f | while read -r source_file; do

    file_name=$(basename "$source_file")    

    find "$target_dir" -type f -name "$file_name" | while read -r target_file; do
        echo "Checking: $source_file -> $target_file"  
        
        if cp -f "$source_file" "$target_file"; then
            echo "替换成功: $source_file -> $target_file"
            replaced_files+=("$target_file")
        else
            echo "替换失败: $source_file -> $target_file"
        fi
    done
done


