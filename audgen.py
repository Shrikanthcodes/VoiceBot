from google.cloud import texttospeech
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "My First Project-2e1b0d351e36.json"

#wav_path = ''
gsm_path = '/home/priya/Downloads/v5/v4/train_data/'

#message is obtained from /home/AudioText
def timeaudio():
    textdata = open(r"/home/priya/Public/AudioText","r")
    text = textdata.readlines()
    text = str(text[0])

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.types.SynthesisInput(text = text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voices = client.list_voices()
    for voice in voices.voices:
        if voice.name == "en-US-Standard-B":
            break
    voice = texttospeech.types.VoiceSelectionParams(
            language_code=voice.language_codes[0],
            ssml_gender=voice.ssml_gender)

    # Select the type of audio file you want returned
    audio_config = texttospeech.types.AudioConfig(
            speaking_rate=0.85,
            sample_rate_hertz=8000,
            audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)
        
    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(synthesis_input, voice, audio_config)

    # The response's audio_content is binary.
    with open('output.wav', 'wb') as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file "closed.gsm"')
    #def sox_convert(wav_path, gsm_path):
        #os.system("sox {}.wav -r 8000 -c 1 {}.gsm".format(wav_path, gsm_path))
        #os.system("rm {}.wav".format(wav_path))
    #sox_convert('output', gsm_path + 'closed')
timeaudio()

