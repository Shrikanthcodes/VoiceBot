import sys
import os


### folder paths
dir_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sound_src = '/var/www/html/cms/api/sounds/'
# sound_src = dir_path + '/sounds/'
agi_src = dir_path + '/agi-bin/'
json_src = agi_src + 'utils/'
tmp_dir = '/tmp/'
temp_json_src = '/var/www/html/cms/api/'
# temp_json_src = dir_path

### agent config
language_code = 'en-us'
accept_project_id = 'acceptance-233711'
voice_project_id = 'ninth-iris-236300'
accept_intent = 'YesorNo'
voice_intent = 'order'
accept_json = json_src + 'acceptance-3a1d2ba797d4.json'
voice_json = json_src + 'My First Project-2e1b0d351e36.json'
model = 'command_and_search'