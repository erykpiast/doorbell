# Sound tools

Python scripts that make the WAV files the receiver plays. They use only the
Python standard library.

| Script | What it does |
| --- | --- |
| `gen_chime.py` | Makes `chime.wav`: a two-note "ding-dong" bell. This is the default doorbell sound. |
| `gen_alarm.py` | Makes `alarm.wav`: a harsh, scream-like tone that is hard to ignore. |
| `gen_melody.py` | Makes `melody.wav`: a short sequence of notes. Used to test the speaker and DAC. |
| `make_louder.py` | Takes an existing WAV file and raises its volume without hard clipping. |

## Usage

The `gen_*` scripts write their file to the current directory. Run them from
`receiver/`, so `listen.py` finds the result:

```
cd receiver
python3 sound_tools/gen_chime.py
python3 sound_tools/make_louder.py chime.wav chime_loud.wav 12
```

The last argument of `make_louder.py` is the gain in dB. To play another file,
set `DOORBELL_SOUND=chime_loud.wav` when you start `listen.py`.
