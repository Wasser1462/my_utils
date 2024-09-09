#!/bin/bash
# Created by fangcheng on 2022/12/07
# 导出gpu推理需要的模型文件

. ./path.sh || exit 1

stage=0
stop_stage=4

conf_path=""
beam_size=10
num_decoding_left_chunks=5
online_chunk_size=16
offline_chunk_size=-1

average_num=5

. tools/parse_options.sh || exit 1

if [ $# != 4 ]; then
  echo "Usage: $0 [options] <in_dir> <model_dir> <model_4x> <out_dir>"
  echo "in_dir: 训练完成的模型文件夹路径,需要包含train.yaml以及pytorch模型文件路径."
  echo "model_dir: 发版模型文件夹路径, 需包含conf/asr.yaml文件、model_repo以及model_repo_stateful."
  echo "model_4x: 导出的CPU模型文件夹路径, 需包含conf, graph, lang_char.txt, libtorch_model,onnx_model, post_processing,self_learning"
  echo "out_dir: 导出的模型推理文件夹路径, 须与待发版的模型文件夹同名, 如asr_model_v5.2.1."
  echo "--average_num: 默认5."
  echo "--conf_path: 配置文件路径,用于获取参数,一般为conf/asr.yaml,默认为空."
  exit 1
fi

in_dir=$1
model_dir=$2
model_4x=$3
out_dir=$4

# 此处的lm_path以及vocab_path为模型推理加载的相对路径, 需要基于模型给定.
lm_path=`basename $out_dir`/lm.bin
vocab_path=`basename $out_dir`/lang_char.txt

if [[ $conf_path != "" ]]; then
  num_decoding_left_chunks=`sed '/  num_left_chunks:/!d;s/.*://' $conf_path`
  beam_size=`sed '/  beam:/!d;s/.*://' $conf_path`
fi

if [ ! -d $out_dir ];then
  mkdir $out_dir
fi

if [ ${stage} -le 0 ] && [ ${stop_stage} -ge 0 ]; then
  echo "$(date) stage 0: 导出onnx model."

  # 导出流式模型
  onnx_dir=${out_dir}/onnx_model/online_model
  mkdir -p ${onnx_dir}
  python local/triton_model_repo/scripts/export_onnx_gpu.py \
    --config ${in_dir}/train.yaml \
    --cmvn_file ${in_dir}/global_cmvn \
    --checkpoint ${in_dir}/avg_${average_num}.pt \
    --decoding_chunk_size ${online_chunk_size} \
    --beam_size ${beam_size} \
    --reverse_weight 0.0 \
    --ctc_weight 0.5 \
    --output_onnx_dir ${onnx_dir} \
    --num_decoding_left_chunks ${num_decoding_left_chunks} \
    --streaming

  # 导出非流式模型
  onnx_dir=$out_dir/onnx_model/offline_model
  mkdir -p ${onnx_dir}
  python local/triton_model_repo/scripts/export_onnx_gpu.py \
    --config ${in_dir}/train.yaml \
    --cmvn_file ${in_dir}/global_cmvn \
    --checkpoint ${in_dir}/avg_${average_num}.pt \
    --decoding_chunk_size ${offline_chunk_size} \
    --reverse_weight 0.0 \
    --ctc_weight 0.5 \
    --beam_size ${beam_size} \
    --output_onnx_dir ${onnx_dir} \
    --num_decoding_left_chunks -1

fi

if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ]; then
  echo "$(date) stage 1: 生成triton model."

  # 流式
  onnx_dir=${out_dir}/onnx_model/online_model
  cp -r ${model_dir}/model_repo_stateful ${out_dir}/
  python local/triton_model_repo/scripts/convert.py \
    --config ${in_dir}/train.yaml \
    --vocab ${vocab_path} \
    --model_repo ${out_dir}/model_repo_stateful \
    --onnx_model_dir ${onnx_dir} \
    --lm_path ${lm_path}

  # 非流式
  onnx_dir=$out_dir/onnx_model/offline_model
  cp -r ${model_dir}/model_repo ${out_dir}/
  python local/triton_model_repo/scripts/convert.py \
    --config ${in_dir}/train.yaml \
    --vocab ${vocab_path} \
    --model_repo ${out_dir}/model_repo \
    --onnx_model_dir ${onnx_dir} \
    --lm_path ${lm_path}
fi

if [ ${stage} -le 2 ] && [ ${stop_stage} -ge 2 ]; then
  # 删除GPU onnx文件夹
  rm -rf $out_dir/onnx_model
  # 拷贝其他必须文件
  cp -r ${model_4x}/* $out_dir
  if [ ! -f $out_dir/lang_char.txt ];then
    cp ${model_dir}/lang_char.txt $out_dir
  fi 
  if [ ! -f $out_dir/lm.bin ];then
    cp ${model_dir}/lm.bin $out_dir
  fi 
fi

if [ ${stage} -le 3 ] && [ ${stop_stage} -ge 3 ]; then
  # 生成md5文件
  find $out_dir -type f|xargs md5sum >> md5sum.txt
  mv md5sum.txt $out_dir
fi
echo "export models successfully!"

