import os
from gtts import gTTS
import subprocess
import platform
from pydub import AudioSegment

def text_to_speech_with_gtts(input_text, output_filepath_mp3):
    language = "en"
    audioobj = gTTS(text=input_text, lang=language, slow=False)
    audioobj.save(output_filepath_mp3)

    output_filepath_wav = output_filepath_mp3.replace(".mp3", ".wav")
    subprocess.run(["ffmpeg", "-i", output_filepath_mp3, output_filepath_wav, "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    os_name = platform.system()
    try:
        if os_name == "Darwin":
            subprocess.run(['afplay', output_filepath_mp3])
        elif os_name == "Windows":
            subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{output_filepath_wav}").PlaySync();'])
        elif os_name == "Linux":
            subprocess.run(['aplay', output_filepath_mp3])
    except Exception as e:
        print(f"An error occurred while trying to play the audio: {e}")
