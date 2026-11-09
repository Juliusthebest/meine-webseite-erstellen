"""Erzeugt die Sprachaufnahmen mit Piper (deutsche Stimmen) + ffmpeg-Effekten."""
import os, subprocess, hashlib, json, wave

VOICE_DIR = os.environ.get("VOICE_DIR", "voices")

# Stimme, Tempo (length_scale), ffmpeg-Filter
VOICES = {
    "MIA":    ("de-kerstin-low",  1.00, "asetrate=16000*1.06,aresample=44100,atempo=0.95"),
    "MAMA":   ("de-ramona-low",   1.05, "aresample=44100"),
    "BEN":    ("de-thorsten-low", 1.00, "aresample=44100"),
    "OPA":    ("de-karlsson-low", 1.15, "asetrate=16000*0.92,aresample=44100,atempo=1.05,vibrato=f=5:d=0.15"),
    "DOC":    ("de-pavoque-low",  1.05, "aresample=44100"),
    "ERZ":    ("de-karlsson-low", 1.20, "asetrate=16000*0.86,aresample=44100,atempo=1.08,aecho=0.8:0.7:60:0.25"),
    "ZOMBIE": ("de-thorsten-low", 1.30, "asetrate=16000*0.72,aresample=44100,atempo=1.15,"
                                       "acrusher=bits=8:mix=0.25,vibrato=f=7:d=0.35,aecho=0.8:0.6:40:0.3"),
    "KEVIN":  ("de-pavoque-low",  1.35, "asetrate=16000*0.78,aresample=44100,atempo=1.1,"
                                       "vibrato=f=6:d=0.3,aecho=0.8:0.6:40:0.3"),
}


def tts(speaker, text, out_dir):
    model, length, filt = VOICES[speaker]
    key = hashlib.md5(f"{speaker}|{text}|{model}|{length}|{filt}".encode()).hexdigest()[:12]
    final = os.path.join(out_dir, f"{speaker}_{key}.wav")
    if os.path.exists(final):
        return final
    raw = final + ".raw.wav"
    subprocess.run(["python3", "-m", "piper", "-m", os.path.join(VOICE_DIR, model + ".onnx"),
                    "--length-scale", str(length), "--sentence-silence", "0.15", "-f", raw],
                   input=text.encode(), check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    filt + ",loudnorm=I=-16:TP=-1.5,aformat=sample_fmts=s16:channel_layouts=mono",
                    "-ar", "44100", final], check=True)
    os.remove(raw)
    return final
