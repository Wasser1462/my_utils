import logging

logging.basicConfig(level=logging.INFO)

def __wavscp(wav_scp):
    with open(wav_scp, 'r', encoding="utf-8") as f:
        texts = f.readlines()
    
    total_time = 0
    for text in texts:
        text_list = text.split()
        assert len(text_list) == 2  
        id_sequence = text_list[0].strip().split('-')  
        time = (int(id_sequence[-2]) - int(id_sequence[-3])) / 1000 
        total_time += time

    logging.info(f"统计结果: {len(texts)}条, 总时长: {total_time:.3f}s / {total_time / 3600:.3f}h.")

wav_scp_file = '/data1/zengyongwang/oupai/wav-channels/part2/wav.scp' 
__wavscp(wav_scp_file)
