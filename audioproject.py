import os
from pathlib import Path
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
    def __init__(self) -> None:
        pass

    def download_audio(self, url):
        '''
        Download audio file from youtube using ytdlp
        :param url: str, url of the audio file
        :return: None
        '''
        ydl_opts = {
                        'format': 'wav/bestaudio/best',
                        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
                        'postprocessors': [{  # Extract audio using ffmpeg
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'wav',
                        }],
                        'outtmpl': '%(id)s.%(ext)s',
                    }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
        pass

    def split_audio_demucs(self, path_to_file,model='htdemucs_6s',output_path='./resources/tmp'):
        '''
        Split audio file using demucs
        :param audio_file: str, path to audio file
        :return: None
        '''
        sp.run(["python3", "-m", "demucs.separate", "-o", output_path, "-n", model, path_to_file])
        output_dir = Path(output_path) / Path(model)
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

    def get_stretch_ratio(self, audio_file, target_bpm):
        '''
        Get stretch ratio to target bpm
        :param audio_file: str, path to audio file
        :param target_bpm: float, target bpm
        :return: float, stretch ratio
        '''
        y, sr = sf.read(audio_file)
        bpm = self.get_bpm_from_beats(self.get_beats(y))
        return target_bpm/bpm

    def time_stretch(self, audio_file, stretch_ratio=1):
        '''
        Time stretch audio file to target bpm
        :param audio_file: str, path to audio file
        :param target_bpm: float, target bpm
        :return: str, path to stretched audio file
        '''
        output_dir = './resources/tmp'
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(audio_file)
        y, sr = sf.read(audio_file)
        output_file = os.path.join(output_dir, filename[:filename.find('.')]+"_stretched.wav")
        stretched_audio = pyrb.time_stretch(y, sr, stretch_ratio)
        # stretched_audio = librosa.effects.time_stretch(y, rate=stretch_ratio)
        sf.write(output_file, stretched_audio, sr)
        return output_file
    
if __name__=='__main__':
    project = AudioProject()
    print("Downloading audio...")
    project.download_audio('https://youtube.com/watch?v=Br3KkvgMAZY')
    print("Stretching audio...")
    project.time_stretch('Br3KkvgMAZY.wav', 0.8)
    # print("Getting beats...")
    # print("Beats: ",project.get_beats('Br3KkvgMAZY.wav'))
    print("Splitting audio files...")
    print([path for path in project.split_audio_demucs('Br3KkvgMAZY.wav')])
