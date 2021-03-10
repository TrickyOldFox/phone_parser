# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 01:20:22 2020

@author: Андрей
"""

import json
import csv
import phonenumbers
from settings import *

from telethon.sync import TelegramClient
from pprint import pprint

import re
try:
	with open('dialogs_to_parse.csv', mode='r', encoding='UTF-8') as infile:
		DIALOGS_TO_PARSE = []
		reader = csv.DictReader(infile, fieldnames=['id', 'name'])
		for row in reader:
			DIALOGS_TO_PARSE.append(int(row['id']))
except Exception as e:
	print(e)
	DIALOGS_TO_PARSE=[]
print(DIALOGS_TO_PARSE)


regex = r'[\+\(]?[0-9]{1,3}[\s.\-\(\)]{0,3}[0-9]{2,3}[\s.\-\(\)]{0,3}[0-9]{2}[\s.\-\(\)]{0,3}[0-9]{0,3}[\s.\-\(\)]{0,3}[0-9]{2,3}[\D]'

client = TelegramClient('anon', API_ID, API_HASH)

def parse_message(message):
	text = str(message.message) + 'n'
	number = ''
	fails = 0
	phones = re.findall(regex, text)
	valid_phones = []
	cleared_phones = []
	separators = [' ', '-', '(', ')', '.']
	if phones:
		for phone in phones:
			cleared_phone = phone[:-1]
			for separator in separators:
				cleared_phone = cleared_phone.replace(separator, '')
			cleared_phones.append(cleared_phone)
			if cleared_phone[0]!='+':
				cleared_phones.append(f'+{cleared_phone}')
	for phone in cleared_phones:
		try:
			counter = 0
			while True:
				if not COUNTRY_CODES[counter] and phone[0] != '+':
					counter += 1
					continue
				if counter == len(COUNTRY_CODES):
					break
				number = phonenumbers.parse(phone, COUNTRY_CODES[counter])
				if phonenumbers.is_possible_number(number):
					number = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
					if number not in valid_phones:
						valid_phones.append(number)
					break
				counter += 1
		except:
			pass
	if valid_phones:
		return True, valid_phones
	return False, None

async def main():
	account = await client.get_me()

	users = []
	dialogs = []
	
	async for dialog in client.iter_dialogs():
		dialogs.append({
			'id': dialog.id,
			'name': dialog.name
			})
		if dialog.id in DIALOGS_TO_PARSE:
			try:
				async for user in client.iter_participants(dialog):
					if user.username and user.phone:
						user_dict = {}
						user_dict['username'] = user.username
						user_dict['phone'] = [user.phone]
						user_dict['first_name'] = user.first_name
						user_dict['last_name'] = user.last_name
						users.append(user_dict)
			except:
				print('Not enough privileges')
			counter = 0
			async for message in client.iter_messages(dialog, limit=MESSAGE_LIMIT):
				counter += 1
				valid, phone = parse_message(message)
				if valid:
					user_id = message.from_id.user_id if hasattr(message.from_id, 'user_id') else \
						message.from_id
					if user_id:
						user = await client.get_entity(user_id)
						user_dict = {
							'username': user.username,
							'phone': phone,
							'first_name': user.first_name if hasattr(user, 'first_name') else None,
							'last_name': user.last_name if hasattr(user, 'last_name') else None
						}
						users.append(user_dict)
			print(counter)
	if users:
		with open('users.csv', 'w', encoding='utf8') as csv_file:
			csv_writer = csv.DictWriter(csv_file, users[0].keys())
			for user in users:
				csv_phone = ''
				for phone in user['phone']:
					if csv_phone:
						csv_phone += '   ' + str(phone)
					else:
						csv_phone += str(phone)
				user['phone'] = csv_phone
			csv_writer.writerows(users)
		with open('users.json', 'w', encoding='utf8') as outfile:
			json.dump(users, outfile, ensure_ascii=False)
	with open('dialogs.csv', 'w', encoding='utf8') as csv_file:
		csv_writer = csv.DictWriter(csv_file, dialogs[0].keys())
		csv_writer.writerows(dialogs)

with client:
    client.loop.run_until_complete(main())
