# Author: zyw
# Date: 2024-09-11
# Description: 检测训练数据的一致性

import os
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_data_consistency(wav_scp_lines, text_lines, data_list_lines):
    if len(wav_scp_lines) != len(text_lines) or len(wav_scp_lines) != len(data_list_lines):
        logging.warning("============================================================")
        logging.warning("警告: wav.scp, text, data.list 文件的行数不一致,请检查输入文件。")
        logging.warning("wav.scp 行数: %d", len(wav_scp_lines))
        logging.warning("text 行数: %d", len(text_lines))
        logging.warning("data.list 行数: %d", len(data_list_lines))
        logging.warning("============================================================")
    else:
        logging.info("数据一致性检查通过")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Check train data .')
    parser.add_argument('input_dir', help='input dir,include wav.scp,text,data.list')
    
    args = parser.parse_args()
    
    wav_scp_path = os.path.join(args.input_dir, 'wav.scp')
    text_path = os.path.join(args.input_dir, 'text')
    data_list_path = os.path.join(args.input_dir, 'data.list')

    with open(wav_scp_path, 'r') as wav_scp_file, open(text_path, 'r') as text_file, open(data_list_path, 'r') as data_list_file:
        wav_scp_lines = wav_scp_file.readlines()
        text_lines = text_file.readlines()
        data_list_lines = data_list_file.readlines()
        check_data_consistency(wav_scp_lines, text_lines, data_list_lines)
    logging.info('check done !')

