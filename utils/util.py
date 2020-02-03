import time
import json
from os.path import expanduser
import datetime
import threading
import random
import contextlib
import wave

from text_to_speech.tts import tts
from utils.config import os, sound_src, tmp_dir, voice_intent, accept_intent, dir_path, temp_json_src
from utils.playaudio import Playaudio


home = "/etc/asterisk"
timestamp=time.time()

def folder_create(caller_id):
	"""This function creates folders needed for our application

	:param caller_id: Caller id of the user
	:type caller_id: str
	"""
	if not (os.path.exists('{}/train_data'.format(dir_path))):
		os.system("mkdir {}/train_data".format(dir_path))
		os.system("mkdir {}".format(dir_path+"/train_data/"+voice_intent))
		os.system("mkdir {}".format(dir_path+"/train_data/"+accept_intent))
		os.system("mkdir {}".format(dir_path+"/train_data/"+'quantity'))
		os.system("mkdir {}".format(dir_path+"/train_data/"+'package'))
		os.system("mkdir {}".format(dir_path+"/train_data/"+'final_confirm'))

	if not (os.path.exists('/tmp/{}'.format(caller_id))):
		os.system("mkdir {}{}".format(tmp_dir, caller_id))
		os.system("mkdir {}{}/addItem".format(tmp_dir,caller_id))

	if not (os.path.exists('{}{}/monitor/'.format(tmp_dir, caller_id))):
		os.system("mkdir {}{}/monitor".format(tmp_dir, caller_id))

	if not (os.path.exists('{}/UserDialog/{}'.format(home,caller_id))):
		os.chdir("{}".format(home))
		os.system("mkdir UserDialog")
		os.chdir("{}/UserDialog/".format(home))
		os.system("mkdir {}".format(caller_id))

def food_list():
	"""This function usage is to read json

	:return: data got from json
	:rtype: str
	"""
	with open( temp_json_src + 'temp.json', 'r') as myfile:
		data=myfile.read()
	return json.loads(data)

def get_time():
	"""This function returns current time

	:return: current time
	:rtype: str
	"""
	return datetime.datetime.now().strftime('%H:%M:%S')

def ListOfDict(agi, result):
	"""This function converts food list to sentence(human understandable format)

	:param agi: AGI class object
	:type agi: instance of a class
	:param result: Food list
	:type result: list
	:return: string
	:rtype: str
	"""
	string = "Your order details ,"
	result = [str(res['quantity']) + ' ' + ' '.join(res['modifier']) + ' ' + ' '.join([res['package']]) for i,res in enumerate(result) if res != 'empty' and res['modifier'][0] != '']
	if len(result) > 1:
		string += ', '.join([res if i < len(result)-1 else 'and , ' + res for i,res in enumerate(result)])
	else:
		string += ', '.join([res for res in result])
	return string

def mixmonitor(agi, caller_id):
	"""This function used to monitor the entire conversation

	:param agi: AGI class object
	:type agi: instance of a class
	:param caller_id: Caller id of the user
	:type caller_id: str
	"""
	agi.appexec('MixMonitor', '{}{}/monitor/{}.wav16'.format(tmp_dir, caller_id, get_time()))

def parse(agi, con, x):
	"""This function used to parse each and every details from food list

	:param agi: AGI class object
	:type agi: instance of a class
	:param con: Condition states decides to put eval or not
	:type con: int
	:param x: Food list
	:type x: list
	:return: parsed data
	:rtype: str
	"""
	if(con == 1):
		y = eval(x)
	else:
		y = x
	food_item = y['food_item']
	modifier = y["modifier"]
	quantity = y["quantity"]
	return food_item, modifier, quantity

def rename(caller_id):
	"""This function usage is to rename the file

	:param caller_id: Caller id of the user
	:type caller_id: str
	"""
	os.chdir('{}/UserDialog/{}/'.format(home,caller_id))
	if os.path.exists('now.txt'):
		os.system('mv now.txt {}/UserDialog/{}/{}.txt '.format(home,caller_id,timestamp))

def userconvwrite(caller_id,ref,msg):
	"""This function handles threading during log writing

	:param caller_id: Caller id of the user
	:type caller_id: str
	:param ref: String defines whose statement going to written in log(ex: system or customer)
	:type ref: str
	:param msg: Content to be written in log file
	:type msg: str
	"""
	t = threading.Thread(target=userconvwritethread, args = (caller_id,ref,msg,))
	t.start()
	t.join()

def userconvwritethread(caller_id,ref,msg):
	"""This function writes data to the log file

	:param caller_id: Caller id of the user
	:type caller_id: str
	:param ref: String defines whose statement going to written in log(ex: system or customer)
	:type ref: str
	:param msg: Content to be written in log file
	:type msg: str
	"""
	with open('{}/UserDialog/{}/now.txt'.format(home,caller_id), "a") as myfile:
		myfile.write("\n")
		myfile.write(ref+"==>\t"+str(msg))

def create_audio(agi, caller_id, text,  filename):
	"""This function passes text to tts function and creates audio

	:param agi: AGI class object
	:type agi: instance of a class
	:param caller_id: Caller id of the user
	:type caller_id: str
	:param text: text to convert into audio
	:type text: str
	:param filename: audio filename
	:type filename: str
	"""
	tts(agi, text, caller_id, filename)
	# audio = '{}'.format(filename)

def stream_audio(agi, caller_id, text, audio):
	"""This function writes audio data to log file and then streams

	:param agi: AGI class object
	:type agi: instance of a class
	:param caller_id: Caller id of the user
	:type caller_id: str
	:param text: Audio content
	:type text: str
	:param audio: name of the audio file
	:type audio: str
	"""
	userconvwrite(caller_id,"system",text)
	agi.stream_file(tmp_dir + caller_id + '/' + audio, escape_digits='', sample_offset=0)

def result_conversion(result):
	"""This function converts dflow data to json format(ex: _ to &)

	:param result: food list data returned from dflow
	:type result: list
	:return: Changed food list as per json format
	:rtype: list
	"""
	for res in result:
		if 'food_item' in res.keys():
			if res['food_item'] != '' and res['food_item'] != res['modifier'][0]:
				res['food_item'] = res['food_item'].replace('_', 'And')
				res['food_item'] = ''.join(' ' + food_item.lower() if food_item.isupper() else food_item for food_item in res['food_item'][:])
				res['food_item'] = res['food_item'].title()
	return result

def resultkey_delete(result):
	"""This function usage is to delete result dictionary from the food list

	:param result: food list
	:type result: list
	:return: formatted food list
	:rtype: list
	"""
	if result != '' and result != ['empty'] and result !=  ['improper'] and result != [] and result != ['empty_audio'] and result != ['dummy']:
		if 'result' in result[-1].keys():
			del result[-1]
	return result

def result_split(caller_id, result):
	"""This function split the dflow data

	:param caller_id: Caller id of the user
	:type caller_id: str
	:param result: food list from dflow
	:type result: list
	:return: splitted query text and result
	:rtype: str & list
	"""
	query_text, result = result.split('|')
	userconvwrite(caller_id, 'customer', 'said-> ' + str(query_text))
	result = eval(result)
	return query_text, result



def dtmf(agi, valid_digits, intent_name, caller_id, audio):
	# agi.appexec('Monitor', 'wav16,{}{}/{}_{}_monitor'.format(tmp_dir, caller_id, voice_file, intent_name))
	userconvwrite(caller_id,'system',str(audio).split('/')[-1] + ' ' +intent_name)
	dtmf_res = agi.get_data(sound_src + audio, 4000, valid_digits)
	# agi.appexec('StopMonitor')
	return dtmf_res

def dtmf_monitor(agi, valid_digits, voice_file, intent_name, caller_id, audio):
	agi.appexec('Monitor', 'wav16,{}{}/{}_{}_monitor'.format(tmp_dir, caller_id, voice_file, intent_name))
	userconvwrite(caller_id,'system',str(audio).split('/')[-1] + ' ' +intent_name)
	dtmf_res = agi.get_data(sound_src + audio, 10000, valid_digits)
	agi.appexec('StopMonitor')
	return dtmf_res

def stream_record(agi, voice_file, intent_name, caller_id, audio, record_duration):
	agi.appexec('Monitor', 'wav16,{}{}/{}_{}_monitor'.format(tmp_dir, caller_id, voice_file, intent_name))
	agi.stream_file(sound_src+ audio, escape_digits='', sample_offset=0)
	userconvwrite(caller_id,'system',str(audio).split('/')[-1] + ' ' +intent_name)

	try:
		agi.appexec('RECORD', '{}{}/{}_{}_input.wav16,4,{}'.format(tmp_dir, caller_id, voice_file, intent_name, record_duration) )
		agi.verbose('I/P File recorded')
	except:
		agi.verbose('error in recording')

	agi.appexec('StopMonitor')

def preparation_check(agi,modifier, data):
	modifier = [data for data in modifier if data]
	modifier = [value.replace('With', '').lstrip() for value in modifier]
	for i, value in enumerate(modifier):
		if value[0].isdigit():
			modifier[i] = value.replace(value[0],'')
			modifier[i] = modifier[i].replace(modifier[i][0],"",1)
	if (set(modifier).intersection(set(data))):
		return True
	else:
		return False

def pack_update(result_lower, data_lower):
	pack = []
	for i in range(len(result_lower)):     
		if result_lower[i]['food_item'] in data_lower:
			if result_lower[i]['food_item'] != []:
				pack.append(result_lower[i]['food_item'])
				del result_lower[i] 
	for i in range(len(result_lower)):
		result_lower[i]['package'] = pack
	return result_lower

def package_check(agi, result_update, data):
	data_lower = [item.lower() for item in data]
	result = []
	for item in result_update:
		for k, v in item.items(): 
			if k == 'food_item':
				result.append(v)
				if v in data_lower:
					if (set(result).intersection(set(data_lower))):
						return True
					else:
						return False

def check(result_lower, data_lower):
	ri = []
	for i, entry in enumerate(result_lower):
		for k, v in entry.items():
			if v in data_lower:
				ri.append(i)
	return ri

def pack_check(result_lower, data_lower):
	ri = []
	for i, entry in enumerate(result_lower):
		if i > 0:
			for k, v in entry.items():
				if v in data_lower:
					ri.append(i)
		else:
			result_lower[i]['package'] = "regular"
	return ri
# def DictOfList(agi, result):
# 	s = "Your order details "
# 	s += ', '.join("%s" % ' '.join(map(str, (result['quantity'][i], res))) for i, res in enumerate(result['modifier']) if res != '')
# 	index = s.rfind(str([int(num) for num in s.split() if num.isdigit()][-1]))
# 	if len([int(num) for num in s.split() if num.isdigit()]) > 1:
# 		s = s[:index-2] + ' and ' + s[index:]
# 	return s

# def get_time():
#     t= time.ctime().split()[3].split(':')
#     HH, MM, _ = int(t[0]), int(t[1])+30, t[2]
#     if int(MM/60) > 0:
#         HH += 1
#         if int(HH/24) > 0:
#             HH %= 24
#     MM %= 60
#     t = time.strptime(str(HH) + ':' + str(MM), "%H:%M")
#     hr_12 = time.strftime( "%I:%M%p", t )
#     return hr_12
# print(get_time())












