import json
import csv
from itertools import permutations

from agent_operations import os, DflowOperation

def csv_write(file_name, rows):
    if rows != []:
        with open(file_name+'.csv', 'a+') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerows(rows)

def combo(string):
    string_combo = []

    combos = permutations(string.split())
    for combo in list(combos):
        string_combo.append(' '.join(combo))

    return string_combo

def csv_row_build(food_names, file_name):
    result_row = []

    for food_name in food_names:
        food_name = food_name.replace('.', '')
        row = [food_name]*2
        row += combo(food_name.lower())
        row += combo(food_name.title())
        result_row.append(row)

    return csv_write(file_name, result_row)

def main(dir_path):

    food_items = json.load(open('food_update.json'))
    for food_category in food_items:
        file_name = dir_path + '/food_csv/'
        csv_row_build([food_category], file_name+'FoodCat')

        food_names = food_items[food_category]
        file_name += food_category[0].lower() + food_category.title().replace(' ','')[1:]
        csv_row_build(food_names, file_name)

    print('Done')

    obj = DflowOperation('ninth-iris-236300')

    files = os.listdir(dir_path + '/food_csv/')
    files.sort()
    for file_name in files:
        obj.create_entity_type(dir_path + '/food_csv/'+file_name)

# main()