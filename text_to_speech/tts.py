import os
import time
from gtts import gTTS
from utils.config import language_code, sound_src, tmp_dir ,voice_intent, voice_json


# def tts(agi,mytext, callerid, file_name):
#     myobj = gTTS(text=mytext, lang=language_code, slow=False)
#     # myobj.save(sound_src + 'train_data/' +  voice_intent + "/" + file_name + ".mp3")
#     # os.system("sox {}train_data/{}/{}.mp3 -r 8000 -c 1 {}train_data/{}/{}.gsm".format(sound_src, voice_intent, file_name, sound_src, voice_intent, file_name))
#     myobj.save(tmp_dir +callerid +"/" + file_name + ".mp3")
#     os.system("sox {}{}/{}.mp3 -r 8000 -c 1 {}{}/{}.gsm".format(tmp_dir, callerid, file_name, tmp_dir, callerid, file_name))
#     os.system("rm {}{}/{}.mp3".format(tmp_dir, callerid, file_name))


def tts(agi, ssml, callerid, filename):
    """Synthesizes speech from the input string of ssml.
    Note: ssml must be well-formed according to:
        https://www.w3.org/TR/speech-synthesis/
    Example: <speak>Hello there.</speak>
    """
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = voice_json
    from google.cloud import texttospeech
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.types.SynthesisInput(ssml=ssml)
    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().

    # voice = client.list_voices().voices[160]
    # For MALE voice
    # voice = client.list_voices().voices[157]
    voices = client.list_voices()
    for voice in voices.voices:
        if voice.name == "en-US-Standard-B":
            break

    voice = texttospeech.types.VoiceSelectionParams(
        language_code=voice.language_codes[0],
        ssml_gender=voice.ssml_gender)

    audio_config = texttospeech.types.AudioConfig(
        speaking_rate=0.85,
        sample_rate_hertz=8000,
        audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16)
    response = client.synthesize_speech(input_text, voice, audio_config)

    # The response's audio_content is binary.
    with open(tmp_dir + callerid + "/" + filename + '.wav' , 'wb') as out:
        out.write(response.audio_content)
    os.system("sox {}{}/{}.wav -r 8000 -c 1 {}{}/{}.gsm".format(tmp_dir, callerid, filename, tmp_dir, callerid, filename))
    os.system("rm {}{}/{}.wav".format(tmp_dir, callerid, filename))

# def tts(agi, ssml, callerid, filename):
#     """Synthesizes speech from the input string of ssml.
#     Note: ssml must be well-formed according to:
#         https://www.w3.org/TR/speech-synthesis/
#     Example: <speak>Hello there.</speak>
#     """
#     os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = voice_json
#     from google.cloud import texttospeech
#     client = texttospeech.TextToSpeechClient()
#     input_text = texttospeech.types.SynthesisInput(ssml=ssml)
#     # Note: the voice can also be specified by name.
#     # Names of voices can be retrieved with client.list_voices().

#     voice = client.list_voices().voices[160]
#     # For MALE voice
#     # voice = client.list_voices().voices[157]

#     voice = texttospeech.types.VoiceSelectionParams(
#         language_code=voice.language_codes[0],
#         ssml_gender=voice.ssml_gender)

#     audio_config = texttospeech.types.AudioConfig(
#         speaking_rate=0.85,
#         sample_rate_hertz=8000,
#         audio_encoding=texttospeech.enums.AudioEncoding.mp3)
#     response = client.synthesize_speech(input_text, voice, audio_config)

#     # The response's audio_content is binary.
#     with open(tmp_dir + callerid + "/" + filename + '.mp3' , 'wb') as out:
#         out.write(response.audio_content)
#     os.system("sox {}{}/{}.mp3 -r 8000 -c 1 {}{}/{}.gsm".format(tmp_dir, callerid, filename, tmp_dir, callerid, filename))
#     os.system("rm {}{}/{}.mp3".format(tmp_dir, callerid, filename))