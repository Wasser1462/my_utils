import os
import glob
from funasr import AutoModel
import re
from collections import Counter
from funasr.utils.postprocess_utils import rich_transcription_postprocess

model_dir = "iic/SenseVoiceSmall"

def emotion_tag(text):
    print(f"text: {text}") 
    pattern = r"<\|([A-Z]+)\|>"
    tags = re.findall(pattern, text)

    if not tags:
        return None
    
    tag_counts = Counter(tags)
    most_common_tag, _ = tag_counts.most_common(1)[0]
    
    return most_common_tag

def format_str(s):
    match = re.search("[\u4e00-\u9fa5]", s)
    if match:
        start = match.start()
        return s[start:]
    return ""

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  
        u"\U0001F300-\U0001F5FF"  
        u"\U0001F680-\U0001F6FF" 
        u"\U0001F1E0-\U0001F1FF"  
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


model = AutoModel(
    model=model_dir,
    trust_remote_code=True,
    remote_code="./model.py",
    vad_model="fsmn-vad",
    vad_kwargs={"max_single_segment_time": 30000},
    device="cuda:0",
)

wav_dir = "/data1/zengyongwang/test/emotion2vec/emotion_wav"
wav_files = glob.glob(os.path.join(wav_dir, "*.wav"))


output_dir = "./outputs"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "results.txt")


with open(output_file, "w") as f:
    for wav_file in wav_files:
        try:
            res = model.generate(
                input=wav_file,
                cache={},
                language="auto",  
                use_itn=True,  
                batch_size_s=60,  
                merge_vad=True,  
                merge_length_s=15, 
            )
            
            text=rich_transcription_postprocess(res[0]["text"])
            emotion = emotion_tag(res[0]["text"])
            result = format_str(text)
            result = remove_emojis(result)
            
            f.write(f"{wav_file}: emotion:{emotion}, text:{result} \n")
            print(f"Processed {wav_file}, result saved to {output_file}")
        except Exception as e:
            print(f"Error processing {wav_file}: {e}")

print("Processing completed.")

