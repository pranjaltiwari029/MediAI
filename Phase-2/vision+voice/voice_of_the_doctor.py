# Step 1a:Setup text to speech-TTS-model(gTTS )
import os
from gtts import gTTS

# def text_to_speech_with_gtts_old(input_text,output_filepath):
#     language="en"
    
#     audioobj=gTTS(
#         text=input_text,
#         lang=language,
#         slow=False
#     )
#     audioobj.save(output_filepath)
    
# input_text="hello all , Myself Pranjal Tiwari"
# text_to_speech_with_gtts(input_text=input_text,output_filepath="ggts_testing.mp3")


# Step  1b : Stepup text to speech- TTS model with ElevenLabs

import elevenlabs

from elevenlabs.client import ElevenLabs


# def text_to_speech_with_elevenlabs_old(input_text,output_filepath):

#     client=ElevenLabs(api_key=ELEVENLABS_API_KEY)
#     audio=client.generate(
#         text=input_text,
#         voice="Aria",
#         output_format="mp3_22050_32",
#         model="eleven_turbo_v2"
#     )

#     elevenlabs.save(audio,output_filepath)
    
# text_to_speech_with_elevenlabs(input_text,output_filepath="elevenlabs_testing.mp3")

# Step2:Use Model for text output to voice

import subprocess
import platform
from pydub import AudioSegment

# 
def text_to_speech_with_gtts(input_text, output_filepath_mp3):
    language = "en"
    
    # Generate speech and save as MP3
    audioobj = gTTS(
        text=input_text,
        lang=language,
        slow=False
    )
    audioobj.save(output_filepath_mp3)

    # Convert MP3 to WAV (for Windows SoundPlayer)
    output_filepath_wav = output_filepath_mp3.replace(".mp3", ".wav")
    subprocess.run(["ffmpeg", "-i", output_filepath_mp3, output_filepath_wav, "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Detect OS and play the audio
    os_name = platform.system()
    try:
        if os_name == "Darwin":  # macOS
            subprocess.run(['afplay', output_filepath_mp3])
        elif os_name == "Windows":  # Windows (Use WAV file for compatibility)
            subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{output_filepath_wav}").PlaySync();'])
        elif os_name == "Linux":  # Linux
            subprocess.run(['aplay', output_filepath_mp3])  # Alternative: use 'mpg123' or 'ffplay'
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"An error occurred while trying to play the audio: {e}")

# Example usage
input_text = "Hello all, myself Pranjal Tiwari, new version of testing, autoplay to be precise."
# text_to_speech_with_gtts(input_text, "ggts_testing_autoplay.mp3")

# using elevenlabs ( testing -1 )

# def text_to_speech_with_elevenlabs(input_text, output_filepath):
#     client=ElevenLabs(api_key=ELEVENLABS_API_KEY)
#     audio=client.generate(
#         text= input_text,
#         voice= "Aria",
#         output_format= "mp3_22050_32",
#         model= "eleven_turbo_v2"
#     )
#     elevenlabs.save(audio, output_filepath)
#     os_name = platform.system()
#     try:
#         if os_name == "Darwin":  # macOS
#             subprocess.run(['afplay', output_filepath])
#         elif os_name == "Windows":  # Windows
#             subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{output_filepath}").PlaySync();'])
#         elif os_name == "Linux":  # Linux
#             subprocess.run(['aplay', output_filepath])  # Alternative: use 'mpg123' or 'ffplay'
#         else:
#             raise OSError("Unsupported operating system")
#     except Exception as e:
#         print(f"An error occurred while trying to play the audio: {e}")




# def text_to_speech_with_elevenlabs(input_text, output_filepath_mp3):
#     client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
#     # Generate speech and save as MP3
#     audio = client.generate(
#         text=input_text,
#         voice="Aria",
#         output_format="mp3_22050_32",
#         model="eleven_turbo_v2"
#     )
    
#     # Save MP3
#     with open(output_filepath_mp3, "wb") as f:
#         f.write(audio)

#     # Convert MP3 to WAV (Required for Windows)
#     output_filepath_wav = output_filepath_mp3.replace(".mp3", ".wav")
#     subprocess.run(["ffmpeg", "-i", output_filepath_mp3, output_filepath_wav, "-y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#     # Detect OS and play the audio
#     os_name = platform.system()
#     try:
#         if os_name == "Darwin":  # macOS
#             subprocess.run(['afplay', output_filepath_mp3])
#         elif os_name == "Windows":  # Windows (Play WAV file)
#             subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{output_filepath_wav}").PlaySync();'])
#         elif os_name == "Linux":  # Linux
#             subprocess.run(['aplay', output_filepath_mp3])  # Alternative: use 'mpg123' or 'ffplay'
#         else:
#             raise OSError("Unsupported operating system")
#     except Exception as e:
#         print(f"An error occurred while trying to play the audio: {e}")

# # Example usage
# input_text = "Hello, this is a test of ElevenLabs autoplay feature."
# text_to_speech_with_elevenlabs(input_text, "elevenlabs_testing_autoplay.mp3")
# text_to_speech_with_elevenlabs(input_text, output_filepath="elevenlabs_testing_autoplay.mp3")
    
# text_to_speech_with_elevenlabs(input_text,output_filepath="1elevenlabs_testing.mp3")


# testing -3

def text_to_speech_with_elevenlabs(input_text, output_filepath_mp3="final.mp3"):
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    # Generate MP3 speech
    audio = client.generate(
        text=input_text,
        voice="Aria",
        output_format="mp3_22050_32",
        model="eleven_turbo_v2"
    )
    elevenlabs.save(audio, output_filepath_mp3)

    # Convert MP3 to WAV (Windows SoundPlayer requires WAV)
    output_filepath_wav = output_filepath_mp3.replace(".mp3", ".wav")
    sound = AudioSegment.from_mp3(output_filepath_mp3)
    sound.export(output_filepath_wav, format="wav")

    # Detect OS and play the correct file format
    os_name = platform.system()
    try:
        if os_name == "Darwin":  # macOS
            subprocess.run(['afplay', output_filepath_mp3])
        elif os_name == "Windows":  # Use WAV for compatibility
            subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{output_filepath_wav}").PlaySync();'])
        elif os_name == "Linux":  # Linux
            subprocess.run(['aplay', output_filepath_mp3])  # Alternative: 'mpg123' or 'ffplay'
        else:
            raise OSError("Unsupported operating system")
    except Exception as e:
        print(f"An error occurred while trying to play the audio: {e}")

    return output_filepath_wav  # Return the WAV file for further use
