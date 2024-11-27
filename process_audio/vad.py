# Author: zyw
# Date: 2024-11-27
# Description: This script is used to extract segments from audio files using Voice Activity Detection (VAD).

import os
import argparse
from pydub import AudioSegment
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks

inference_pipeline = pipeline(
    task=Tasks.voice_activity_detection,
    model='iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',
    model_revision="v2.0.4",
)

def process_audio(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.endswith('.wav'):
            input_file = os.path.join(input_folder, filename)

            segments_result = inference_pipeline(input=input_file)
            segments = segments_result[0]['value']  

            audio = AudioSegment.from_wav(input_file)

            combined_audio = AudioSegment.empty()

            for segment in segments:
                start_ms = segment[0]  
                end_ms = segment[1]    
                segment_audio = audio[start_ms:end_ms]
                combined_audio += segment_audio  

            output_file = os.path.join(output_folder, filename)
            combined_audio.export(output_file, format='wav')

            print(f"Processed {filename} and saved to {output_file}")

    print("Processing completed!")

def main():

    parser = argparse.ArgumentParser(description='Process audio files using VAD and save the results.')
    parser.add_argument('input_folder', type=str, help='The folder containing input .wav files')
    parser.add_argument('output_folder', type=str, help='The folder where processed .wav files will be saved')

    args = parser.parse_args()

    process_audio(args.input_folder, args.output_folder)

if __name__ == '__main__':
    main()
