import re
import requests
import sys
import time
import pathlib
from bs4 import BeautifulSoup
from queue import Queue
from threading import Thread

# 398000

URL = 'https://ieeexplore.ieee.org/document/{num}'
PATTERN = r'xplGlobal\.document\.metadata=(.*);'
OUT = 'out/Astar'
THREADS = int(sys.argv[1])

def func(qin:Queue, qout:Queue) -> None:
	"""
	"""

	while True:
		i =  qin.get()
		if i is None:
			break
		try:
			qout.put((i,requests.get(URL.format(num=i)).text))
		except BaseException:
			qout.put((i,None))
			time.sleep(10)


qs = [Queue(), Queue()]
ts = [Thread(target=func, args=(qs[0], qs[1])) for _ in range(THREADS)]
for t in ts:
	t.start()

pathlib.Path(OUT).mkdir(parents=True, exist_ok=True)

start, count = int(sys.argv[2]), 0
while start < 10**7:
	
	if qs[0].qsize() < 2 * THREADS:
		for _ in range(THREADS):
			qs[0].put(start)
			start += 1
	
	with open(f'{OUT}/ieee.txt', 'a+', encoding='utf-8') as f:
		for _ in range(THREADS):
			num, r = qs[1].get()
			if r is None:
				qs[0].put(num)
				continue
			s = BeautifulSoup(r, features='lxml')		
			for e in s.find_all('script'):
				if e.string:
					m = re.findall(PATTERN, e.string)
					if len(m) > 0:
						count += 1
						print(num, count)
						f.write(f'{m[0]}\n')

for _ in range(THREADS):
	qs[0].put(None)
for t in ts:
	t.join()
