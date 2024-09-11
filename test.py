import os
import json
import argparse
from pydub import AudioSegment
import numpy as np
import shutil
from multiprocessing import pool
import logging

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(name)s %(levelname)s ')
logger = logging.getLogger(__name__)

def check_data_consistency(wav_scp_lines, text_lines, data_list_lines):
    if len(wav_scp_lines) != len(text_lines) or len(wav_scp_lines) != len(data_list_lines):
        logger.error('Data length is not consistent!')
        return False
    return True
    
def copy_dev_folder(source_dir, output_dir):
    dev_folder = os.path.join(source_dir, 'dev')
    des_folder = os.path.join(output_dir, 'dev')
    if os.path.exists(dev_folder):
        shutil.copytree(dev_folder, des_folder)
        logging.info('dev folder copied successfully!')
    else:
        logger.error('No dev folder found in the source directory!')
        
def add_noise(audio_segment,noise_factor=0.02):
    sample = np.array(audio_segment.get_array_of_samples())
    noise = np.random.randn(0, 1, len(sample))
    augmented_sample = sample + noise_factor * noise*np.max(np.abs(sample))
    augmented_audio = audio_segment.from_array(augmented_sample) 
    return augmented_audio   