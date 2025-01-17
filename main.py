import os
import pathlib
import argparse
import subprocess as sp
import numpy as np
from yt_dlp import YoutubeDL
import demucs.api
import madmom
from madmom.features.beats import RNNBeatProcessor, BeatTrackingProcessor
# from audiostretchy.stretch import process_audio
import pyrubberband as pyrb
import soundfile as sf

class AudioProject:
    def __init__() -> None:
        pass

    def download_audio(self, url):
        '''
        Download audio file from youtube using ytdlp
        :param url: str, url of the audio file
        :return: None
        '''
        with YoutubeDL() as ydl:
            ydl.download(url)
        pass

    def split_audio_demucs(self, path_to_file,model='htdemucs_ft',output_path='../resources/tmp'):
        '''
        Split audio file using demucs
        :param audio_file: str, path to audio file
        :return: None
        '''
        # file_name = os.path.basename(path_to_file)
        # sp.run(["python3", "-m", "demucs.separate", "-o", output_path, "-n", model, path_to_file])
        # return os.path.join(output_path, model,file_name[:file_name.find('.')])
        separator = demucs.api.Separator(model=model)
        origin, separated = separator.separate_audio_file(path_to_file)
        return separated

    def get_beats(self, audio_file):
        '''
        Get beats from audio file
        :param audio_file: str, path to audio file
        :return: np.ndarray, beats
        '''
        proc = BeatTrackingProcessor(fps=100)
        act = madmom.features.beats.RNNBeatProcessor()(audio_file)
        self.beats = proc(act)
        return self.beats#proc(act)

    def get_bpm_from_beats(self, beats):
        '''
        Get bpm from beats
        :param beats: np.ndarray, beats
        :return: float, bpm
        '''
        self.bpm = 60.0/np.mean(np.diff(beats))
        return self.bpm

    def time_stretch(self, audio_file, target_bpm=None, stretch_ratio=None):
        '''
        Time stretch audio file to target bpm
        :param audio_file: str, path to audio file
        :param target_bpm: float, target bpm
        :return: str, path to stretched audio file
        '''
        output_dir = '../resources/tmp'
        filename = os.path.basename(audio_file)
        y, sr = sf.read(audio_file)
        output_file = os.path.join(output_dir, filename[:filename.find('.')]+"_stretched.wav")
        if target_bpm is not None:
            stretch_ratio = target_bpm / self.bpm

        stretched_audio = pyrb.time_stretch(y, sr, stretch_ratio)
        # stretched_audio = librosa.effects.time_stretch(y, rate=stretch_ratio)
        sf.write(output_file, stretched_audio, sr)
        return output_file