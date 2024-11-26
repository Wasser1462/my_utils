
from funasr import AutoModel
import json
import torch
from pathlib import Path
from argparse import ArgumentParser
import os

def load_wavs(path):
  return path.iterdir()


def load_scp(scp_file):
  with open(scp_file, 'r', encoding="utf-8") as f:
    texts = f.readlines()
  result = {}
  for text in texts:
    text_list = text.split()
    assert len(text_list) == 2
    result[text_list[0]] = Path(text_list[1])
  
  return result


def non_stream(paths, save_path, device="cpu"):
  """
    model = AutoModel(model="paraformer-zh",  vad_model="fsmn-vad",  punc_model="ct-punc")
  """
  model = AutoModel(model="paraformer", model_revision="v2.0.4",vad_model="fsmn-vad", device=device)
  if not save_path.exists():
    save_path.mkdir(parents=True)
  
  f_write = open(f"{save_path}/text", "w")
  if isinstance(paths, dict):
    paths = paths.values()

  res = ""
  for wav_file in paths:
    audio_name = wav_file.name
    try:
        res = model.generate(input=str(wav_file))
    except Exception as err:
        print("generate result fail!audio_name:{},err:{}".format(audio_name,err))
        continue
    if len(res) > 0:
        text = res[0]["text"]
        score = res[0]["score"]
        f_write.write(f"{audio_name}|{text}|{score}\n")
  f_write.close()


if __name__=="__main__":
  desc = "funasr asr."
  parser = ArgumentParser(description=desc)
  parser.add_argument("save_dir", type=Path, help="输出文件夹路径.")
  parser.add_argument("--wav_scp", type=Path,
                      help="wav_scp")
  parser.add_argument("--wavs", type=Path,help="wav.")
  parser.add_argument('--gpu',
                        type=int,
                        default=-1,
                        help='gpu id for this rank, -1 for cpu')
  args = parser.parse_args()
  if args.wav_scp is not None:
    wav_paths = load_scp(args.wav_scp)
  elif args.wavs is not None:
    wav_paths =load_wavs(args.wavs)
  else:
    raise ValueError(f"No wav path.")
  if args.gpu != "-1":
    device="cuda:{}".format(args.gpu)
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
  else:
    device="cpu"
  os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
  non_stream(wav_paths, save_path=args.save_dir, device=device)

