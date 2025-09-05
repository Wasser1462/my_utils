# Date : 2025-09-05
import os
import sys
import argparse
import numpy as np
import soundfile as sf
from pathlib import Path
from fractions import Fraction
from scipy.signal import resample_poly, fftconvolve, butter, sosfiltfilt
from funasr import AutoModel
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class My_utils():
    def read_scp(self, scp_path):
        pairs = []
        with open(scp_path, 'r', encoding='utf-8') as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith('#'):
                    continue
                parts = ln.split(maxsplit=1)
                if len(parts) != 2:
                    continue
                utt, path = parts
                pairs.append((utt, path))
        return pairs

    def read_text(self, text_path):
        pairs = {}
        with open(text_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip('\n')
                if not line or line.startswith('#'):
                    continue
                splite = line.split(maxsplit=1)
                if len(splite) == 1:
                    utt, text = splite[0], ''
                else:
                    utt, text = splite[0], splite[1]
                pairs[utt] = text
        return pairs

    def to_mono(self, wav):
        if wav.ndim == 1:
            return wav.astype(np.float32)
        wav = np.mean(wav, axis=1).astype(np.float32)
        return wav

    def resample(self, wav, sr_from, sr_to):
        if sr_from == sr_to:
            return wav.astype(np.float32)
        frac = Fraction(sr_to, sr_from).limit_denominator(1000)
        up, down = frac.numerator, frac.denominator
        return resample_poly(wav, up=up, down=down).astype(np.float32)

    def load_audio_mono(self, path):
        y, sr = sf.read(path, always_2d=False)
        y = self.to_mono(np.asarray(y))
        y = np.clip(y, -1.0, 1.0).astype(np.float32)
        return y, int(sr)

    def change_speed(self, y, speed):
        speed = max(0.5, min(2.0, float(speed)))
        frac = Fraction(speed).limit_denominator(1000)
        up, down = frac.numerator, frac.denominator
        return resample_poly(y, up=up, down=down).astype(np.float32)

    def butter_filter(self, y, fs, ftype='bandpass', f_low=300.0, f_high=3400.0, order=4):
        nyq = 0.5 * fs
        if ftype == 'bandpass':
            low = max(10.0, f_low) / nyq
            high = min(fs/2-10.0, f_high) / nyq
            if low >= high:
                return y
            sos = butter(order, [low, high], btype='band', output='sos')
        elif ftype == "lowpass":
            high = min(fs/2-10.0, f_high) / nyq
            sos = butter(order, high, btype="low", output="sos")
        elif ftype == "highpass":
            low = max(10.0, f_low) / nyq
            sos = butter(order, low, btype="high", output="sos")
        else:
            return y
        try:
            return sosfiltfilt(sos, y).astype(np.float32)
        except Exception:
            from scipy.signal import sosfilt
            return sosfilt(sos, y).astype(np.float32)

    def rms(self, x):
        x = x.astype(np.float32)
        return np.sqrt(np.mean(np.square(x)) + 1e-12)

    def convolve_rir(self, y, rir):
        if len(rir) == 0:
            return y
        out = fftconvolve(y.astype(np.float64), rir.astype(np.float64), mode='full')
        ry = self.rms(y)
        ro = self.rms(out)
        if ro > 1e-9:
            out = out * (ry / ro)
        return out.astype(np.float32)

    def peak_normalize(self, x, peak_margin=0.999):
        peak = float(np.max(np.abs(x) + 1e-12))
        if peak > 1.0:
            x = x * (peak_margin / peak)
        return x.astype(np.float32)

    def load_random_segment(self, path, target_len, sr_target, rng):
        with sf.SoundFile(path, mode='r') as f:
            sr_src = f.samplerate
            frames = len(f)
            if frames == 0:
                return np.zeros(target_len, dtype=np.float32)
            need_src = target_len if sr_src == sr_target else int(np.ceil(target_len * sr_src / sr_target))
            if frames >= need_src:
                starts = int(rng.integers(0, frames - need_src + 1))
                f.seek(starts)
                seg = f.read(need_src, dtype='float32', always_2d=True)
            else:
                f.seek(0)
                seg = f.read(frames, dtype="float32", always_2d=True)
            seg = self.to_mono(seg)
            seg = np.clip(seg, -1.0, 1.0).astype(np.float32)
            if sr_src != sr_target:
                seg = self.resample(seg, sr_src, sr_target)
            if len(seg) < target_len:
                reps = int(np.ceil(target_len / max(1, len(seg))))
                seg = np.tile(seg, reps)[:target_len]
            elif len(seg) > target_len:
                s = int(rng.integers(0, len(seg) - target_len + 1))
                seg = seg[s:s + target_len]
            return seg.astype(np.float32)

    def load_random_rir(self, rir_path, sr_target):
        y, sr = self.load_audio_mono(rir_path)
        if sr != sr_target:
            y = self.resample(y, sr, sr_target)
        y = y / (np.max(np.abs(y)) + 1e-9)
        return y.astype(np.float32)

    def mix_background_at_snr(self, speech, bg_seg, snr_db):
        rs = self.rms(speech)
        rn = self.rms(bg_seg)
        if rn < 1e-10:
            return speech.astype(np.float32)
        alpha = rs / (rn * (10.0 ** (snr_db / 20.0)))
        if len(bg_seg) < len(speech):
            bg_seg = np.tile(bg_seg, int(np.ceil(len(speech) / len(bg_seg))))[:len(speech)]
        mixed = speech.astype(np.float32) + (alpha * bg_seg.astype(np.float32))
        return mixed.astype(np.float32)

    def place_with_offset(self, container_len, seg_len, rng):
        if seg_len >= container_len:
            return 0
        return int(rng.integers(0, container_len - seg_len + 1))

    def build_interference_sum(self, L, sr, interfere_pairs, rng, overlap_min=0.3, overlap_max=1.0, max_interferers=2, speed_prob=0.3, speed_min=0.9, speed_max=1.1, filter_prob=0.3, rir_prob=0.0, rir_list=None, rir_volume=0.6):
        K = int(rng.integers(1, max_interferers + 1))
        out = np.zeros(L, dtype=np.float32)

        for _ in range(K):
            iutt, ipath = interfere_pairs[int(rng.integers(0, len(interfere_pairs)))]
            seg_len = int(np.clip(int(rng.uniform(overlap_min, overlap_max) * L), 1, L))
            raw = self.load_random_segment(ipath, seg_len, sr, rng)

            if rng.random() < speed_prob:
                factor = float(rng.uniform(speed_min, speed_max))
                raw = self.change_speed(raw, factor)

            if len(raw) < seg_len:
                reps = int(np.ceil(seg_len / max(1, len(raw))))
                raw = np.tile(raw, reps)[:seg_len]

            elif len(raw) > seg_len:
                s = int(rng.integers(0, len(raw) - seg_len + 1))
                raw = raw[s:s + seg_len]

            if rng.random() < filter_prob:
                if rng.random() < 0.7:
                    raw = self.butter_filter(raw, fs=sr, ftype="bandpass", f_low=300.0, f_high=3400.0, order=4)
                else:
                    f_hi = float(rng.uniform(2500.0, 5000.0))
                    raw = self.butter_filter(raw, fs=sr, ftype="lowpass", f_high=f_hi, order=4)
            
            if rir_list and len(rir_list) > 0 and (rng.random() < rir_prob):
                r_utt, r_path = rir_list[int(rng.integers(0, len(rir_list)))]
                rir = self.load_random_rir(r_path, sr)
                rir = rir_volume * rir
                raw = self.convolve_rir(raw, rir)
            
            if len(raw) > seg_len:
                raw = raw[:seg_len]
            
            elif len(raw) < seg_len:
                reps = int(np.ceil(seg_len / max(1, len(raw))))
                raw = np.tile(raw, reps)[:seg_len]
            
            start = self.place_with_offset(L, seg_len, rng)
            out[start:start + seg_len] += raw
        return out.astype(np.float32)

    def mix_interferers_at_sir(self, speech, interf_sum, sir_db):
        rs = self.rms(speech)
        ri = self.rms(interf_sum)
        
        if ri < 1e-10:
            return speech.astype(np.float32)
        beta = rs / (ri * (10.0 ** (sir_db / 20.0)))
        
        if len(interf_sum) < len(speech):
            interf_sum = np.tile(interf_sum, int(np.ceil(len(speech) / len(interf_sum))))[:len(speech)]
        mixed = speech.astype(np.float32) + beta * interf_sum.astype(np.float32)
        return mixed.astype(np.float32)

def parse_args():
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--in-scp-name", default="wav.scp")
    ap.add_argument("--in-text-name", default="text")
    ap.add_argument("--out-scp-name", default="wav.scp")
    ap.add_argument("--out-text-name", default="text")
    ap.add_argument("--interfere-scp", required=True)
    ap.add_argument("--sir-min", type=float, default=0.0)
    ap.add_argument("--sir-max", type=float, default=10.0)
    ap.add_argument("--max-interferers", type=int, default=2)
    ap.add_argument("--overlap-min", type=float, default=0.3)
    ap.add_argument("--overlap-max", type=float, default=1.0)
    ap.add_argument("--bg-scp", default=None)
    ap.add_argument("--snr-min", type=float, default=5.0)
    ap.add_argument("--snr-max", type=float, default=20.0)
    ap.add_argument("--bg-prob", type=float, default=0.8)
    ap.add_argument("--speed-prob", type=float, default=0.3)
    ap.add_argument("--speed-min", type=float, default=0.9)
    ap.add_argument("--speed-max", type=float, default=1.1)
    ap.add_argument("--filter-prob", type=float, default=0.3)
    ap.add_argument("--rir-scp", default=None)
    ap.add_argument("--rir-prob", type=float, default=0.3)
    ap.add_argument("--copies", type=int, default=1)
    ap.add_argument("--peak-margin", type=float, default=0.999)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rir_volume", type=float, default=0.6)
    ap.add_argument("--num-workers", type=int, default=8)
    return ap.parse_args()

def seg_ms_to_samples(seg, sr, total_len):
    if isinstance(seg, dict):
        s_ms = float(seg.get("start", 0.0)); e_ms = float(seg.get("end", 0.0))
    else:
        s_ms = float(seg[0]); e_ms = float(seg[1])
    s = int(round(s_ms * sr / 1000.0))
    e = int(round(e_ms * sr / 1000.0))
    s = max(0, min(total_len, s))
    e = max(s, min(total_len, e))
    return s, e

def main():
    args = parse_args()
    if args.copies < 1:
        print("[ERROR] --copies must >= 1。", file=sys.stderr); sys.exit(1)
    if args.sir_max < args.sir_min:
        print("[ERROR] SIR range is error", file=sys.stderr); sys.exit(1)
    if args.snr_max < args.snr_min:
        print("[ERROR] SNR range is error", file=sys.stderr); sys.exit(1)
    if not (0.0 <= args.overlap_min <= args.overlap_max <= 1.0):
        print("[ERROR] overlap range is error, it must be 0<=min<=max<=1。", file=sys.stderr); sys.exit(1)

    rng_global = np.random.default_rng(args.seed)
    in_scp = Path(args.in_dir) / args.in_scp_name
    in_text = Path(args.in_dir) / args.in_text_name
    out_dir = Path(args.out_dir)
    out_scp_path = out_dir / args.out_scp_name
    out_text_path = out_dir / args.out_text_name
    wav_dir = out_dir / "wav"
    wav_dir.mkdir(parents=True, exist_ok=True)

    utils = My_utils()
    
    train_pairs = utils.read_scp(str(in_scp))
    if not train_pairs:
        print("[ERROR] train is empty and exit", file=sys.stderr); sys.exit(1)
    text_map = utils.read_text(str(in_text))
    if not text_map:
        print("[ERROR] text is empty or error", file=sys.stderr); sys.exit(1)
    interfere_pairs = utils.read_scp(args.interfere_scp)
    if not interfere_pairs:
        print("[ERROR] speaker data is empty or error ,please check。", file=sys.stderr); sys.exit(1)
    
    bg_pairs = utils.read_scp(args.bg_scp) if args.bg_scp else []
    rir_pairs = utils.read_scp(args.rir_scp) if args.rir_scp else []
    os.makedirs(out_dir, exist_ok=True)
    vad_model = AutoModel(model="../SenseVoice/fsmn_vad", model_revision="v2.0.4", disable_update=True)
    vad_lock = threading.Lock()

    def run_vad(path):
        with vad_lock:
            res = vad_model.generate(input=path)
        return res

    def process_one(idx, pair):
        t_utt, t_path = pair

        if t_utt not in text_map:
            return []
        
        try:
            speech, sr_t = utils.load_audio_mono(t_path)
        except Exception as e:
            print(f"[WARN] failed read wav:{t_utt} -> {t_path} ({e}), skip", file=sys.stderr)
            return []
       
        L = len(speech)
        if L <= 0:
            print(f"[WARN] empty wav:{t_utt} -> {t_path}, skip .", file=sys.stderr)
            return []
        base_txt = text_map[t_utt]
      
        try:
            vad_res = run_vad(t_path)
            raw_vad = vad_res[0].get("value", [])
        except Exception as e:
            print(f"[WARN] VAD failed for {t_utt}: {e}", file=sys.stderr)
            raw_vad = []
      
        seg_samples = [seg_ms_to_samples(seg, sr_t, L) for seg in raw_vad]
        if not seg_samples:
            seg_samples = [(0, L)]
        outs = []
        base_seed = int(args.seed + idx * 1315423911)
       
        for c in range(args.copies):
            mixed = speech.copy().astype(np.float32)
            rng = np.random.default_rng(base_seed + c + 1)
            for (start, end) in seg_samples:
                if end - start <= 0:
                    continue  
                seg_view = mixed[start:end].copy()
                
                if bg_pairs and (rng.random() < args.bg_prob):
                    bg_utt, bg_path = bg_pairs[int(rng.integers(0, len(bg_pairs)))]
                    
                    try:
                        bg_seg = utils.load_random_segment(bg_path, end - start, sr_t, rng)
                        snr_db = float(rng.uniform(args.snr_min, args.snr_max))
                        seg_view = utils.mix_background_at_snr(seg_view, bg_seg, snr_db)
                    except Exception as e:
                        print(f"[WARN] failed read background noise: {bg_utt} -> {bg_path} ({e}), skip.", file=sys.stderr)
                
                try:
                    interf_sum = utils.build_interference_sum(
                        end - start, sr_t, interfere_pairs, rng,
                        overlap_min=args.overlap_min, overlap_max=args.overlap_max,
                        max_interferers=args.max_interferers, speed_prob=args.speed_prob,
                        speed_min=args.speed_min, speed_max=args.speed_max,
                        filter_prob=args.filter_prob, rir_prob=args.rir_prob, rir_list=rir_pairs,
                        rir_volume=args.rir_volume
                    )
                    sir_db = float(rng.uniform(args.sir_min, args.sir_max))
                    seg_view = utils.mix_interferers_at_sir(seg_view, interf_sum, sir_db)
                
                except Exception as e:
                    print(f"[WARN] Failed to mix interferer for {t_utt}: {e}.", file=sys.stderr)
                mixed[start:end] = seg_view

            mixed = utils.peak_normalize(mixed, peak_margin=args.peak_margin)
            suffix = f"_aug{c+1}" if args.copies > 1 else "_aug1"
            out_name = f"{t_utt}{suffix}.wav"
            out_path = str(wav_dir / out_name)

            try:
                sf.write(out_path, mixed, sr_t, subtype="PCM_16")
            
            except Exception as e:
                print(f"[WARN] failed to write file:{out_path} ({e}), skip.", file=sys.stderr)
                continue
            
            out_utt = f"{t_utt}{suffix}"
            outs.append((out_utt, out_path, base_txt))
        return outs

    total = len(train_pairs)
    num_workers = args.num_workers if args.num_workers > 0 else max(1, (os.cpu_count() or 4) - 1)
    results = []
    
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futs = {ex.submit(process_one, i, pair): i for i, pair in enumerate(train_pairs)}
        done_count = 0
        for fut in as_completed(futs):
            outs = fut.result()
            if outs:
                results.extend(outs)
            done_count += 1
            if done_count % 20 == 0 or done_count == total:
                print(f"[INFO] files processed: {done_count}/{total}", file=sys.stderr)

    with open(out_scp_path, "w", encoding="utf-8") as out_scp_fp, open(out_text_path, "w", encoding="utf-8") as out_text_fp:
        for out_utt, out_path, base_txt in results:
            out_scp_fp.write(f"{out_utt} {out_path}\n")
            out_text_fp.write(f"{out_utt} {base_txt}\n")

    print(f"[DONE] Output {len(results)} augmented audio and text pairs. SCP: {out_scp_path}, TEXT: {out_text_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
