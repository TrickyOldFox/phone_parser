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

regex = r'[\+\(]?[0-9]{1,3}[\s.\-\(\)]{0,3}[0-9]{2,3}[\s.\-\(\)]{0,3}[0-9]{2}[\s.\-\(\)]{0,3}[0-9]{0,3}[\s.\-\(\)]{0,3}[0-9]{2,3}[\D]'

client = TelegramClient('anon', api_id, api_hash)

def parse_message(message):
	text = message.message + 'n'
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
				if counter == 0 and phone[0] != '+':
					counter += 1
					continue
				if counter == len(country_codes):
					break
				number = phonenumbers.parse(phone, country_codes[counter])
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
		dialog_id = 459878125
		if dialog.id == dialog_id:
			dialogs.append({
			'id': dialog.id,
			'name': dialog.name
			})
			try:
				async for user in client.iter_participants("me"):
					if user.username and user.phone:
						user_dict = {}
						user_dict['username'] = user.username
						user_dict['phone'] = user.phone
						user_dict['first_name'] = user.first_name
						user_dict['last_name'] = user.last_name
						users.append(user_dict)
				async for message in client.iter_messages("me"):
					valid, phone = parse_message(message)
					if valid:
						user = await client.get_entity(message.peer_id.user_id)
						user_dict = {
							'username': user.username,
							'phone': phone,
							'first_name': user.first_name,
							'last_name': user.last_name
						}
						users.append(user_dict)
			except:
				pass
	if users:
		with open('users.csv', 'w', encoding='utf8') as csv_file:
			csv_writer = csv.DictWriter(csv_file, users[0].keys())
			csv_writer.writerows(users)
		with open('users.json', 'w', encoding='utf8') as outfile:
			json.dump(users, outfile, ensure_ascii=False)
	with open('dialogs.json', 'w', encoding='utf8') as outfile:
		json.dump(dialogs, outfile, ensure_ascii=False)

with client:
    client.loop.run_until_complete(main())
