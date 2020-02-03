import json
import requests
import threading
from text_to_speech.tts import tts
from utils.util import parse, ListOfDict, userconvwrite, create_audio
#from ContNum import *

class store:
	phone_number = ""
	extension = ""
	caller_name = ""
	foodlistinitial = []
	foodlistfinal=[]
	cost = ""
	order_status = ''
	userid = ''
	printer_status = ''

	@classmethod
	def update(cls, a, value):
		if a == "phone_number":
			if value:
				cls.phone_number = value
			else:
				pass
		elif a == "extension":
			if value:
				cls.extension = value
			else:
				pass
		elif a == "foodlistinitial":
			if value:
				cls.foodlistinitial = value
			else:
				pass
		elif a == "caller_name":
			if value:
				cls.caller_name = value
			else:
				pass
		elif a == "cost":
			if a == "cost":
				cls.cost = value
			else:
				pass
		elif a == "foodlistfinal":
			if value:
				cls.foodlistfinal.append(value)
			else:
				pass
		elif a == "order_status":
			if value:
				cls.order_status = value
			else:
				pass
		elif a == "printer_status":
			if value:
				cls.printer_status = value
			else:
				pass

	def postdata(cls):
		return [cls.phone_number, cls.extension, cls.caller_name, cls.foodlistfinal]

	def initialdata(cls):
		return (cls.foodlistinitial)

	def __init__(self, a, value):
		self.value = value
		self.update(a, value)


def postthread(payload, agi,status):
	if(status=="cost"):
		URL = "http://35.226.124.135/cms/api/?function=pricev5"
	else:
		URL = "http://35.226.124.135/cms/api/?function=orderv5"
	raw_key = {"phone_number":payload[0], "extension":payload[1], "caller_name":payload[2], "food":payload[3], "special_note":""}
	key = json.dumps(raw_key)

	payload = {"json":key}
	#agi.verbose("Post_payload>>>>>>>>>>>>", payload)
	r = requests.post(url=URL, data=(payload))
	result = r.json()
	#agi.verbose("Post result>>>>>>>>", result)
	store('cost', result["total_price"])
	if (status == 'cost'):
		create_audio(agi, store.phone_number, 'Total price is ' + str(store.cost) + ' dollars. ' +  ' Taxes as applicable ' +' Please Confirm', 'cost' )
	else:
		store('order_status', result['order_status'])
		store('printer_status', result['Print'])

def post(agi,status):
	payload = store.postdata(store)
	postthread(payload, agi,status)

def update(agi,result):
	food_category, food_name, quantity = parse(agi, 1, result)
	store ("food_category", food_category)
	store ("food_name", food_name)
	store ("quantity", quantity)

def namepostthread(agi):
	store('phone_number', agi.env['agi_callerid'])
	store('extension', agi.env['agi_context'])
	URL = "http://35.226.124.135/cms/api/?function=getCallerName"
	key = {"phone_number": agi.env['agi_callerid']}
	r = requests.post(url=URL, data=(key))
	result = r.json()
	#store("userid", result["ID"])
	if(result["status"]==1 and result["name"] != ""):
		a=result["name"]
		tts(agi,"Hello"+a+"?", store.phone_number, "caller_name")
	else:
		pass


def setname(caller_name):
	if caller_name != 'empty' or caller_name != 'error':
		URL = "http://35.226.124.135/cms/api/?function=setCallerName"
		key = {"phone_number":store.phone_number,"caller_name":caller_name}
		r = requests.post(url=URL, data=(key))

def setname_initial(agi, callerid):
	URL = "http://35.226.124.135/cms/api/?function=startCall"
	key = {"phone_number":callerid}
	r = requests.post(url=URL, data=(key))

def callforward(agi, data, query_text):
	URL = "http://35.226.124.135/cms/api/?function=callforward"
	raw_key = {"phone_number":store.phone_number, "extension":store.extension, "caller_name":store.caller_name, "food":data, "special_note":"", "unfound":query_text}
	key = json.dumps(raw_key)
	payload = {"json":key}
	r = requests.post(url=URL, data=(payload))
	result = str(r.json())
