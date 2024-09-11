# Author: zyw
# Date: 2024-09-01
# Description: test
from augment_data import check_data_consistency
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    input_dir = '/data1/zengyongwang/dataset/output/train'
    wav_scp_path = os.path.join(input_dir, 'wav.scp')
    text_path = os.path.join(input_dir, 'text')
    data_list_path = os.path.join(input_dir, 'data.list')

    with open(wav_scp_path, 'r') as wav_scp_file, open(text_path, 'r') as text_file, open(data_list_path, 'r') as data_list_file:
        wav_scp_lines = wav_scp_file.readlines()
        text_lines = text_file.readlines()
        data_list_lines = data_list_file.readlines()
        check_data_consistency(wav_scp_lines, text_lines, data_list_lines)
        logger.info('Data consistency check passed.')
    logger.info('Test completed.')