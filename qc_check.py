#!/usr/bin/env python3
"""
Narration QC — proves the voiceover is really audible in the final MP4.

Method (house standard): sample-level FFT cross-correlation between the
clean voiceover WAV and the final video's audio, over a +/-2 second lag
window, using the complex conjugate. A sanity check (voice vs itself)
must score ~1.0. PASS = final score > 0.5.

Usage:
  python3 qc_check.py <voice_full.wav> <final_video.mp4>
(needs numpy + ffmpeg/ffprobe on the machine — local verification tool,
 not needed inside GitHub Actions.)
"""
import subprocess
import sys

import numpy as np

SR = 22050


def load_wav_as_float(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def fft_xcorr_peak(a, b, sr, max_lag_s=2.0):
    """Max normalized cross-correlation of a and b within +/- max_lag_s."""
    n = len(a) + len(b) - 1
    L = 1 << (n - 1).bit_length()
    A = np.fft.rfft(a, L)
    B = np.fft.rfft(b, L)
    corr = np.fft.irfft(A * np.conj(B), L)
    lag = int(max_lag_s * sr)
    window = np.concatenate([corr[:lag + 1], corr[L - lag:]])
    denom = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if denom == 0:
        return 0.0
    return float(np.max(np.abs(window)) / denom)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    vo = load_wav_as_float(sys.argv[1])
    fin = load_wav_as_float(sys.argv[2])
    sanity = fft_xcorr_peak(vo, vo.copy(), SR)
    score = fft_xcorr_peak(vo, fin, SR)
    print(f"sanity (voice vs itself): {sanity:.4f}")
    print(f"narration QC score:       {score:.4f}")
    print("PASS" if score > 0.5 and sanity > 0.99 else "FAIL")
    sys.exit(0 if score > 0.5 else 1)


if __name__ == "__main__":
    main()
