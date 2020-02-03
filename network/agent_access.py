import time
import threading

import json
from collections import OrderedDict
from google.cloud import speech_v1p1beta1 as speech
import dialogflow_v2 as yesagent
import dialogflow_v2beta1 as voiceagent
import dialogflow_v2 as dialogflow

from utils.config import language_code, os, accept_project_id, voice_project_id, voice_intent, accept_intent, accept_json, voice_json, sound_src, tmp_dir, agi_src, dir_path, model
from utils.playaudio import Playaudio
from utils.util import userconvwrite, dtmf, stream_record, dtmf_monitor


class AgentAccess():

	def __init__(self):
		self.SAMPLE_RATE_HERTZ = 16000
		self.language_code = language_code
		self.accept_project_id = accept_project_id
		self.voice_project_id = voice_project_id
		self.accept_intent = accept_intent
		self.voice_intent = voice_intent
		self.accept_json = accept_json
		self.voice_json = voice_json
		self.enable_record = True
		self.dtmf_res = ''
		self.model = model
		# self.playaudio = Playaudio()


	def detect_intent_texts(self, agi, session_id, query_text):
		"""Returns the result of detect intent with texts as inputs.
		Using the same `session_id` between requests allows continuation
		of the conversation."""

		session_client = dialogflow.SessionsClient()

		session = session_client.session_path(self.voice_project_id, session_id)

		try:
			# for query in query_text:
			text_input = dialogflow.types.TextInput(
				text=query_text, language_code=self.language_code)

			query_input = dialogflow.types.QueryInput(text=text_input)

			response = session_client.detect_intent(
				session=session, query_input=query_input)

			if response.query_result.fulfillment_text == '[]' or 'Error' in response.webhook_status.message:
				return response.query_result.query_text + '|[]'
			elif not response.query_result.fulfillment_text:
				return response.query_result.query_text + "|['improper']"
			else:
				return response.query_result.query_text + '|'+response.query_result.fulfillment_text

		except Exception as e:
			return " |['empty']"

	def enhanced_STT(self, agi, session_id, audio_file_path):
		"""Transcribe the given audio file synchronously with
		the selected model."""

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
		for i, result in enumerate(response.results):
			query_text += str(result.alternatives[0].transcript)
		result = self.detect_intent_texts(agi, session_id, query_text)
		#     if i%2 == 1:
		#         result += self.detect_intent_texts(session_id, query)
		#         query_text = ''
		# if query_text != '':
		#     result += self.detect_intent_texts(session_id, query)
		return result

	def detect_intent_stream(self, session_id, audio_file_path):
		"""Returns the result of detect intent with streaming audio as input.

		Using the same `session_id` between requests allows continuation
		of the conversation."""

		os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.accept_json

		session_client = yesagent.SessionsClient()

		# Note: hard coding audio_encoding and sample_rate_hertz for simplicity.
		audio_encoding = yesagent.enums.AudioEncoding.AUDIO_ENCODING_LINEAR_16

		session_path = session_client.session_path(self.accept_project_id, session_id)

		def request_generator(audio_config, audio_file_path):
			query_input = yesagent.types.QueryInput(audio_config=audio_config)

			# The first request contains the configuration.
			yield yesagent.types.StreamingDetectIntentRequest(session=session_path, query_input=query_input)

			# Here we are reading small chunks of audio data from a local
			# audio file.  In practice these chunks should come from
			# an audio input device.
			with open(audio_file_path, 'rb') as audio_file:
				while True:
					chunk = audio_file.read(4096)
					if not chunk:
						break
					# The later requests contains audio data.
					yield yesagent.types.StreamingDetectIntentRequest(input_audio=chunk)

		audio_config = yesagent.types.InputAudioConfig(
			audio_encoding=audio_encoding, language_code=self.language_code,
			sample_rate_hertz=self.SAMPLE_RATE_HERTZ)

		requests = request_generator(audio_config, audio_file_path)

		responses = session_client.streaming_detect_intent(requests)

		res = ""
		flag = False
		for response in responses:
			if response.response_id:
				flag = True
				res = response

		if not flag:
			with open(tmp_dir + session_id + '/' + session_id + '_result_acceptance.json', 'w') as Jfile:
				json.dump({"QueryText": response.query_result.query_text}, Jfile)
			return 'empty'
		else:
			if res.query_result.intent.display_name == self.accept_intent:
				# Note: The result from the last response is the final transcript along with the detected content.
				query_result = res.query_result
				if query_result.fulfillment_text == '':
					with open(tmp_dir + session_id + '/' + session_id + '_result_acceptance.json', 'w') as Jfile:
						json.dump({"QueryText": query_result.query_text}, Jfile)
					return {}
				else:
					with open(tmp_dir + session_id + '/' + session_id + '_result_acceptance.json', 'w') as Jfile:
						json.dump(OrderedDict({"QueryText": query_result.query_text, "Result": query_result.fulfillment_text}), Jfile)
					return query_result.fulfillment_text
			else:
				with open(tmp_dir + session_id + '/' + session_id + '_result_acceptance.json', 'w') as Jfile:
					json.dump({"QueryText": res.query_result.query_text}, Jfile)
				return 'improper'

	def detect_intent_streamV2beta1_chunk(self, session_id, audio_file_path):
		"""Returns the result of detect intent as audio file with streaming audio as input.

		Using the same `session_id` between requests allows continuation
		of the conversation."""


		os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.voice_json

		session_client = voiceagent.SessionsClient()

		# Note: hard coding audio_encoding and sample_rate_hertz for simplicity.
		audio_encoding = voiceagent.enums.AudioEncoding.AUDIO_ENCODING_LINEAR_16

		session = session_client.session_path(self.voice_project_id, session_id)

		def request_generator(audio_config, audio_file_path):
			query_input = voiceagent.types.QueryInput(audio_config=audio_config)

			# The first request contains the configuration.
			yield voiceagent.types.StreamingDetectIntentRequest(session=session, query_input=query_input)

			# Here we are reading small chunks of audio data from a local
			# audio file.  In practice these chunks should come from
			# an audio input device.
			with open(audio_file_path, 'rb') as audio_file:
				while True:
					chunk = audio_file.read(4096)
					if not chunk:
						break
					# The later requests contains audio data.
					yield voiceagent.types.StreamingDetectIntentRequest(input_audio=chunk)

		audio_config = voiceagent.types.InputAudioConfig(
			audio_encoding=audio_encoding, language_code=self.language_code,
			sample_rate_hertz=self.SAMPLE_RATE_HERTZ)

		output_audio_config = voiceagent.types.OutputAudioConfig(
			audio_encoding=voiceagent.enums.AudioEncoding.AUDIO_ENCODING_LINEAR_16, sample_rate_hertz=self.SAMPLE_RATE_HERTZ)

		requests = request_generator(audio_config, audio_file_path)

		responses = session_client.streaming_detect_intent(requests)

		res = ""
		flag = False

		for response in responses:
			if response.response_id:
				flag = True
				res = response

		if not flag:
			with open(tmp_dir + session_id + '/' + session_id + '_result.json', 'w') as Jfile:
				json.dump({"QueryText": response.query_result.query_text}, Jfile)
			return response.query_result.query_text+"|['empty']"
		else:
			if res.query_result.intent.display_name == self.voice_intent:
				# Note: The result from the last response is the final transcript along with the detected content.
				query_result = res.query_result
				if query_result.fulfillment_text == '[]' or 'Error' in res.webhook_status.message:
					with open(tmp_dir + session_id + '/' + session_id + '_result.json', 'w') as Jfile:
						json.dump({"QueryText": query_result.query_text}, Jfile)
					return query_result.query_text+'|[]'
				else:
					with open(tmp_dir + session_id + '/' + session_id + '_result.json', 'w') as Jfile:
						json.dump(OrderedDict({"QueryText": query_result.query_text, "Result": query_result.fulfillment_text}), Jfile)

					with open(tmp_dir + session_id + '/' + session_id + '_order_output.wav', 'wb') as out:
						out.write(response.output_audio)

					return query_result.query_text+"|"+query_result.fulfillment_text
			else:
				with open(tmp_dir + session_id + '/' + session_id + '_result.json', 'w') as Jfile:
					json.dump({"QueryText": res.query_result.query_text}, Jfile)
				return res.query_result.query_text+"|['improper']"

	def dflow_response(self, agi, valid_digits, intent_name, caller_id, audio, record_duration):
		'''dflow_response sending input audio to dialogflow agent and getting response

		This function records user audio, converts to 16K sample rate and send to detect_intent_streamV2beta1_chunk for getting response from dialogflow agent

		:param name: intent name to match with intent of the response
		:rtype: str -> string
		'''
		voice_file = str(time.time())

		if intent_name ==  'preparations':
			self.dtmf_res = dtmf(agi, valid_digits, voice_file, intent_name, caller_id, audio)
			file_name = voice_file + '_' +intent_name+'_monitor-in.wav16'
		elif intent_name == 'order_retake':
			self.dtmf_res = dtmf_monitor(agi, valid_digits, voice_file, intent_name, caller_id, audio)
			file_name = voice_file + '_' +intent_name+'_monitor-in.wav16'
		else:
			self.dtmf_res = ''
			if self.enable_record:
				stream_record(agi, voice_file, intent_name, caller_id, audio, record_duration)
				os.system("cp -p {}.wav16 {}/train_data/{}/{}.wav16".format(tmp_dir + caller_id + '/' + voice_file + '_' + intent_name + '_monitor-in', dir_path, intent_name, time.time()))
				file_name = voice_file + '_' +intent_name+'_monitor-in.wav16'

			else:
				file_name = 'addItem/inp.wav16'
				self.enable_record = True

		if self.dtmf_res == '':
			t = threading.Thread( target=Playaudio.holdmusic, args = (agi, 'holdmusic',))
			Playaudio.audioflag = True
			t.start()
			# start = time.time()
			result = self.enhanced_STT(agi, caller_id, tmp_dir + caller_id + '/' + file_name)
			# end = time.time() - start
			Playaudio.audioflag = False
			t.join()
		else:
			result = "|['dummy']"
		return result, self.dtmf_res