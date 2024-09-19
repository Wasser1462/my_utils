#!/bin/bash
# Created by fangcheng on 2022/12/07
# 导出cpu推理需要的模型文件

set -e
. ./path.sh || exit 1

stage=0
stop_stage=3

conf_path=""
beam_size=10
num_decoding_left_chunks=-1
online_chunk_size=16
offline_chunk_size=-1

average_num=5

. tools/parse_options.sh || exit 1

if [ $# != 3 ]; then
  echo "Usage: $0 [options] <in_dir> <model_dir> <out_dir>"
  echo "in_dir: 训练完成的模型文件夹路径,需要包含train.yaml以及pytorch模型文件路径."
  echo "model_dir: 发版模型文件夹, 需包含conf/asr.yaml文件."
  echo "out_dir: 导出的模型推理文件夹路径."
  echo "--average_num: 默认5."
  exit 1
fi

in_dir=$1
model_dir=$2
out_dir=$3

conf_path=${model_dir}/conf/asr.yaml

mkdir -p $out_dir

if [[ $conf_path != "" ]]; then
  num_decoding_left_chunks=`yq .decoder_config.num_left_chunks $conf_path`
  beam_size=`yq .decoder_config.beam $conf_path`
fi

if [ ${stage} -le 0 ] && [ ${stop_stage} -ge 0 ]; then
  echo "$(date) stage 0: 导出script model."
  python wenet/bin/export_jit.py \
    --config $in_dir/train.yaml \
    --checkpoint $in_dir/avg_${average_num}.pt \
    --output_file $out_dir/final.zip \
    --output_quant_file $out_dir/asr.zip
fi

if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ]; then
  echo "$(date) stage 1: 导出onnx model."
  # 导出流式模型
  onnx_dir=$out_dir/onnx_model/online_model
  python wenet/bin/export_onnx_cpu.py \
    --config $in_dir/train.yaml \
    --checkpoint $in_dir/avg_${average_num}.pt \
    --chunk_size ${online_chunk_size} \
    --output_dir $onnx_dir \
    --num_decoding_left_chunks ${num_decoding_left_chunks}

  is_online_quant=`python local/self_learning/export/verify_quant_model.py \
                   ${model_dir}/onnx_model/online_model/ctc.onnx`
  is_online_quant=`echo $is_online_quant | grep "is_quant=.*" -o | cut -d "=" -f 2`
  if [[ ${is_online_quant} == 'True' ]];then
    mv ${onnx_dir}/ctc.quant.onnx ${onnx_dir}/ctc.onnx
    mv ${onnx_dir}/decoder.quant.onnx ${onnx_dir}/decoder.onnx
    mv ${onnx_dir}/encoder.quant.onnx ${onnx_dir}/encoder.onnx
  else
    rm -f ${onnx_dir}/*.quant.onnx
  fi
  # 导出非流式模型
  onnx_dir=$out_dir/onnx_model/offline_model
  python wenet/bin/export_onnx_cpu.py \
    --config $in_dir/train.yaml \
    --checkpoint ${in_dir}/avg_${average_num}.pt \
    --chunk_size ${offline_chunk_size} \
    --output_dir ${onnx_dir} \
    --num_decoding_left_chunks ${num_decoding_left_chunks}

  is_offline_quant=`python local/self_learning/export/verify_quant_model.py \
                    ${model_dir}/onnx_model/offline_model/ctc.onnx`
  is_offline_quant=`echo $is_offline_quant | grep "is_quant=.*" -o | cut -d "=" -f 2`
  if [[ ${is_offline_quant} == 'True' ]];then
    mv ${onnx_dir}/ctc.quant.onnx ${onnx_dir}/ctc.onnx
    mv ${onnx_dir}/decoder.quant.onnx ${onnx_dir}/decoder.onnx
    mv ${onnx_dir}/encoder.quant.onnx ${onnx_dir}/encoder.onnx
  else
    rm -f ${onnx_dir}/*.quant.onnx
  fi
fi

if [ ${stage} -le 2 ] && [ ${stop_stage} -ge 2 ]; then
  # 将本次更新的模型与发版的资源文件进行组合, 组成本次优化后的可发版模型.
  documents="lang_char.txt lm.bin token_similarity"
  for comment in $documents;do
    if [ -f $model_dir/${comment} ];then
      cp $model_dir/${comment} $out_dir
    fi
  done
  folders="conf graph post_processing self_learning"
  for folder in $folders;do
    if [ -d $model_dir/${folder} ];then
      cp -rL $model_dir/${folder}/ $out_dir
    fi
  done

  # 更新自学习文件
  rm $out_dir/self_learning/exp/*
  cp $in_dir/avg_${average_num}.pt $out_dir/self_learning/exp/init.pt
  cp $in_dir/train.yaml $out_dir/self_learning/exp/
  cp $in_dir/global_cmvn $out_dir/self_learning/exp/

  mkdir $out_dir/libtorch_model
  if [[ ${is_offline_quant} == 'True' ]];then
    mv $out_dir/asr.zip $out_dir/libtorch_model/asr.zip
    rm $out_dir/final.zip
  else
    mv $out_dir/final.zip $out_dir/libtorch_model/asr.zip
    rm $out_dir/asr.zip
  fi
fi

if [ ${stage} -le 3 ] && [ ${stop_stage} -ge 3 ]; then
  # 生成md5文件
  find $out_dir -type f|xargs md5sum >> md5sum.txt
  mv md5sum.txt $out_dir
fi
echo "export models successfully!"
