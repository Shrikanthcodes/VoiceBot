import speech_recognition as sr
import time
import datetime
import os
import threading
from google.cloud import speech_v1p1beta1 as speech

from utils.config import sound_src, tmp_dir, dir_path, model, voice_json
from utils.playaudio import Playaudio
from utils.util import userconvwrite, dtmf, stream_record
#AUDIO_FILE = ('example.wav')

class STT():
	def __init__(self):
		self.s_result = { 'yes', 's', 'ss', 'yess', 'yeah', 'yep', 'yup', 'yah', 'ya', 'confirm', 'proceed' }
		self.no_result = {'no', 'nope', 'nah', 'nada', 'know', 'cancel', 'remove', 'delete', 'nothing' }
		self.reorder = {'reorder','re-order'}
		self.negatives = {'dont', 'donot', 'doesnot', 'not', 'didnot'}
		self.quantity = {1:{'1','one','won'}, 2:{'2','two','too'}, 3:{'3','three','tree','free'}, 4 :{'4','four','for'}, 5:{'5','five'}, 6:{'6','six'}, 7:{'7',' seven'}, 8:{'8','eight'}, 9:{'9','nine'}, 10:{'10','ten,in'}, 11:{'11','eleven'}, 12:{'12','twelve'}, 13:{'13','thirteen'}, 14:{'14','fourteen'}, 15:{'15','fifteen'}, 16:{'16','sixteen'}, 17:{'17','seventeen'}, 18:{'18','eighteen'}, 19:{'19','nineteen'}, 20:{'20','twenty'}}
		self.custom =  {'Very Mild Spice':{'1','one','won'}, 'Mild Spice':{'2','two','too', 'to'},'Medium Spicy':{'3','three','tree','free'},  'Spicy':{'4','four','for'}, 'Extra Spice':{'5','five'}}
		self.error = {'error'}
		self.empty = {'empty'}
		self.dtmf_res = ''
		self.model = model
		self.SAMPLE_RATE_HERTZ = 16000
		self.voice_json = voice_json

	def stt_recognize(self, session_id, audio_file_path):
		os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.voice_json

		client = speech.SpeechClient()

		with open(audio_file_path, 'rb') as audio_file:
			content = audio_file.read()

		audio = speech.types.RecognitionAudio(content=content)

		config = speech.types.RecognitionConfig(
			encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
			sample_rate_hertz=self.SAMPLE_RATE_HERTZ,
			language_code='en-US',
			use_enhanced=True,
			model=self.model)

		response = client.recognize(config, audio)

		query = []
		result = []
		query_text = ''
		
		try:
			for i, result in enumerate(response.results):
				query_text += str(result.alternatives[0].transcript)
			return query_text
		except Exception as e:
			with open ('stt_log.txt', 'a') as f:
				f.write(datetime.datetime.now().strftime('%d:%b:%Y:%H:%M:%S')+' ----> '+str(e)+'\n')
			return 'error'

	
	# def opensource_recognizer(self,  AUDIO_FILE):
	#     r = sr.Recognizer()
	#     with sr.AudioFile(AUDIO_FILE) as source:
	#         audio = r.record(source)
	#     try:
	#         return r.recognize_google(audio)
	#     except sr.UnknownValueError:
	#         return 'empty'
	#     except sr.RequestError as e:
	#         return 'error'

	def acceptancemapping(self, split_result):
		return ( 'YES' if split_result.intersection(self.s_result)  else ('NO' if split_result.intersection(self.no_result) else ('REORDER' if split_result.intersection(self.reorder) else ('ERROR' if split_result.intersection(self.error) else('EMPTY' if split_result.intersection(self.empty)  else split_result)))))

	def final_confirmation(self, sentence):
		sentence = sentence.replace('\'', '')
		sentence = sentence.replace(',', '')
		sentence_copy = sentence

		result = 'EMPTY'
		for s in self.s_result:
			if s in sentence.split():
				result = 'YES'
				sentence = sentence[sentence.index(s)+len(s):]
				break

		for no in self.no_result:
			if no in sentence.split():
				result = 'NO'
				sentence = sentence[sentence.index(no)+len(no):]
				break

		for re in self.reorder:
			if re in sentence.split():
				return 'REORDER'

		for neg in self.negatives:
			if neg in sentence_copy.split():
				if result == 'YES':
					return 'NO'
				else:
					return 'YES'

		return result


	def quantitymapping(self, result, split_result):
		if result != 'error' and result != 'empty':
			for key, value in self.quantity.items():
				if split_result.intersection(value):
					return key
		return ''


	def custommapping(self, result, split_result):
		if result != 'error' and result != 'empty':
			for key, value in self.custom.items():
				if split_result.intersection(value):
					return key
		return ''

	def packagemapping(self, result, split_result, data):
		data = [x.lower().split() for x in data]
		if result != 'error' and result != 'empty':
			return [value for value in data if set(value).intersection(split_result)]
		return ''

	def press_say(self, intent_name, dtmf_res, result, split_result):
		if intent_name == 'ivr':
			result = str(self.quantitymapping(result, split_result))
		elif intent_name == 'custom':
			dtmf_res = (self.custommapping(dtmf_res, set(dtmf_res)) if dtmf_res != '' else dtmf_res)
			result = self.custommapping(result, split_result)
		if dtmf_res == '' and result == '' :
			return ''
		else:
			return (dtmf_res if dtmf_res != '' else (result if result != '' else ''))

	def speechtotext(self, agi, valid_digits, intent_name, caller_id, audio, record_duration, data):

		voice_file = str(time.time())

		if not (intent_name == 'ivr' or intent_name == 'custom'):
			stream_record(agi, voice_file, intent_name, caller_id, audio, record_duration)
			os.system("cp -p {}.wav16 {}/train_data/{}/{}.wav16".format(tmp_dir + caller_id + '/' + voice_file + '_' + intent_name + '_monitor-in', dir_path, intent_name, time.time()))
		else:
			self.dtmf_res = dtmf(agi, valid_digits, voice_file, intent_name, caller_id, audio)

		if self.dtmf_res == '':
			t = threading.Thread( target=Playaudio.holdmusic, args = (agi, 'holdmusic', ))
			Playaudio.audioflag = True
			t.start()
			result = self.stt_recognize(caller_id, tmp_dir + caller_id + '/' + voice_file + '_' + intent_name + '_monitor-in.wav16')
			# result = self.opensource_recognizer(tmp_dir + caller_id + '/' + voice_file + '_' + intent_name + '_monitor-in.wav16')
			Playaudio.audioflag = False
			t.join()
		else:
			result = 'empty'


		split_result = set(result.lower().split())

		if intent_name == 'YesorNo':
			output = ''.join(self.acceptancemapping(split_result))
			userconvwrite(caller_id,'customer',result)
			return voice_file,len(split_result), output
		elif intent_name == 'quantity':
			output = self.quantitymapping(result, split_result)
		elif intent_name == 'custom' or intent_name == 'ivr':
			output =  self.press_say(intent_name, self.dtmf_res, result, split_result)
			self.dtmf_res = ''
		elif intent_name == 'final_confirm':
			output = self.final_confirmation(result)
		elif intent_name == 'package':
			output = self.packagemapping(result, split_result, data)
		else:
			output = result
		userconvwrite(caller_id,'customer',output)
		return output
