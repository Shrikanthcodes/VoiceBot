from network.agent_access import AgentAccess
from utils.config import sound_src, tmp_dir, voice_intent, accept_intent
from utils.util import dtmf
from speech_to_text.stt import STT
import os
from utils.util import result_split, result_conversion, resultkey_delete, userconvwrite, create_audio, stream_audio

class Data():
	"""This is a class for defining data 	"""
	caller_id = ''
	dflow_record_duration = 50
	stt_record_duration = 20
	valid_digits = 1
	audio = "welcome_press"
	checkjson = False
	agent_access = AgentAccess()
	stt = STT()

class ASR():
	"""This is a class for handling all operations, returning solution used for decision making

	:return: Result needed for that specific scenario
	:rtype: list
	"""
	def __init__(self):
		"""The constructor for ASR class"""
		self.count = 0

	def convert_lower(self, result):
		for res in result:
			res['food_item'] = res['food_item'].lower()
			res['modifier'][0] = res['modifier'][0].lower()
		return result

	def normalize(self, result):
		"""This method responsible for normalizing the input data, remove duplicates and unnecessary data

		:param result: Input data(user specified food order structured from dialogflow)
		:type result: List
		:return: Normalized data
		:rtype: List
		"""
		length = len(result)
		for i in range(length-1):
			for j in range(i+1,length):
				if result[i]['food_item'] == result[j]['food_item'] and result[i]['modifier'][0] == result[j]['modifier'][0]:
					if result[j]['modifier'][0] != '':
						result[i]['quantity'] += result[j]['quantity']
						result[i]['modifier'] += result[j]['modifier'][1:]
						if result[j]['custom'] != '':
							if result[i]['custom'] != '':
								result[i]['custom'] += result[j]['custom']
							else:
								result[i]['custom'] = result[j]['custom']
						if result[j]['package'] != '':
							if result[i]['package'] != '':
								result[i]['package'] += result[j]['package']
							else:
								result[i]['package'] = result[j]['package']
					result[j]['food_item'] = ''
		return [res for res in result if res['food_item'] != '']

	def checkfooditem(self, agi, food_item, data):
		for i in data:
			agi.verbose(i, len(i))
		if food_item in data:
			return True
		else:
			userconvwrite(Data.caller_id,"system", food_item+'--->'+'food item not in the list')
			Data.checkjson = True
			return False

	def checkmodifier(self, food_item, modifier, data):
		if modifier in data:
			return True
		else:
			userconvwrite(Data.caller_id,"system", modifier+'--->'+'modifier not in the list')
			Data.checkjson = True
			return False

	# def audio_update(self, intent_name):
	# 	if intent_name == 'quantity':
	# 		Data.audio = 'quantity_repeat'
	# 	elif intent_name == 'package':
	# 		Data.audio = 'preparations/pack_repeat'
	# 	else:
	# 		Data.audio = 'repeat_option'

	def stt_request(self, agi, intent_name, maxcount, data):
		"""The method handles STT request

		:param agi: agi object
		:type agi: instance of a class
		:param intent_name: Specifies which type of data needed from STT(ex:quantity, custom)
		:type intent_name: str
		:param maxcount: Specifies Maximum Tries
		:type maxcount: int
		:param data: Input Data fetched from json
		:type data: list
		:return: list -> when we attain a solution or str -> Empty string
		:rtype: list or str
		"""
		self.count = 0
		while True:
			result  = Data.stt.speechtotext(agi, Data.valid_digits, intent_name, Data.caller_id, Data.audio, Data.stt_record_duration, data)
			if result == 'EMPTY' or result == '' or result == []:
				# self.audio_update(intent_name)
				self.count += 1
				if self.count == maxcount:
					return ''
			else:
				return result

	def item(self, agi, maxcount, flag, intent_name):
		"""This method hits Dialogflow

		:param agi: AGI object
		:type agi: instance of a class
		:param maxcount: Maximum tries allowed
		:type maxcount: int
		:param flag: Variable used to whether process the result or to return the result as it is
		:type flag: Boolean
		:return: list -> when we attain a solution or str -> Empty string
		:rtype: list or str
		"""
		self.count = 0
		while True :
			result, dtmf_res = Data.agent_access.dflow_response(agi, Data.valid_digits, intent_name, Data.caller_id,  Data.audio, Data.dflow_record_duration)
			if flag:
				return result, dtmf_res
			query_text, result = result_split(Data.caller_id, result)
			if result == ['empty'] or result ==  ['improper'] or result == [] or result == ['empty_audio']:
				Data.audio = 'repeat_order'
				self.count += 1
				if self.count == maxcount:
					return '', query_text
			else:
				return result_conversion(result), query_text


#ADD ON item cofirmation(using voice input)
	# def addonConfirmation(self, agi):
	# 	"""This method checks user's preferences when asking add on

	# 	:param agi: AGI object
	# 	:type agi: instance of a class
	# 	:return: timestamp and users'preference
	# 	:rtype: str
	# 	"""
	# 	self.count = 0
	# 	while True :
	# 		voice_file, len_result, yesorno = Data.stt.speechtotext(agi, Data.valid_digits, accept_intent, Data.caller_id, Data.audio, Data.stt_record_duration, '')
	# 		if yesorno == 'NO':
	# 			return "", ""
	# 		elif yesorno == 'YES':
	# 			if len_result > 1:
	# 				return voice_file, "skip_recording"
	# 			else:
	# 				return "", "record_input"
	# 		else:
	# 			if self.count <= 2:
	# 				self.count += 1
	# 			else:
	# 				return "",""
	# 			if yesorno == 'EMPTY' or yesorno == 'ERROR':
	# 				Data.audio = 'repeat_yorn'
	# 			else:
	# 				return voice_file, "hit_dflowonce"

	# def addonItem(self, agi):
	# 	"""This method proceeds with user's preference decides whether to hit dflow or not

	# 	:param agi: AGI class object
	# 	:type agi: instance of a class
	# 	:return: result or empty string
	# 	:rtype: list or str
	# 	"""
	# 	while True:
	# 		voice_file, yesorno = self.addonConfirmation(agi)
	# 		if yesorno == "":
	# 			return ""
	# 		elif yesorno == 'skip_recording':
	# 			os.system("cp -p {}.wav16 {}addItem/inp.wav16".format(tmp_dir + Data.caller_id + '/' + voice_file + '_' + 'YesorNo' + '_input', tmp_dir + Data.caller_id + '/'  ))
	# 			Data.agent_access.enable_record = False
	# 			result  = self.item(agi, 2, False, voice_intent)
	# 			result = self.convert_lower(resultkey_delete(result))
	# 			return result
	# 		elif yesorno == 'record_input':
	# 			Data.audio = 'addon_query'
	# 			result  = self.item(agi, 2, False, voice_intent)
	# 			result = self.convert_lower(resultkey_delete(result))
	# 			return result
	# 		elif yesorno == 'hit_dflowonce':
	# 			os.system("cp -p {}.wav16 {}addItem/inp.wav16".format(tmp_dir + Data.caller_id + '/' + voice_file + '_' + 'YesorNo' + '_input', tmp_dir + Data.caller_id + '/'  ))
	# 			Data.agent_access.enable_record = False
	# 			result  = self.item(agi, 1, False, voice_intent)
	# 			if result != '':
	# 				if 'result' in result[-1].keys():
	# 					if result[-1]['result'] == 'NO':
	# 						return ''
	# 					elif result[-1]['result'] == 'YES':
	# 						if len(result) == 1:
	# 							Data.audio = 'addon_query'
	# 							result  = self.item(agi, 2, False, voice_intent)
	# 							result = self.convert_lower(resultkey_delete(result))
	# 							return result
	# 						result = self.convert_lower(resultkey_delete(result))
	# 						return result
	# 				elif len(result) != 0 :
	# 					return self.convert_lower(result)
	# 			return ''

#Add On process using pressed input

	def addonConfirmation(self, agi):
		for i in range(3):
			dtmf_res = dtmf(agi, Data.valid_digits, accept_intent, Data.caller_id, Data.audio)
			userconvwrite(Data.caller_id, 'customer', 'pressed-> '+str(dtmf_res))
			if dtmf_res == str(1):
				Data.audio = 'order_place_beep'
				return 'proceed'
			elif dtmf_res == str(2):
				return 'cancel'
			elif dtmf_res == '' :
				if i != 2:
					Data.audio = 'press_option'
					agi.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
					Data.audio = 'invalid_anything_else'
			else:
				if i != 2:
					Data.audio = 'invalid_option'
					agi.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
					Data.audio = 'invalid_anything_else'
		return ''
	def addonItem(self, agi):
		user_preference = self.addonConfirmation(agi)
		if user_preference == 'proceed':
			result, query_text  = self.item(agi, 2, False, voice_intent)
			if result!= '':
				result = self.convert_lower(resultkey_delete(result))
			return result, query_text
		elif user_preference == 'cancel':
			return 'cancel', ''
		else:
			return user_preference, ''



	# def quantityWithConflict_resolved(self, agi, food_name):
	# 	"""This method collects quantity information from the user

	# 	:param agi: AGI class object
	# 	:type agi: instance of a class
	# 	:param food_name: Name of a food to which quantity information needed
	# 	:type food_name: str
	# 	:return: quantity data
	# 	:rtype: int
	# 	"""

	# 	food_name = food_name.lower().replace(' ', '')
	# 	Data.audio = 'quantity/' + food_name
	# 	total = 0

	# 	while True:
	# 		result = self.stt_request(agi, 'quantity', 2, '')
	# 		len_result = len(str(result))
	# 		if result != '':
	# 			if len_result > 1:
	# 				total += 1
	# 				if total == 2:
	# 					return result
	# 				create_audio(agi, Data.caller_id, 'Please confirm quantity detail' + ' ' + str(result)[0] +'or' + str(result), 'quantity_confirmation')
	# 				stream_audio(agi, Data.caller_id, 'Please confirm quantity detail' + ' ' + str(result)[0] +'or' + str(result), 'quantity_confirmation')
	# 				Data.audio = 'confirm'
	# 			else:
	# 				return result
	# 		else:
	# 			return result

	def quantity(self, agi, food_name):
		"""This method collects quantity information from the user

		:param agi: AGI class object
		:type agi: instance of a class
		:param food_name: Name of a food to which quantity information needed
		:type food_name: str
		:return: quantity data
		:rtype: int
		"""

		food_name = food_name.lower().replace(' ', '')
		Data.audio = 'quantity/' + food_name
		agi.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
		Data.audio = 'quantity_press'
		for i in range(2):
			dtmf_res = dtmf(agi, 2, 'quantity', Data.caller_id, Data.audio)
			userconvwrite(Data.caller_id, 'customer', 'pressed-> '+str(dtmf_res))
			if len(dtmf_res) == 2:
				return ''
			elif dtmf_res == '':
				Data.audio = 'quantity_press'
			elif int(dtmf_res) in range(10) and int(dtmf_res) !=0 :
				return dtmf_res
			else:
				Data.audio = 'invalid_option'
				agi.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
				Data.audio = 'quantity_press'
		return ''

	def modifier(self, agi, food_name):
		"""This method used to get food item for modifier from user

		:param food_name: specifies the food category to which modifier needed
		:type food_name: str
		:return: result got from dflow or empty string
		:rtype: list or str
		"""

		food_name = food_name.lower().replace(' ', '')
		Data.audio = 'modifier/' + food_name
		for i in range (2):
			result, query_text = self.item(agi, 1, False, voice_intent)
			result = resultkey_delete(result)
			if result == '' or result == []:
				Data.audio = 'repeat_option'
			else:
				if result[0]['modifier'][0] != '':
					return self.convert_lower(result)
				else:
					Data.audio = 'repeat_option'
		return ''

	def preparation(self, agi, funcname, food_name, data):
		"""This method decides which preparation function going to trigger

		:param agi: AGI class object
		:type agi: instance of a class
		:param funcname: Preparation label (ex: SPicy level or Complementary)
		:type funcname: str
		:param food_name: Name of a food for which we need preparation data
		:type food_name: str
		:param data: Data contains particular content for the preparation
		:type data: list
		:param code: Code got from CMS for that preparation
		:type code: str
		:param payload:initial user ordered food list
		:type payload: list
		:return: result list contains preparation information or empty string
		:rtype: list or str
		"""

		food_name = food_name.lower().replace(' ', '')
		funcname = funcname.lower().replace(' ', '')
		Data.audio = 'preparations/'+ funcname+'/' + food_name
		data = sorted(data)

		#press only
		for i in range(3):
			dtmf_res = dtmf(agi, Data.valid_digits, 'preparations', Data.caller_id, Data.audio)
			userconvwrite(Data.caller_id, 'customer', 'pressed-> '+str(dtmf_res))
			if dtmf_res != '':
				dtmf_res = int(dtmf_res)
				value = (data[dtmf_res-1] if dtmf_res in range(len(data)+1) and dtmf_res != 0 else '')
				if value != '':
					if funcname == 'complementary':
						if value == 'Not Required':
							value = '  Rice'
						value = ['With' + value.replace('With', '')]
						return value
					return [value]
				else:
					if i != 2:
						Data.audio = 'invalid_option'
						agi.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
						Data.audio = 'preparations/'+ funcname+'/' + 'invalid_option'
			elif dtmf_res == '':
				if i != 2:
					Data.audio = 'press_option'
					agi.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
					Data.audio = 'preparations/'+ funcname+'/' + 'invalid_option'
		return ''

		# press or say
		# return_result = []
		# for i in range (2):
		# 	result, dtmf_res = Data.agent_access.dflow_response(agi, Data.valid_digits, 'preparations', Data.caller_id, Data.audio, Data.dflow_record_duration)
		# 	userconvwrite(Data.caller_id, 'customer', 'pressed-> '+str(dtmf_res))
		# 	query_text, result = result_split(Data.caller_id, result)
		# 	result = resultkey_delete(result)
		# 	if dtmf_res == '' and result == '':
		# 		return ''
		# 	elif dtmf_res != '':
		# 		dtmf_res = int(dtmf_res)
		# 		value = (data[dtmf_res-1] if dtmf_res in range(len(data)+1) and dtmf_res != 0 else '')
		# 		return [value] if value != '' else ''
		# 	elif result == ['empty'] or result ==  ['improper'] or result == [] or result == ['empty_audio'] or result == ['dummy']:
		# 		Data.audio = 'preparations/'+ funcname+'_repeat'
		# 		if i == 1:
		# 			return ''
		# 	elif result != '':
		# 		result = self.convert_lower(result)
		# 		for res in result:
		# 			res['modifier'] = [x for x in res['modifier'] if x]
		# 			return_result.extend(res['modifier'])
		# 		return return_result

		# 	else:
		# 		return ''
