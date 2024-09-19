#!/bin/bash
# Author: zyw
# Date: 2024-09-12
# Description: 

average_checkpoint=true
average_num=5
out_dir=/data1/zengyongwang/model/asr_model_v4.6.0-hefei-0912

if [ ${average_checkpoint} == true ]; then
    decode_checkpoint=$out_dir/avg_${average_num}.pt
    echo "do model average and final checkpoint is $decode_checkpoint"
    python wenet/bin/average_model.py \
        --dst_model $decode_checkpoint \
        --src_path $out_dir \
        --num ${average_num} \
        --val_best
fi
