import os
from pathlib import Path
import argparse
import subprocess as sp
import numpy as np
from yt_dlp import YoutubeDL
import demucs.api
import madmom
from madmom.features.beats import RNNBeatProcessor, BeatTrackingProcessor
from madmom.features.downbeats import RNNDownBeatProcessor
# from audiostretchy.stretch import process_audio
import pyrubberband as pyrb
import soundfile as sf
import json
import config

def download_audio(url):
    '''
    Download audio file from youtube using ytdlp
    :param url: str, url of the audio file
    :return: None
    '''
    with YoutubeDL(config.YDL_OPTS) as ydl:
        ydl.download(url)
    pass

def split_audio_demucs(path_to_file,model='htdemucs_6s',output_path=config.OUTPUT_DIR):
    '''
    Split audio file using demucs
    :param audio_file: str, path to audio file
    :return: None
    '''
    sp.run(["python3", "-m", "demucs.separate", "-o", output_path, "-n", model, path_to_file])
    output_dir = Path(output_path) / Path(model) / Path(path_to_file).stem
    output_files = output_dir.rglob('*.wav')
    return output_files
    # file_name = os.path.basename(path_to_file)
    # separator = demucs.api.Separator(model=model)
    # origin, separated = separator.separate_audio_file(path_to_file)
    # print("separating stems done")
    # output_paths = []
    # for f, sources in separated:
    #     for stem, source in sources.items():
    #         demucs.api.save_audio(source, f"{output_path}/{stem}_{f}", samplerate=separator.samplerate)
    #         output_paths.append(f"{output_path}/{stem}_{f}")
    # return output_paths

def get_beats(audio_file):
    '''
    Get beats from audio file
    :param audio_file: str, path to audio file
    :return: np.ndarray, beats
    '''
    proc = BeatTrackingProcessor(fps=100)
    act = madmom.features.beats.RNNBeatProcessor()(audio_file)
    beats = proc(act)
    # load info from beat_data.json
    with open(f'{config.OUTPUT_DIR}/beat_data.json', 'r') as f:
        beat_data = json.load(f)
    beat_data['beats'] = beats.tolist()
    with open(f'{config.OUTPUT_DIR}/beat_data.json', 'w') as f:
        json.dump(beat_data, f)

    return beats#proc(act)


def get_downbeats(audio_file, min_confidence=0.10): #0.22
    """
    Get an array of downbeat timestamps from an audio file.
    
    Args:
        audio_file (str): Path to the audio file
        min_confidence (float): Minimum confidence threshold for detection (0-1)
        
    Returns:
        numpy.ndarray: Array of downbeat timestamps in seconds
    """
    # Initialize the processors
    beat_processor = RNNBeatProcessor()
    downbeat_processor = RNNDownBeatProcessor()
    
    # Get beat activations and downbeat activations
    beat_activations = beat_processor(audio_file)
    downbeat_activations = downbeat_processor(audio_file)
    
    # Find frames where both beat and downbeat are detected with sufficient confidence
    downbeat_confidence = downbeat_activations[:, 1]  # Extract downbeat confidence values
    downbeat_frames = np.where(
        (beat_activations >= min_confidence) & 
        (downbeat_confidence >= min_confidence)
    )[0]
    
    # Convert frame indices to timestamps (hop size = 441 samples @ 44100Hz = 0.01s)
    downbeat_times = downbeat_frames * 0.01
    with open(f'{config.OUTPUT_DIR}/beat_data.json', 'r') as f:
        beat_data = json.load(f)
    beat_data['beats'] = downbeat_times.tolist()
    with open(f'{config.OUTPUT_DIR}/beat_data.json', 'w') as f:
        json.dump(beat_data, f)
    
    return downbeat_times

def get_bpm_from_beats(beats):
    '''
    Get bpm from beats
    :param beats: np.ndarray, beats
    :return: float, bpm
    '''
    bpm = 60.0/np.mean(np.diff(beats))
    with open(f'{config.OUTPUT_DIR}/beat_data.json', 'r') as f:
        beat_data = json.load(f)
    beat_data['bpm'] = bpm
    with open(f'{config.OUTPUT_DIR}/beat_data.json', 'w') as f:
        json.dump(beat_data, f)
    return bpm

def get_stretch_ratio(audio_file, target_bpm):
    '''
    Get stretch ratio to target bpm
    :param audio_file: str, path to audio file
    :param target_bpm: float, target bpm
    :return: float, stretch ratio
    '''
    y, sr = sf.read(audio_file)
    bpm = get_bpm_from_beats(get_beats(y))
    return target_bpm/bpm

def time_stretch(audio_file, stretch_ratio=1):
    '''
    Time stretch audio file to target bpm
    :param audio_file: str, path to audio file
    :param target_bpm: float, target bpm
    :return: str, path to stretched audio file
    '''
    output_dir = config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(audio_file)
    y, sr = sf.read(audio_file)
    output_file = os.path.join(output_dir, filename[:filename.find('.')]+"_stretched.wav")
    stretched_audio = pyrb.time_stretch(y, sr, stretch_ratio)
    # stretched_audio = librosa.effects.time_stretch(y, rate=stretch_ratio)
    sf.write(output_file, stretched_audio, sr)
    return output_file

def pitch_shift_audio(audio_file, semitones):
    """
    Pitch shift an audio file by a specified number of cents using pyrubberband.
    
    Args:
        input_file (str): Path to input audio file
        output_file (str): Path to save the pitch-shifted audio
        cents (float): Number of cents to shift (positive = up, negative = down)
        sr (int, optional): Target sampling rate. If None, uses the input file's rate
    
    Returns:
        tuple: (sampling_rate, shifted_audio)
    """
    # Load the audio file
    filename = os.path.basename(audio_file)
    y, sr_orig = sf.read(audio_file)
    
    # Perform the pitch shift using pyrubberband
    y_shifted = pyrb.pitch_shift(
        y,
        sr_orig,
        semitones
    )
    
    # Save the output
    output_file = os.path.join(config.OUTPUT_DIR, f'{filename}_final.wav')
    sf.write(output_file, y_shifted, sr_orig)
    
    return output_file

def modify_song(audio_file, target_bpm=None, stretch_ratio=None, pitch_shift_semitones=None):
    """
    Modify an audio file by time-stretching and/or pitch-shifting.
    
    Args:
        audio_file (str): Path to the audio file
        target_bpm (float): Target BPM for time-stretching
        stretch_ratio (float): Time-stretching ratio (overrides target_bpm)
        pitch_shift_semitones (float): Number of semitones to pitch-shift
    
    Returns:
        str: Path to the modified audio file
    """
    # Time-stretch the audio file
    if target_bpm:
        stretch_ratio = get_stretch_ratio(audio_file, target_bpm)
        audio_file = time_stretch(audio_file, stretch_ratio)
    if stretch_ratio:
        audio_file = time_stretch(audio_file, stretch_ratio)
    # Pitch-shift the audio file
    if pitch_shift_semitones:
        audio_file = pitch_shift_audio(audio_file, pitch_shift_semitones)
    
    return audio_file
    
if __name__=='__main__':
    print("Downloading audio...")
    # download_audio('https://youtube.com/watch?v=Br3KkvgMAZY')
    download_audio('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    file_id = 'dQw4w9WgXcQ'
    print("Stretching audio...")
    time_stretch(f'{config.OUTPUT_DIR}/{file_id}.wav', 0.8)
    # Plot beats on the waveform
    print("Getting beats...")
    y, sr = sf.read(f'{config.OUTPUT_DIR}/{file_id}_stretched.wav')
    import matplotlib.pyplot as plt

    beats = get_downbeats(f'{config.OUTPUT_DIR}/{file_id}_stretched.wav')
    beat_times = [beat * sr for beat in beats]

    plt.figure(figsize=(14, 5))
    plt.plot(y[:4410000,0], label='Waveform')
    for beat in beat_times:
        if beat < 4410000:
            plt.axvline(x=beat, color='r', linestyle='--', label='Beat')
    
    plt.title('Waveform with Beats (First 4410000 Samples)')
    plt.xlabel('Samples')
    plt.ylabel('Amplitude')
    plt.legend()
    plt.show()

    print("Beats: ", beats)
    # print("Splitting audio files...")
    # print([path for path in split_audio_demucs(f'{config.OUTPUT_DIR}/Br3KkvgMAZY.wav')])
