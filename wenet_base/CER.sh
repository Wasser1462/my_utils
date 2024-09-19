#!/bin/bash
# 作者: zyw
# 日期: 2024-09-13
# 描述: 计算输出模型CER

. ./path.sh || exit 1;

export CUDA_VISIBLE_DEVICES=""

data_dir=$1
model_dir=$2
out_dir=$3

dict=$model_dir/lang_char.txt
train_config=$out_dir/train.yaml
pretrained_checkpoint=$out_dir/init.pt

dir=$out_dir
decode_modes=("ctc_greedy_search" "ctc_prefix_beam_search" "attention" )

ctc_weight=0.3
reverse_weight=0.5
batch_size=16
num_workers=8
average_checkpoint=true
average_num=5 
decode_checkpoint=$dir/avg_${average_num}.pt

if [ ! -f $dict ]; then
  echo "词典文件 $dict 不存在，请检查路径。"
  exit 1
fi

if [ ! -f $train_config ]; then
  echo "训练配置文件 $train_config 不存在，请检查路径。"
  exit 1
fi

if [ ! -f $decode_checkpoint ]; then
  echo "解码检查点文件 $decode_checkpoint 不存在，请检查路径。"
  exit 1
fi

echo "开始解码并计算 CER..."
for mode in "${decode_modes[@]}"; do
  echo "正在使用解码模式: $mode"
  result_dir=$dir/$mode
  mkdir -p $result_dir

  batch_size=1

  python wenet/bin/recognize.py \
    --gpu 0 \
    --mode $mode \
    --config $train_config \
    --data_type raw \
    --test_data $data_dir/test/data.list \
    --checkpoint $decode_checkpoint \
    --beam_size 10 \
    --batch_size $batch_size \
    --dict $dict \
    --result_file $result_dir/text \
    --ctc_weight $ctc_weight \
    --reverse_weight $reverse_weight

  if [ ! -f $result_dir/text ]; then
    echo "解码结果文件 $result_dir/text 未生成，解码失败。"
    continue
  fi

  python tools/compute-wer.py --char=1 --v=1 \
    $data_dir/test/text $result_dir/text > $result_dir/wer
  echo "解码模式 $mode 的 CER 结果已保存到 $result_dir/wer"
done
