#!/bin/bash

SOURCE_DIR1="/data1/zengyongwang/oupai/wav-channels/part1"
SOURCE_DIR2="/data1/zengyongwang/oupai/wav-channels/part2"
TARGET_DIR="/data1/zengyongwang/oupai/wav-channels-processed"

mkdir -p "${TARGET_DIR}"

cat "${SOURCE_DIR1}/segments.txt" "${SOURCE_DIR2}/segments.txt" | sort | uniq > "${TARGET_DIR}/segments.txt"


cat "${SOURCE_DIR1}/wav.scp" "${SOURCE_DIR2}/wav.scp" | sort | uniq > "${TARGET_DIR}/wav.scp"


cp -rn "${SOURCE_DIR1}"/* "${TARGET_DIR}/"
cp -rn "${SOURCE_DIR2}"/* "${TARGET_DIR}/"

echo "合并完成！"
