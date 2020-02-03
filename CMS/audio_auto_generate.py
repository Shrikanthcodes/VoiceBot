#!/usr/bin/env python3.5
import json
import os
from collections import defaultdict
from json_csv import main
# sound_src = '/var/www/html/cms/api/sounds/'
data = json.load(open('food.json'))
greetings_json = json.load(open('greetings.json'))
from pydub import AudioSegment

food_items = data['food_items']
# print(food_items)
temp = {}
def word_replace():
	# print("json replace starting........")
	for key, value in food_items.items():
		temp_value = {}
		key = key.lower()
		food_key = value
		for food_item, food_value in food_key.items():
			food_item_key = food_item.lower()
			temp_value[food_item_key] = food_value
		temp[key] = temp_value
	with open('food.json', 'r') as file:
		data = json.load(file)
		data['food_items'] = temp
	if os.path.exists("temp.json"):
		os.remove("temp.json")
	with open('temp.json', 'w') as file:
		json.dump(data, file, indent=2)

word_replace()

dir_path = os.path.dirname(os.path.abspath(__file__))

def folder_create(path, folder_name):
	if not os.path.exists(path+ "/" +folder_name):
		os.mkdir(path+ "/" +folder_name)
	#else:
		#text_file.write(folder_name + " is already exist \n")

folder_create(dir_path, "sounds")
sound_src = dir_path + '/sounds/'
os.system("cp -r {}/default_audio/* {}/sounds/".format(dir_path, dir_path))

# os.system("cp -p /var/www/html/cms/api/food.json {}/food.json".format(dir_path))
# print('started audio check')

#data = json.load(open('/var/www/html/cms/api/food.json'))
food_items = data['food_items']
preparations = data['preperations']
# print("Json", preparations)

food_items_list = list(food_items)
preparations_list = list(preparations)

# print (preparations_list)
folder_create(sound_src, "preparations")

def change_word(item):
	item = item.lower().replace(' ', '').replace('_', 'and')
	return (item)

def file_check(audio):
	if os.path.exists(audio):
		return 'yes'

	else:
		return 'no'
prep_update_list = []
def prep_name_check():
	for key, value in preparations.items():
		get_name = value
		for name, n_type in get_name.items():
			if name == "name":
				n_type = change_word(n_type)
				#text_file.write("Preparation_name:" + n_type + "\n")
				prep_update_list.append(n_type)
				folder_create(sound_src + "preparations/", n_type)
prep_name_check()

def synthesize_ssml(filename, ssml):
	"""Synthesizes speech from the input string of ssml.

	Note: ssml must be well-formed according to:
		https://www.w3.org/TR/speech-synthesis/

	Example: <speak>Hello there.</speak>
	"""

	os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'My First Project-2e1b0d351e36.json'
	from google.cloud import texttospeech
	client = texttospeech.TextToSpeechClient()

	input_text = texttospeech.types.SynthesisInput(ssml=ssml)

	# Note: the voice can also be specified by name.
	# Names of voices can be retrieved with client.list_voices().
	# voice = client.list_voices().voices[160]
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
	with open(filename, 'wb') as out:
		out.write(response.audio_content)

def sox_convert(wav_path, gsm_path):
	os.system("sox {}.wav -r 8000 -c 1 {}.gsm".format(wav_path, gsm_path))
	os.system("rm {}.wav".format(wav_path))

def default_audios():
	for key, value in greetings_json.items():
		synthesize_ssml(sound_src + key + ".wav", value)
		key = key.replace('(', '\(')
		key = key.replace(')', '\)')
		os.system("sox {}.wav -r 8000 -c 1 {}.gsm".format(sound_src+key, sound_src+key))
		os.system("rm {}.wav".format(sound_src+key))

default_audios()

def specify_audio():
	specify_text = "Please specify the food item in the menu after the beep"
	synthesize_ssml(sound_src + "specify_food.wav", specify_text)
	sound1 = AudioSegment.from_file(sound_src +"specify_food.wav")
	sound2 = AudioSegment.from_file("default_audio/beep.wav")
	combined = sound1 + sound2
	combined.export(sound_src + "specify_food.wav", format='wav')
	sox_convert(sound_src + "specify_food", sound_src + "specify_food")

specify_audio()

def repeatorder_audio():
	repeat_order_text = "I am Sorry , I didn’t quite get that , please repeat your order or press  0 to talk to the restaurant Manager"
	synthesize_ssml(sound_src + "repeat_order.wav", repeat_order_text)
	sound1 = AudioSegment.from_file(sound_src +"repeat_order.wav")
	sound2 = AudioSegment.from_file("default_audio/beep.wav")
	combined = sound1 + sound2
	combined.export(sound_src + "repeat_order.wav", format='wav')
	sox_convert(sound_src + "repeat_order", sound_src + "repeat_order")

repeatorder_audio()

def invalid_preparations_create():
	for i in preparations:
		name = preparations[i]['name'].lower().replace(' ','')
		# print(name)
		inputlist = sorted(preparations[i]['list'].keys())
		text = 'Press'
		for i, value in enumerate(inputlist):
			value = value.replace('With', '')
			# print(i, value)
			text = text + '  '+ str(i+1) + '  '+  'for' + '  '+value + '.'
		# print(text)

		if file_check(sound_src + 'preparations/' + name + '/' + 'invalid_option'+'.gsm') == 'no':
				# tts(text, sound_src + 'preparations/' + prep_type + '/' + item)
				synthesize_ssml(sound_src + 'preparations/' + name + '/' + 'invalid_option' + ".wav", text)
				sox_convert(sound_src + 'preparations/' + name + '/' + 'invalid_option', sound_src + 'preparations/' + name + '/' + ' ')
invalid_preparations_create()


def invalid_pack_create(item_prep_list):
	# print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Priya", item_prep_list)
	# print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Priya", type(item_prep_list))
	inputlist = item_prep_list.keys()
	text = 'Press'
	for i, pack in enumerate(inputlist):
			text = text + '  ' + str(i+1) + 'for' + pack
			i += 1
	if file_check(sound_src + 'preparations/pack/' + 'invalid_option.gsm') == 'no':
		synthesize_ssml(sound_src + 'preparations/pack/' + 'invalid_option' + ".wav", text)
		sox_convert(sound_src + 'preparations/pack/' + 'invalid_option', sound_src + 'preparations/pack/' + 'invalid_option')

def prep_create(item, prep_type, item_prep):
	if prep_type in prep_update_list:
		if prep_type == 'spicylevel':
			text = 'How much spice would you like in your' + item + 'Press'
			for i,spice in enumerate(sorted(list(preparations[item_prep]['list']))):
				text = text + '  '+ str(i+1) +  'for' + spice + '.'

		else:
			if prep_type == 'complementary':
				text = 'Would you like to add on Naan to the complementary Plain Rice for just 50 cents. Press'
				# print("Value", list(preparations[item_prep]['list']))
				# print("Preparation", preparations[item_prep]['list'])
				# print("Just >>", item_prep)
				for i,comp in enumerate(sorted(list(preparations[item_prep]['list']))):
					n = len(list(preparations[item_prep]['list']))
					if n == i+1:
						comp = comp.replace('With', '')
						text = text + '  '  + str(n) + 'for' + "Not Required" + '.'
						print("text - Not Required", text)
					else:
						comp = comp.replace('With', '')
						text = text + '  '  + str(i+1) + 'for' + comp + '.'
						print("text - Naan's", text)
			elif prep_type == 'desserts':
				text = 'What dessert would you like to order, Press'
				for i,dessert in enumerate(sorted(list(preparations[item_prep]['list']))):
					text = text + '  ' + str(i+1) + 'for' + dessert + '.'
			else:
				text = ''
				for addon, value in preparations[item_prep]['list'].items():
					text = text + '  ' + addon
					cost = preparations[item_prep]['list'][addon]
					if cost != 0.0:
						text = text + ' for ' + str(cost) + ' dollars'
					text += ' or      '
				text = text[:-9]
	#print("synthesize_ssml>>>>>>>>>>>>>", sound_src + 'preparations/' + prep_type + '/' + item)
	# if folder_check(sound_src + 'preparations/' + prep_type) == 'yes':
	if file_check(sound_src + 'preparations/' + prep_type + '/' + item+'.gsm') == 'no':
		# tts(text, sound_src + 'preparations/' + prep_type + '/' + item)
		synthesize_ssml(sound_src + 'preparations/' + prep_type + '/' + item + ".wav", text)
		print("synthesize_ssml>>>>>>>>>>>>>", sound_src + 'preparations/' + prep_type + '/' + item)
		sox_convert(sound_src + 'preparations/' + prep_type + '/' + item, sound_src + 'preparations/' + prep_type + '/' + item)

def prep_list_build(flag, item, item_prep_list):
	# print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Jayanthi",item_prep_list)
	if flag == 1:
		for item_prep in item_prep_list:
			prep_type = change_word(preparations[item_prep]['name'])
			prep_create(item, prep_type, item_prep)
	else:
		text = 'Which pack do you prefer for your ?' + item +'Press'
		i = 0
		for pack,cost in sorted(item_prep_list.items()):
			text = text + '  ' + str(i+1) + 'for' + pack
			i += 1
			# if cost != 0.0:
			#     text = text + ' for ' + str(cost) + ' dollars.'
			# text += ' or      '
		# text = text[:-9]
		# print (text)
		# if folder_check(sound_src + 'preparations/pack') == 'yes':
		if file_check(sound_src + 'preparations/pack/' + item+'.gsm') == 'no':
			# tts(text, sound_src + 'preparations/pack/' + item)
			synthesize_ssml(sound_src + 'preparations/pack/' + item + ".wav", text)
			sox_convert(sound_src + 'preparations/pack/' + item, sound_src + 'preparations/pack/' + item)
		invalid_pack_create(item_prep_list)

def hashaudio():
	textdata = open(r"/home/gcphrk2019/AudioText11","r")
	text = textdata.readlines()
	text = str(text[0]) #Function to read AudioText11 and change  hash audio
	synthesize_ssml(sound_src + "Order_beep_hash.wav", text)
	sox_convert(sound_src + "Order_beep_hash", sound_src + "Order_beep_hash")
hashaudio()

def timeaudio():
        textdata = open(r"/home/voicebot/v4/agi-bin/AudioText","r")
        text = textdata.readlines()
        text = str(text[0]) #Function to read AudioText and change restaurant closed audio
        synthesize_ssml(sound_src + "Timingsclose.wav", text)
        sox_convert(sound_src + "Timingsclose", sound_src + "closed")
timeaudio()

def audio_data_fill():
	key_list = []
	# print(food_items_list)
	for food in food_items_list:
		# print(food)
		key_list_orig = list(food_items[food].keys())
		if len(key_list_orig) > 2:
			food1 = change_word(food)
			text = 'Which' + food1 + 'would you like to order ?'
			folder_create(sound_src, "modifier")
			if file_check(sound_src + 'modifier/' + food1+'.gsm') == 'no':
				# tts(text, sound_src + 'modifier/' + food1)
				# print('before ssml===>> ',food1)
				synthesize_ssml(sound_src + 'modifier/' + food1 + ".wav", text)
				sox_convert(sound_src + 'modifier/' + food1, sound_src + 'modifier/' + food1)
		
		key_list_temp = [key for key in key_list_orig if key != 'state']
		key_list += key_list_temp
		for key in key_list_temp:
			if food_items[food][key]['popup_count'] > 0:
				item = change_word(key)
				prep_list_build(1, item, food_items[food][key]['preperations'])
			#else:
				#text_file.write(key + 'popup count is zero \n')
			if (food_items[food][key]['is_pack']) > 0:
				item = change_word(key)
				folder_create(sound_src + 'preparations/', "pack")
				prep_list_build(2, item, food_items[food][key]['pack'])
			#else:
				#text_file.write(key + 'pack count is zero \n')
	# print('='*100)
	# print(key_list)

	for key in key_list:
		# print(key)
		key = key.lower()
		key = change_word(key)
		## tts(key, audio_path + key)
		text = 'How many' + key + 'you want ?'
		folder_create(sound_src, "quantity")
		if file_check(sound_src + 'quantity/' + key+'.gsm') == 'no':
			# tts(text, sound_src + 'quantity/' + key)
			synthesize_ssml(sound_src + 'quantity/' + key + ".wav", text)
			sox_convert(sound_src + 'quantity/' + key, sound_src + 'quantity/' + key)
			# os.system("cp -p {}/default_audio/ {}/food.json".format(dir_path))

audio_data_fill()


def newItemUpdate():
	print("am here")
	normal_category = defaultdict(list)

	new_dict = {}
	multi = []
	outer = []
			
	for food, value in food_items.items():
		for key1, value1 in value.items():
			if value1['state'] == 'new':
				if value1['is_pack'] > 0:
					multi.append(key1)
				else:
					if food == key1:
						outer.append(key1)
					else:
						normal_category[food].append(key1)

	new_dict.update({'multi':multi}) 
	new_dict.update({'outer':outer})
	new_dict.update(normal_category)

	with open('food_update.json', 'w')as f:
		json.dump(new_dict,f)

newItemUpdate()
folder_create(dir_path, "food_csv")
main(dir_path)


f = open("sync.txt", "w")
f.write("0")
f.close()
print ("mudinjithu")

