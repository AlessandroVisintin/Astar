import re
import requests
import time
from bs4 import BeautifulSoup
from queue import Queue
from threading import Thread


URL = 'https://ieeexplore.ieee.org/document/{num}'
PATTERN = r'xplGlobal\.document\.metadata=(.*);'
OUT = 'out/Astar'
THREADS = 10


def func(qin:Queue, qout:Queue) -> None:
	"""
	"""

	while True:
		i =  qin.get()
		print(i)
		if i is None:
			break
		try:
			qout.put((i,requests.get(URL.format(num=i)).text))
		except BaseException:
			qout.put((i,None))


qs = [Queue(), Queue()]
ts = [Thread(target=func, args=(qs[0], qs[1])) for _ in range(THREADS)]
for t in ts:
	t.start()

start, count = 0, 0
while start < 10**7:

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
