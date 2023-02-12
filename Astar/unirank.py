from StorageUtils.SQLite import SQLite

import googlemaps
import re
import requests
import time
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim


def get_pages():
	
	url = 'https://www.4icu.org/reviews/index{num}.htm'
	
	nums = ['0001']
	nums.extend(range(2,28))
	
	with open('out/astar/unirank_links', 'w') as f:
		for i in nums:
			print(i, end=' ')
			txt = requests.get(url.format(num=i)).text
			s = BeautifulSoup(txt, features='lxml')
			for e in s.find_all('a'):
				if 'reviews' in e['href']:
					f.write(f'{e["href"]}\n')
		print('\n')


def get_universities():
	
	db = SQLite('out/astar/unirank.db')
	
	db.fetch(query=
			 'CREATE TABLE IF NOT EXISTS Universities('
			 'url TEXT, '
			 'name TEXT, '
			 'acronym TEXT, '
			 'logo TEXT, '
			 'address TEXT, '
			 'country TEXT, '
			 'foundation INTEGER, '
			 'country_rank INTEGER, '
			 'world_rank INTEGER, '
			 'color TEXT, '
			 'latitude TEXT, '
			 'longitude TEXT, '
			 'PRIMARY KEY (url)'
			 ') WITHOUT ROWID;'
		)
	
	insert = (
		'INSERT OR REPLACE INTO Universities(url,name,acronym,logo,address,'
		'country,foundation,country_rank,world_rank,color,latitude,longitude'
		') VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'
		)

	
	done = set()
	with open('out/astar/unirank_links', 'r') as f:
		for url in f:
			url = url.strip()
			if url in done:
				continue
			print(len(done), end=' ')
			txt = requests.get(f'https://www.4icu.org{url}').text
			s = BeautifulSoup(txt, features='lxml')
			done.add(url)
			
			data = [
				url, # 0 - url
				None, # 1 - name
				None, # 2 - acronym
				None, # 3 - image
				None, # 4 - address
				None, # 5 - country
				None, # 6 - foundation
				None, # 7 - country rank
				None, # 8 - world rank
				None, # 9 - color
				None, # 10 - latitude
				None # 11 - longitude
				]

			t = s.find('img', {'itemprop':'logo'})
			if t:
				data[3] = t['src']

			ccode = s.select_one('div.hidden-xs a')
			if ccode:
				t = re.search(r'/([a-zA-z][a-zA-z])/', ccode['href'])
				if t:
					data[5] = t.group(1)
	
			for e in s.find_all('table'):

				t = re.search(r'Name\s{1,2}(.+)', e.text)
				if t and not data[1]:
					data[1] = str(t.group(1))
				
				t = re.search(r'Acronym\s{1,2}(.+)', e.text)
				if t:
					data[2] = str(t.group(1))
				
				t = re.search(r'Address\s{1,2}(.+)', e.text)
				if t:
					data[4] = str(t.group(1))

				t = re.search(r'Founded\s{1,2}(\d+)', e.text)
				if t:
					data[6] = int(t.group(1))

				t = re.search(r'country rank\s{1,2}(\d+)', e.text)
				if t:
					data[7] = int(t.group(1))

				t = re.search(r'world rank\s{1,2}(\d+)', e.text)
				if t:
					data[8] = int(t.group(1))
					
				t = re.search(r'Colours\s{1,2}(.+)', e.text)
				if t:
					data[9] = str(t.group(1))
			
			if data[1] and data[4]:
				db.fetch(query=insert, params=[tuple(data)])

	del db


def geolocate_osm():
	
	insert = (
		'INSERT OR REPLACE INTO Universities(url,name,acronym,logo,address,'
		'country,foundation,country_rank,world_rank,color,latitude,longitude'
		') VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'
		)
	
	count = 0
	loc = Nominatim(user_agent='LocAgent')
	db = SQLite('out/astar/unirank.db')
	for i,row in enumerate(db.fetch(query='SELECT * FROM Universities;')):
		if i < 2034:
			continue
		time.sleep(1)
		print(count, i)
		l = loc.geocode(row[4], exactly_one=True)
		if l:
			row = list(row)
			row[10] = l.latitude
			row[11] = l.longitude
			db.fetch(query=insert, params=[tuple(row)])
			count += 1

def geolocate_gmaps():
	
	insert = (
		'INSERT OR REPLACE INTO Universities(url,name,acronym,logo,address,'
		'country,foundation,country_rank,world_rank,color,latitude,longitude'
		') VALUES (?,?,?,?,?,?,?,?,?,?,?,?);'
		)
	
	with open('config/Astar/google_maps.key', 'r') as f:
		key = f.read()
	
	count = 0
	loc = googlemaps.Client(key=key)
	db = SQLite('out/astar/unirank.db')
	for i,row in enumerate(db.fetch(query='SELECT * FROM Universities;')):
		time.sleep(0.1)
		print(count, i)
		
		l = None
		try:
			l = loc.geocode(row[4])
		except BaseException as e:
			time.sleep(1)
			continue
		
		if l:
			lat = l[0]['geometry']['location']['lat']
			lng = l[0]['geometry']['location']['lng']
			
			store = True
			for d in l[0]['address_components']:
				if 'country' in d['types']:
					if not d['short_name'].lower() == row[5]:
						store = False
						break
			
			if store:
				row = list(row)
				row[10] = str(lat)
				row[11] = str(lng)
				db.fetch(query=insert, params=[tuple(row)])
			count += 1


if __name__ == '__main__':
	
	geolocate_gmaps()
