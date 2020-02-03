#!/usr/bin/env python3.5
import time
import os
import json
import threading

from asterisk.agi import *
from text_to_speech.tts import tts
from utils.util import folder_create, ListOfDict, userconvwrite, rename, create_audio, stream_audio, result_split, result_conversion, resultkey_delete, mixmonitor, food_list, preparation_check, dtmf, package_check, check
from utils.config import sound_src, tmp_dir, os, voice_intent, accept_intent, dir_path
from analytics.analytics import store, post, postthread, update, parse, namepostthread, setname, callforward, setname_initial
from asr import ASR, Data
from utils.playaudio import Playaudio
from Timings import *


class preparation:
	"""This class contains all Preparation data
	"""
	food_list = food_list()
	popupcount = 0
	popupcodelist=[]
	popuplist=[]
	spicelevel=""
	package=""
	askedmodifier=False
	askedpackage=False
	askedquantity=False


	@classmethod
	def update(cls,a,value):
		"""This method upates the value to that specific class variables

		:param a: Name of class variable
		:type a: str
		:param value: Updating value fetched from json
		:type value: str
		"""
		if (a=="popupcount"):
			if value:
				cls.popupcount = value
			else:
				pass
		elif(a=="popupcodelist"):
			if value:
				cls.popupcodelist += value
			else:
				pass
		elif(a=="popuplist"):
			if value:
				cls.popuplist.append(value)
			else:
				pass

	def __init__(self, a, value):
		"""This is constructor for preparation class

		:param a: This variable contains name of which value has to change
		:type a: str
		:param value: Fetched value from json
		:type value: str
		"""
		self.value = value
		self.update(a, value)

def parse_data(food_item,modifier):
	m_popupcode=(preparation.food_list["food_items"]["{}".format(food_item)]["{}".format(modifier)]["preperations"])
	preparation("popupcodelist",m_popupcode)
	for i,preparelist in enumerate(m_popupcode):
		preparation("popuplist",preparation.food_list["preperations"]["{}".format(preparelist)]["name"])

class agiDriver():
	"""This class responsible for handling entire logic
	"""

	def __init__(self, agi):
		self.agi_pass = agi
		self.asr = ASR()
		self.value_json= []
		self.SESSION_LIMIT = 2
		self.empty = 0
		self.improper = 0
		self.brace = 0
		self.ivrAny = 0
		self.ivrEmpty = 0
		self.conflict_itemname = 0
		self.addanythingflag = True
		self.addanythingcount = 1
		self.proceed = True
		self.user_response = '$$$$'
		self.get_callername = True
		self.handle_dtmf = False
		self.sample_query = ["i want to order some food", "i want to order something", "i want to order one", "order some food", "order something", "order some veg food", "order some non-veg food"]
		self.query_text = ""



	def clearCtr(self):
		"""This method clears all ctr variable
		"""
		self.empty = self.improper = self.brace = 0

	def clearIvrCtr(self):
		"""This method responsible for ivr routing variables
		"""
		self.ivrEmpty = self.ivrAny = 0

	def sessionCheck(self):
		"""This method decides whether application have to give another chance to the user

		:return: [description]
		:rtype: [type]
		"""
		return self.empty != self.SESSION_LIMIT and self.improper != self.SESSION_LIMIT and self.brace != self.SESSION_LIMIT and self.conflict_itemname != self.SESSION_LIMIT

	def clear_preparationValue(self):
		"""This mehod usage is to clear all the preparation class variables
		"""
		preparation.popupcount = 0
		preparation.popupcodelist=[]
		preparation.popuplist=[]
		preparation.askedmodifier=False
		preparation.askedpackage=False
		preparation.askedquantity=False



	def remove_empty(self):
		checklist = [value for value in store.foodlistinitial if value != 'empty']
		if len(checklist):
			return True
		else:
			return False




	def human_route(self, audio):
		"""This method handles call forwarding to another responsibile person

		:return: string
		:rtype: str
		"""
		#self.agi_pass.verbose("query------------------->", self.query_text)
		callforward(self.agi_pass, store.foodlistinitial, self.query_text)
		self.agi_pass.verbose("query------------------->", self.query_text)
		self.proceed = False
		Data.audio = audio
		userconvwrite(Data.caller_id,"system", str(Data.audio).split('/')[-1])
		self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
		self.agi_pass.appexec('DIAL', 'SIP/9606@34.67.248.168:60281,,m(default)')
		rename(Data.caller_id)
		self.agi_pass.stream_file(sound_src + 'call_disconnect', escape_digits='', sample_offset=0)
		self.agi_pass.hangup()
		return 'session closed'

	def proper_placed(self):
		'''proper_placed Order Confirmation upon collecting order info

		proper_placed() function confirms your order. It also provides option to cancel order.

		:return: final response
		:rtype: str -> string
		'''
		if self.proceed == True:
			self.proceed = False
			t = threading.Thread(target = post, args= (self.agi_pass, 'cost', ))
			t.start()
			create_audio(self.agi_pass, Data.caller_id, ListOfDict(self.agi_pass, store.foodlistfinal), 'order_details')
			stream_audio(self.agi_pass, Data.caller_id, ListOfDict(self.agi_pass, store.foodlistfinal),'order_details')
			t.join()
			stream_audio(self.agi_pass, Data.caller_id, store.cost, 'cost')


		for i in range(2):
			dtmf_res = dtmf(self.agi_pass, Data.valid_digits, 'final_confirm', Data.caller_id, Data.audio)
			userconvwrite(Data.caller_id, 'customer', 'pressed-> '+str(dtmf_res))
			if dtmf_res == str(1):
				Data.audio = 'order_confirmed'
				self.user_response = 'YES'
				return 'YES'
			elif dtmf_res == str(2):
				Data.audio = 'order_cancel'
				self.user_response = 'NO'
				return 'NO'
			elif dtmf_res == str(3):
				Data.audio = 'press1234'
				self.user_response = 'REORDER'
				self.proceed = False
				return 'REORDER'
			elif dtmf_res == '':
				Data.audio = 'press_option'
				self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
				Data.audio = 'press_yes_no'
			else:
				Data.audio = 'invalid_option'
				self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
				Data.audio = 'press_yes_no'
		self.user_response = 'NO'
		return 'NO'

	def final(self, data):
		"""This method stores final payload and route to final confirmation

		:param payload: final entry in food list
		:type payload: dict
		:return: final order confiramtion(Yes/ No)
		:rtype: str
		"""
		if not Data.checkjson:
			store("foodlistfinal",data)
		# store("foodlistfinal",data)
		# Data.audio = "say_yes_no"
		Data.audio = 'press_yes_no'
		return self.proper_placed()


	def initial(self, intent_name):
		'''initial handling dialogflow agent response

		initial() routes control flow according to user response

		:return: Final response from dialogflow agent
		:rtype: str -> string
		'''

		store.foodlistinitial = []
		store.foodlistfinal = []
		result, dtmf_res = self.asr.item(self.agi_pass, 1, True, intent_name)
		self.query_text, result = result_split(Data.caller_id, result)
		

		if dtmf_res == str(0):
			userconvwrite(Data.caller_id, 'customer', 'pressed-> '+str(dtmf_res))
			return self.human_route('connecting_manager')
		elif result == []:
			self.empty += 1
			Data.audio = 'repeat_order'
			if self.query_text.lower() in self.sample_query and self.empty == 1:
				Data.audio = 'food_query'
		elif result == ['empty'] or result == ['improper'] or result == ['empty_audio'] :
			self.empty += 1
			Data.audio = 'repeat_order'
		else:
			self.clearCtr()
			result_lower = self.asr.convert_lower(self.asr.normalize(resultkey_delete(result_conversion(result))))
			store("foodlistinitial",result_lower)
			payload = store.initialdata(store).copy()
			self.agi_pass.verbose(">>>>>>>>>>>>>>Payload", payload)
			payload_limit = len(payload)

			if result_lower != []:
				for i_count, entry in enumerate(payload):
					self.clear_preparationValue()
					if entry["food_item"]:
						self.agi_pass.verbose(">>>>>>entry", entry["food_item"])
						self.agi_pass.verbose(">>>>>>entry len", len(entry["food_item"]))
						if self.asr.checkfooditem(self.agi_pass,entry["food_item"], preparation.food_list['food_items'].keys()):
							if entry["modifier"][0] == "":
								result=self.asr.modifier(self.agi_pass, entry['food_item'])
								if result == '':
									self.human_route('call_forwarding')
								else:
									entry["modifier"][0] = result[0]['modifier'][0]
									if self.asr.checkmodifier(entry["food_item"], entry["modifier"][0], preparation.food_list['food_items'][entry["food_item"]]):
										preparation.askedmodifier=True
							else:
								if self.asr.checkmodifier(entry["food_item"], entry["modifier"][0], preparation.food_list['food_items'][entry["food_item"]]):
									preparation.askedmodifier=True
						if preparation.askedmodifier:
							if (preparation.food_list["food_items"]["{}".format(entry['food_item'])]["{}".format(entry['modifier'][0])]["is_pack"]==1):
								data = list((preparation.food_list["food_items"]["{}".format(entry['food_item'])]["{}".format(entry['modifier'][0])]["pack"].keys()))
								data_lower = [item.lower() for item in data]
								self.agi_pass.verbose(">>>>>>payload", payload)
								ri = check (payload, data_lower)
								if ri != []:
									for value in ri:
										del payload[value]
										entry['package'] = 'Family Pack'
								else:
									entry['package'] = 'Regular'
									# result = self.asr.preparation(self.agi_pass, 'pack', entry['modifier'][0], data)
									# if result == '':
										# self.human_route('call_forwarding')
									# else:
										# entry['package'] = result[0]
									# entry['package'] = (''.join(result[-1]))
								preparation.askedpackage=True
							else:
								preparation.askedpackage=True
						if preparation.askedpackage:
							if not (entry['quantity']):
								result = self.asr.quantity(self.agi_pass, entry['modifier'][0])
								if result == '':
									self.human_route('connecting_manager')
								else:
									preparation.askedquantity=True
									entry['quantity'] = result
							else:
								preparation.askedquantity=True
						if preparation.askedquantity:
							popupcount = preparation("popupcount",preparation.food_list["food_items"]["{}".format(entry['food_item'])]["{}".format(entry['modifier'][0])]["popup_count"])
							if preparation.popupcount > 0:
								parse_data(entry["food_item"],entry["modifier"][0])
								for i,preparelist in enumerate(preparation.popuplist):
									data = list((preparation.food_list["preperations"]["{}".format(preparation.popupcodelist[i])]["list"]).keys())
									if not preparation_check(self.agi_pass, entry['modifier'], data) and len(data) > 1:
										result = self.asr.preparation(self.agi_pass, preparelist, entry['modifier'][0], data)
										if result != '':
											entry['modifier'].extend(result)
						if Data.checkjson:
							self.value_json.append(i_count)
						if(i_count == len(payload)-1):
							if len(self.value_json):
								for value in self.value_json:
									store.foodlistinitial[value] = 'empty'
								self.value_json = []
								self.conflict_itemname += 1
							if (len(store.foodlistinitial) and self.remove_empty()):
								create_audio(self.agi_pass, Data.caller_id, ListOfDict(self.agi_pass,store.foodlistinitial), 'order_details')
								stream_audio(self.agi_pass, Data.caller_id, ListOfDict(self.agi_pass,store.foodlistinitial), 'order_details')
								Data.audio = 'anything_else'
								item, query_text = self.asr.addonItem(self.agi_pass)
								self.agi_pass.verbose("Addon query text >>>>>>>>>>>", query_text)
								self.query_text += query_text
								if item == 'cancel':
									return self.final(entry)
								elif item == "" or item == []:
									return self.human_route('call_forwarding')
								else:
									payload += item
									payload_limit += len(item)
									store.foodlistinitial.extend(item)									
							else:
								Data.audio = 'specify_food'

						if not Data.checkjson:
							store("foodlistfinal",entry)
						Data.checkjson = False
			else:
				if (result[0]['modifier'][1] != '' or result[0]['package'] != '' or result[0]['custom'] != '') and len(result) != 1:
					store.foodlistfinal[i_count-1]['modifier'].append(result[0]['modifier'])
					del(payload[i_count])
					if (i_count == payload_limit-1):
						return self.final({})
				else:
					Data.audio = 'specify_one_food'


		if self.sessionCheck():
			self.initial('order_retake')
		else:
			if not self.sessionCheck():
				return self.human_route('call_forwarding')

	def getCallerName(self):
		"""This method collects user name
		"""
		if not self.get_callername:
			userconvwrite(Data.caller_id,"system", str(Data.audio).split('/')[-1])
			Data.audio = "name"
			userconvwrite(Data.caller_id,"system", str(Data.audio).split('/')[-1])
			caller_name = Data.stt.speechtotext(self.agi_pass, Data.valid_digits, "get_callername", Data.caller_id, Data.audio, Data.stt_record_duration, '')
			setname(caller_name)

	def confirm_order(self):
		t = threading.Thread( target=Playaudio.holdmusic, args = (self.agi_pass, 'confirm_order',))
		Playaudio.audioflag = True
		t.start()
		post(self.agi_pass, 'confirm')
		Playaudio.audioflag = False
		t.join()

	def playcallername(self):
		if (os.path.exists('/tmp/{}/caller_name.gsm'.format(Data.caller_id))):
			callername = '/tmp/{}/caller_name'.format(Data.caller_id)
			self.agi_pass.stream_file(callername, escape_digits='', sample_offset=0)
		else:
			#pass
			self.get_callername = False
			#setname_initial()
			# setname('')


	def mainflow(self):
		"""This method responsible for handling initial greetings and final greetings
		"""

		self.initial(voice_intent)

		if self.user_response == 'REORDER':
			self.proceed = True
			self.handle_dtmf = True
		elif self.user_response == 'YES':
			self.confirm_order()
			self.agi_pass.verbose("printer status---------->", store.printer_status)
			if store.printer_status == 0:
				self.agi_pass.appexec('DIAL', 'SIP/9606@34.67.248.168:60281,,m(default)')
				self.agi_pass.stream_file(sound_src + 'call_disconnect', escape_digits='', sample_offset=0)
			userconvwrite(Data.caller_id,"system", 'order_status' + ' ' +str(store.order_status))

			self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
			userconvwrite(Data.caller_id,"system", str(Data.audio).split('/')[-1])

			self.getCallerName()

			Data.audio = 'thanks_calling_fidaa'
			self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
			userconvwrite(Data.caller_id,"system", str(Data.audio).split('/')[-1])

			# post(self.agi_pass, 'confirm')
			rename(Data.caller_id)

		elif self.user_response == "" or self.user_response == 'NO':
			self.human_route('connecting_manager')
		else:
			pass

	def ivr_routing(self):
		"""This method handles IVR
		"""
		if checktimings(p, s, flag1) == 0:
			if not self.handle_dtmf:
				option = dtmf(self.agi_pass, Data.valid_digits, 'ivr', Data.caller_id, Data.audio)
				userconvwrite(Data.caller_id, 'customer', 'pressed-> '+str(option))

			else:
				option = 'modify'

			if option == str(1):
				self.playcallername()
				Data.audio = 'order_place_beep'
				self.mainflow()
			elif option == str(2) or option == str(0):
				self.human_route('connecting_manager')
			elif option == 'modify':
				Data.audio = 'order_modify'
				self.mainflow()
			else:
				if option == str(3):
					Data.audio = 'help'
					self.clearIvrCtr()
				elif option == str(4):
					Data.audio = 'press1234'
					self.clearIvrCtr()
				elif option == '':
					Data.audio = 'press_option'
					self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
					Data.audio = 'press1234'
					self.ivrEmpty += 1
				else:
					Data.audio = 'invalid_option'
					self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
					Data.audio = 'press1234'
					self.ivrAny += 1
				if self.ivrEmpty == self.SESSION_LIMIT or self.ivrAny == self.SESSION_LIMIT:
					Data.audio = 'session_closed'
					self.proceed = False
					self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
		else:
			Data.audio = 'closed'
			self.agi_pass.stream_file(sound_src + Data.audio, escape_digits='', sample_offset=0)
			# userconvwrite(Data.caller_id,"system", str(Data.audio).split('/')[-1])

			# post(self.agi_pass, 'confirm')
			rename(Data.caller_id)
			self.agi_pass.hangup()
def starter():
	"""starter() acts as the main driver for all stubs. It calls and manages overall activity of this project.
	"""
	agi = AGI()
	caller_id = agi.env['agi_callerid']

	folder_create(caller_id)

	rename(caller_id)

	#self.get_callername = False
	setname_initial(agi, caller_id)
	t = threading.Thread(target=namepostthread, args = (agi,))
	t.start()
	t.join()

	Data.caller_id = caller_id

	agi_obj = agiDriver(agi)
	mixmonitor(agi, caller_id)
	while agi_obj.proceed:
		agi_obj.ivr_routing()

starter()
