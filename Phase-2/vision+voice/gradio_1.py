# UI with gradio
import os
import gradio as gr

from brain import encode_image, analyze_image_with_query
from voice_of_the_patient import record_audio, transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts, text_to_speech_with_elevenlabs
from db_utils import init_db, save_to_db  


# ✅ System prompt to guide the doctor model
system_prompt = """You have to act as a professional doctor, i know you are not but this is for learning purpose. 
            What's in this image?. Do you find anything wrong with it medically? 
            If you make a differential, suggest some remedies for them. Donot add any numbers or special characters in 
            your response. Your response should be in one long paragraph. Also always answer as if you are answering to a real person.
            Donot say 'In the image I see' but say 'With what I see, I think you have ....'
            Dont respond as an AI model in markdown, your answer should mimic that of an actual doctor not an AI bot, 
            Keep your answer concise (max 2 sentences). No preamble, start your answer right away please"""

# ✅ Initialize the database
init_db()

def process_inputs(audio_filepath, image_filepath):
    # Step 1: Transcribe speech
    speech_to_text_output = transcribe_with_groq(
        GROQ_API_KEY=GROQ_API_KEY, 
        audio_filepath=audio_filepath,
        stt_model="whisper-large-v3"
    )

    # Step 2: Analyze image with transcribed text
    if image_filepath:
        doctor_response = analyze_image_with_query(
            query=system_prompt + speech_to_text_output,
            encoded_image=encode_image(image_filepath),
            model="meta-llama/llama-4-scout-17b-16e-instruct"
            
        )
    else:
        doctor_response = "No image provided for analysis."

    # Step 3: Convert response to voice using gTTS
    voice_of_doctor = text_to_speech_with_gtts(input_text=doctor_response, output_filepath_mp3="doctor_response.mp3")

    # ✅ Step 4: Save interaction to database with image path
    save_to_db(speech_to_text_output, doctor_response, image_filepath)


    return speech_to_text_output, doctor_response, voice_of_doctor

# Create the interface
iface = gr.Interface(
    fn=process_inputs,
    inputs=[
        gr.Audio(sources=["microphone"], type="filepath"),
        gr.Image(type="filepath")
    ],
    outputs=[
        gr.Textbox(label="Speech to Text"),
        gr.Textbox(label="Doctor's Response"),
        gr.Audio("Temp.mp3")
    ],
    title="Medical AI Assistant "
)

iface.launch(debug=True)
