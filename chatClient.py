#! /usr/bin/python
# -*-  coding=utf8  -*-

import socket
import threading
import signal
import time
import sys
import os
import subprocess

import readline
import datetime
import math

from Crypto.Cipher import AES

import pygame.camera, pygame.image, pygame.display, pygame.event

HOST = '000.000.000.000' #
PORT = 23333
ADDR = None

udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

video_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

file_trans = None

instant_camera = None

BUFSIZE = 1024

row = 1
last_row = 0

message_flag = 0
last_message = None

last_time = None

heart_beat_count = 0

history_fd = None

def sig_hdr(sig_num, frame):
	global udp_client, tcp_server, video_server, history_fd
	
	udp_client.close()
	tcp_server.close()
	video_server.close()
	history_fd.flush()
	history_fd.close()
	sys.exit(0)

def get_public_addr():
	ips = os.popen("/sbin/ifconfig | grep -E 'inet addr|inet' | awk '{print $2}'").readlines()
	for ip in ips:
		if ip.find("127.") == -1:
			return ip[ip.find(":") + 1:ip.find("\n")]

def cur_file_dir():
	path = sys.path[0]
	if os.path.isdir(path):
		return path
	elif os.path.isfile(path):
		return os.path.dirname(path)

def print_in_mid(line, isChat= True, isInfo = False):
	global row, last_row
	
	if line and len(line) <= 80:
		line = line.strip()
		if isChat:
			sys.stdout.write('\33[s\33[' + str(row) + ";" + str(40 - len(line) / 2 + 1) + 'H\33[33m' + line + '\33[0m\n\33[u')
		else:
			sys.stdout.write('\33[' + str(row) + ";" + str(40 - len(line) / 2 + 1) + 'H\33[33m' + line + '\33[0m\n')
		sys.stdout.flush()
		if isChat and not isInfo:
			history_fd.write("@" + line + "\n")
		last_row = 1
		row = row + last_row
		if isChat and row > 20:
			row = 20

def wrap(data, left):
	global last_row
	
	data = data.decode("utf8")
	
	beg = 0
	count = 0
	lines = []
	for i in range(len(data)):
		if data[i] > u'\u00ff':
			count += 2
		else:
			count += 1
		if count > 48:
			lines.append(data[beg:i + 1])
			beg = i + 1
			count = 0
	if beg < len(data):
		lines.append(data[beg:])

	ret = ""
	if left:
		if count == 0:
			count = 50
		if len(lines) == 1:
			ret += "●"
			ret += "─" * (count + 2)
			ret += "┐\n"
			ret += "│ " + data.encode("utf8") + "\33[" + str(count + 4) + "G│\n└"
			ret += "─" * (count + 2)
			ret += "┘"
		else:
			ret += "●"
			ret += "─" * 52
			ret += "┐\n"
			for line in lines:
				ret += "│ " + line.encode("utf8") + "\33[54G│\n"
			ret += "└"
			ret += "─" * 52
			ret += "┘"
	else:
		if count == 0:
			count = 50
		if len(lines) == 1:
			ret += "\33[" + str(80 - count - 4) + "G┌"
			ret += "─" * (count + 2)
			ret += "┐\n"
			ret += "\33[" + str(80 - count - 4) + "G│ " + data.encode("utf8") + "\33[79G│\n\33[" + str(80 - count - 4) + "G└"
			ret += "─" * (count + 2)
			ret += "●"
		else:
			ret += "\33[26G┌"
			ret += "─" * 52
			ret += "┐\n"
			for line in lines:
				ret += "\33[26G│ " + line.encode("utf8") + "\33[79G│\n"
			ret += "\33[26G└"
			ret += "─" * 52
			ret += "●"
	last_row = len(lines) + 2
	return ret

class TMsg(threading.Thread):
	def run(self):
		global udp_client, BUFSIZE, row, last_row, last_message, last_time, heart_beat_count, history_fd
	
		try:
			while True:
				data, addr = udp_client.recvfrom(BUFSIZE)
				if addr != ADDR:
					continue
				
				if data == "":
					continue
			
				if data == '\xFE\xDC\xBA':
					if heart_beat_count >= 5:
						print_in_mid("Connected with Host!", isInfo = True)
						os.system("wmctrl -F -a PyChat")
					heart_beat_count = 0
				else:
					aes = AES.new(b'fuck your ass!??', AES.MODE_CBC, b'who is daddy!!??')
					data = aes.decrypt(data).rstrip('\0')
					if data[0] == '\0' and data[1] != '\0':
						data = data[1:]
						
						aes = AES.new(b'fuck your ass!??', AES.MODE_CBC, b'who is daddy!!??')
						udp_client.sendto(aes.encrypt("\0\0" + data[:data.find('\0')] + "\0" * (16 - (2 + data.find('\0')) % 16)), ADDR)
						data = data[data.find('\0') + 1:]
			
						if (datetime.datetime.now() - last_time).seconds > 300:
							last_time = datetime.datetime.now()
							print_in_mid(datetime.datetime.strftime(last_time, '%Y-%m-%d %H:%M:%S'))

						sys.stdout.write('\33[s\33[' + str(row) + ';1H\33[34m' + wrap(data, True) + '\33[0m\n\33[u')
						sys.stdout.flush()
						history_fd.write("<" + data + "\n")
						row = row + last_row
						if row > 20:
							row = 20
						os.system("wmctrl -F -a PyChat")
					elif data[0:2] == b"\0\0":
						data = data[2:].rstrip("\0")
						if int(data) == last_message:
							last_message = None
		except Exception, e:
			os.popen("zenity --error --text=\"" + str(e) + "\"")
			sys.exit(1)

class TInput(threading.Thread):
	data = ""
	
	def run(self):
		global udp_client, ADDR, file_trans, row, last_row, message_flag, last_message, last_time, history_fd
	
		try:
			while True:
				data = raw_input()
				if last_message != None:
					sys.stdout.write('\33[22;1H')
					sys.stdout.flush()
					print_in_mid("Last message didn't reply, maybe lost.", isInfo = True)
					last_message = None
				if data == "":
					sys.stdout.write('\33[22;1H')
					sys.stdout.flush()
				else:
					if data == "@history" or data == "@h":
						sys.stdout.write("\33[22;1H\33[2K\33[23;1H\33[2K\33[24;1H\33[2K\33[22;1H")
						sys.stdout.flush()
						os.system("gnome-terminal --title 历史记录 --hide-menubar -e 'sh -c \"" + cur_file_dir() + "/chatClient.py --history\"'")
					elif data == "@file" or data == "@f":
						sys.stdout.write("\33[22;1H\33[2K\33[23;1H\33[2K\33[24;1H\33[2K\33[22;1H")
						sys.stdout.flush()
						paths = os.popen("zenity --title=PyChat-文件传输 --file-selection --multiple").read().strip("\n")
						if paths != "":
							file_trans.send_file(paths)
					elif data == "@i" or data == "@image":
						sys.stdout.write("\33[22;1H\33[2K\33[23;1H\33[2K\33[24;1H\33[2K\33[22;1H")
						sys.stdout.flush()
						paths = os.popen("zenity --title=PyChat-图片传输 --file-selection --multiple --file-filter=\"BMP/JPG/JPEG/PNG/GIF|*.BMP *.bmp *.JPG *.jpg *.JPEG *.jpeg *.PNG *.png *.GIF *.gif\"").read().strip("\n")
						if paths != "":
							file_trans.send_image(paths)
					elif data == "@s" or data == "@screenshot":
						sys.stdout.write("\33[22;1H\33[2K\33[23;1H\33[2K\33[24;1H\33[2K\33[22;1H")
						sys.stdout.flush()
						os.system("mkdir -p ~/Pictures/PyChat/ScreenShot")
						paths = os.getenv("HOME") + "/Pictures/PyChat/ScreenShot/" + datetime.datetime.strftime(last_time, '%Y-%m-%d %H:%M:%S') + ".png"
						os.system("gnome-screenshot -a -f \"" + paths + "\" 1>&- 2>&-; sleep 1")
						file_trans.send_image(paths)
					elif data == "@v" or data == "@video":
						sys.stdout.write("\33[22;1H\33[2K\33[23;1H\33[2K\33[24;1H\33[2K\33[22;1H")
						sys.stdout.flush()
						if not instant_camera.started:
							instant_camera.tostart = True
					else:
						last_message = message_flag
						message_flag += 1
						
						sys.stdout.write("\33[22;1H\33[2K\33[23;1H\33[2K\33[24;1H\33[2K\33[22;1H")
						sys.stdout.flush()
						
						if (datetime.datetime.now() - last_time).seconds > 300:
							last_time = datetime.datetime.now()
							print_in_mid(datetime.datetime.strftime(last_time, '%Y-%m-%d %H:%M:%S'))
					
						aes = AES.new(b'fuck your ass!??', AES.MODE_CBC, b'who is daddy!!??')
						udp_client.sendto(aes.encrypt('\0' + str(last_message) + '\0' + data + '\0' * (16 - (len(data) + 2 + len(str(message_flag))) % 16)), ADDR)
						
						sys.stdout.write('\33[' + str(row) + ';1H' + wrap(data, False) + '\n\33[22;1H')
						sys.stdout.flush()
						history_fd.write(">" + data + "\n")
						row = row + last_row
						if row > 20:
							row = 20
		except Exception, e:
			os.popen("zenity --error --text=\"" + str(e) + "\"")
			sys.exit(1)

class file_trans(threading.Thread):
	def run(self):
		global tcp_server

		try:
			while True:
				tcpconn, tcpaddr = tcp_server.accept()
				data = tcpconn.recv(BUFSIZE)
				if data[0] == "\xFF":
					name_sizes = data[1:].split("||")
					for i in range(len(name_sizes)):
						name_sizes[i] = name_sizes[i].split("|")
					command = "zenity --title=PyChat --width=600 --height=400 --list --checklist --multiple --text=文件传输请求 --column=\"\" --column=序号 --column=文件名 --column=文件大小 "
					i = 1
					for name_size in name_sizes:
						command += "TRUE " + str(i) + " \"" + name_size[0] + "\" " + self.sizefbyte(int(name_size[1]))
						i += 1
					selections = os.popen(command).read().strip("\n")
					if selections == "":
						tcpconn.close()
						continue
					save_dir = os.popen("zenity --title=文件保存目录 --file-selection --directory").read().strip("\n")
					if save_dir == "":
						tcpconn.close()
						continue
					tcpconn.sendall(selections)
					progress = subprocess.Popen("zenity --title=PyChat --progress --text=\"waiting...\" --auto-close", shell = True, stdin = subprocess.PIPE)
					total_size = 0
					now_size = 0
					for selection in selections.split("|"):
						total_size += int(name_sizes[int(selection) - 1][1])
					for selection in selections.split("|"):
						name_size = name_sizes[int(selection) - 1]
						while os.path.exists(save_dir + "/" + name_size[0]):
							name_size[0] = "new_" + name_size[0]
						name_size[1] = int(name_size[1])
						if progress.poll() == None:
							progress.stdin.write("#" + name_size[0] + "\n")
							progress.stdin.flush()
							save_fd = open(save_dir + "/" + name_size[0], "wb")
							while name_size[1] > BUFSIZE:
								if progress.poll() != None:
									break
								data = tcpconn.recv(BUFSIZE)
								if data == "":
									os.system("zenity --error --text=\"传送失败: " + name_size[0] + "\"")
									progress.kill()
								save_fd.write(data)
								name_size[1] -= BUFSIZE
								now_size += BUFSIZE
								progress.stdin.write(str(100 - int(math.ceil((total_size - now_size) * 100.0 / total_size))) + "\n")
								progress.stdin.flush()
							if progress.poll() == None:
								data = tcpconn.recv(name_size[1])
								if data == "":
									os.system("zenity --error --text=\"传送失败: " + name_size[0] + "\"")
									progress.kill()
								save_fd.write(data)
								now_size += name_size[1]
								progress.stdin.write(str(100 - int(math.ceil((total_size - now_size) * 100.0 / total_size))) + "\n")
								progress.stdin.flush()
						if progress.poll() == None or progress.poll() == 0:
							save_fd.flush()
							save_fd.close()
						else:
							save_fd.close()
							os.system("rm -f \"" + save_dir + "/" + name_size[0] + "\"")
							break
				elif data[0] == "\xEE":
					name_sizes = data[1:].split("||")
					for i in range(len(name_sizes)):
						name_sizes[i] = name_sizes[i].split("|")
					command = "zenity --title=PyChat --width=600 --height=400 --list --checklist --multiple --text=图片传输请求 --column=\"\" --column=序号 --column=文件名 "
					i = 1
					for name_size in name_sizes:
						command += "TRUE " + str(i) + " \"" + name_size[0] + "\" "
						i += 1
					selections = os.popen(command).read().strip("\n")
					if selections == "":
						tcpconn.close()
						continue
					os.system("mkdir -p ~/Pictures/PyChat")
					save_dir = os.getenv("HOME") + "/Pictures/PyChat"
					if save_dir == "":
						tcpconn.close()
						continue
					tcpconn.sendall(selections)
					for selection in selections.split("|"):
						name_size = name_sizes[int(selection) - 1]
						while os.path.exists(save_dir + "/" + name_size[0]):
							name_size[0] = "new_" + name_size[0]
						name_size[1] = int(name_size[1])
						save_fd = open(save_dir + "/" + name_size[0], "wb")
						while name_size[1] > BUFSIZE:
							data = tcpconn.recv(BUFSIZE)
							if data == "":
								os.system("zenity --error --text=\"传送失败: " + name_size[0] + "\"")
								data = None
								break
							save_fd.write(data)
							name_size[1] -= BUFSIZE
						if not data:
							save_fd.close()
							os.system("rm -f \"" + save_dir + "/" + name_size[0] + "\"")
							break
						data = tcpconn.recv(name_size[1])
						if data == "":
							os.system("zenity --error --text=\"传送失败: " + name_size[0] + "\"")
							save_fd.close()
							os.system("rm -f \"" + save_dir + "/" + name_size[0] + "\"")
							break
						save_fd.write(data)
						save_fd.flush()
						save_fd.close()
						os.system("xdg-open \"" + save_dir + "/" + name_size[0] + "\" 1>&- 2>&-")
				tcpconn.close()
		except Exception, e:
			os.popen("zenity --error --text=\"" + str(e) + "\"")
			sys.exit(1)
					
	
	def send_file(self, paths):
		global ADDR, PORT

		files = paths.split("|")
		tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tcp_client.connect((ADDR[0], PORT + 1))
		data = ""
		for f in files:
			data += f[f.rfind("/") + 1:] + "|"
			data += str(os.path.getsize(f)) + "||"
		tcp_client.sendall("\xFF" + data[:-2])
		selections = tcp_client.recv(BUFSIZE)
		if selections == "":
			tcp_client.close()
			return
		for selection in selections.split("|"):
			try:
				tcp_client.sendall(open(files[int(selection) - 1]).read())
			except Exception, e:
				os.system("zenity --error --text=\"传送失败: " + files[int(selection) - 1] + "\"")
				tcp_client.close()
		tcp_client.close()
	
	def send_image(self, paths):
		global ADDR, PORT

		files = paths.split("|")
		tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tcp_client.connect((ADDR[0], PORT + 1))
		data = ""
		for f in files:
			data += f[f.rfind("/") + 1:] + "|"
			data += str(os.path.getsize(f)) + "||"
		tcp_client.sendall("\xEE" + data[:-2])
		selections = tcp_client.recv(BUFSIZE)
		if selections == "":
			tcp_client.close()
			return
		for selection in selections.split("|"):
			try:
				tcp_client.sendall(open(files[int(selection) - 1]).read())
			except Exception, e:
				os.system("zenity --error --text=\"传送失败: " + files[int(selection) - 1] + "\"")
				tcp_client.close()
		tcp_client.close()
	
	def sizefbyte(self, byte_count):
		if byte_count / 1024 == 0:
			return "{0:d}\\ B ".format(byte_count)
		elif byte_count / (1024 * 1024) == 0:
			return "{0:.1f}\\ KB ".format(byte_count / 1024.0)
		elif byte_count / (1024 ** 3) == 0:
			return "{0:.1f}\\ MB ".format(byte_count / (1024.0 * 1024.0))
		else:
			return "{0:.1f}\\ GB ".format(byte_count / (1024.0 ** 3))

class InstVideo(threading.Thread):
	surface_buffer = ""
	new_surface = None
	video_surface = None
	
	started = False
	
	def __init__(self):
		threading.Thread.__init__(self)
		pygame.display.init()
	
	def __del__(self):
		pygame.display.quit()
	
	def run(self):
		global video_server, instant_camera
		
		try:
			while True:
				count = 0
				tcpconn, tcpaddr = video_server.accept()
				data = tcpconn.recv(BUFSIZE)
				if not self.started and data[:4] == "@beg":
					self.surface_buffer = ""
					self.new_surface = None
					self.video_surface = None
					self.started = True
					
#					if not instant_camera.started:
#						instant_camera.tostart = True
					
					pygame.display.init()
					pygame.display.set_caption("PyChat")
					pygame.display.set_icon(pygame.image.load("/usr/share/icons/hicolor/256x256/apps/cheese.png"))
					self.video_surface = pygame.display.set_mode((320, 240), 0, 24)
					self.surface_buffer += data[4:]
					count += BUFSIZE - 4
					running = True
					while running:
						data = tcpconn.recv(BUFSIZE)
						if data == "" or data[:4] == "@end":
							break
						if 230400 - count >= BUFSIZE:
							self.surface_buffer += data
							count += BUFSIZE
						else:
							self.surface_buffer += data[:230400 - count]
							count = 0
							self.new_surface = pygame.image.fromstring(self.surface_buffer, (320, 240), "RGB")
							self.surface_buffer = ""
							self.video_surface.blit(self.new_surface, (0, 0))
							pygame.display.update()
						for event in pygame.event.get():
							if event.type == pygame.QUIT:
								running = False
								break
					pygame.display.quit()
					self.surface_buffer = ""
					self.new_surface = None
					self.video_surface = None
					self.started = False
				tcpconn.close()
		except Exception, e:
			os.popen("zenity --error --text=\"" + str(e) + "\"")
			sys.exit(1)

class InstCamera(threading.Thread):
	cam = None
	
	started = False
	tostart = False
	toend = False
	
	def __init__(self):
		threading.Thread.__init__(self)
		pygame.camera.init()
		self.cam = pygame.camera.Camera(pygame.camera.list_cameras()[0], (320, 240), "RGB")
	
	def __del__(self):
		if self.cam and self.started:
			try:
				self.cam.stop()
			except Exception:
				pass
		pygame.camera.quit()
	
	def run(self):
		try:
			while True:
				if not self.started and not self.tostart:
					time.sleep(0.25)
				elif not self.started and self.tostart:
					self.cam.start()
					self.started = True
					self.tostart = False
				elif self.started and not self.toend:
					cam_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					cam_client.connect((ADDR[0], PORT - 1))
					try:
						cam_client.sendall("@beg" + pygame.image.tostring(self.cam.get_image(), "RGB") + '\0' * (BUFSIZE - (230400 + 4) % BUFSIZE))
						time.sleep(0.25)
						while not self.toend:
							cam_client.sendall(pygame.image.tostring(self.cam.get_image(), "RGB") + '\0' * (BUFSIZE - 230400 % BUFSIZE))
							time.sleep(0.25)
					except Exception:
						self.toend = True
				elif self.started and self.toend:
					try:
						cam_client.sendall("@end")
					except Exception:
						pass
					cam_client.close()
					self.cam.stop()
					self.started = False
					self.tostart = False
					self.toend = False
				else:
					self.started = False
					self.tostart = False
					self.toend = False
		except Exception, e:
			os.popen("zenity --error --text=\"" + str(e) + "\"")
			sys.exit(1)

class HeartBeat(threading.Thread):
	def run(self):
		global udp_client, ADDR, heart_beat_count
		
		while True:
			if heart_beat_count < 5:
				udp_client.sendto('\xAB\xCD\xEF', ADDR)
				heart_beat_count += 1
			elif heart_beat_count == 5:
				print_in_mid("Diconnected with Host!", isInfo = True)
				heart_beat_count = 6
				os.system("wmctrl -F -a PyChat")
			else:
				udp_client.sendto('\xAB\xCD\xEF', ADDR)
			time.sleep(5)

def main(argv):
	global HOST, ADDR, udp_client, tcp_server, video_server, file_trans, instant_camera, row, last_time, history_fd
	
	ADDR = (HOST, PORT)
	
	history_fd = open(os.getenv("HOME") + "/.chat_history.dat", "a+")
	
	if len(argv) > 0:
		if argv[0] == "--history":
			os.system("resize -s 24 80 > /dev/null")
			history_fd.seek(0,0)
			for line in history_fd.readlines():
				if line[0] == "<":
					sys.stdout.write('\33[' + str(row) + ';1H\33[34m' + wrap(line[1:].rstrip("\n"), True) + '\33[0m\n')
					sys.stdout.flush()
					row = row + last_row
					if row > 24:
						row = 24
				elif line[0] == ">":
					sys.stdout.write('\33[' + str(row) + ';1H' + wrap(line[1:].rstrip("\n"), False) + '\n')
					sys.stdout.flush()
					row = row + last_row
					if row > 24:
						row = 24
				elif line[0] == "@":
					print_in_mid(line[1:], False)
				else:
					print "\33[31m历史记录文件损坏！\33[0m\n"
					break
			raw_input("回车键退出。。。")
			history_fd.close()
			sys.exit(0)
	
	os.system("resize -s 24 80 > /dev/null")
	ip = raw_input("输入主机IP：（默认" + str(HOST) + "）")
	if ip != '':
		if len(ip) > 15:
			ip = ip[:15]
		ADDR = (ip, ADDR[1])
		thefd = open(cur_file_dir() + "/chatClient.py", "r+")
		content = thefd.read()
		thefd.seek(content.find("HOST = ") + 8, 0)
		thefd.write(ip + "' #")
		thefd.flush()
		thefd.close()
	
	signal.signal(signal.SIGINT, sig_hdr)
	signal.signal(signal.SIGTERM, sig_hdr)
	
	tcp_server.bind(("0.0.0.0", PORT + 2))
	tcp_server.listen(10)
	
	video_server.bind((ADDR[0], PORT - 2))
	video_server.listen(1)

	last_time = datetime.datetime.now()
	
	sys.stdout.write('\33[2J\33[1;20r\33[21;1H--------------------------------------------------------------------------------\33[22;1H')
	sys.stdout.flush()
	print_in_mid(datetime.datetime.strftime(last_time, '%Y-%m-%d %H:%M:%S'))
	
	tMsg = TMsg()
	tInput = TInput()
	file_trans = file_trans()
	instant_video = InstVideo()
	instant_camera = InstCamera()
	heartBeat = HeartBeat()
	tMsg.setDaemon(True)
	tInput.setDaemon(True)
	file_trans.setDaemon(True)
	instant_video.setDaemon(True)
	instant_camera.setDaemon(True)
	heartBeat.setDaemon(True)
	tMsg.start()
	tInput.start()
	file_trans.start()
	instant_video.start()
	instant_camera.start()
	heartBeat.start()
	while tMsg.isAlive() and tInput.isAlive() and file_trans.isAlive() and instant_video.isAlive() and instant_camera.isAlive() and heartBeat.isAlive():
		time.sleep(1)

if __name__ == "__main__":
	try:
		main(sys.argv[1:])
	except Exception, e:
		os.popen("zenity --error --text=\"" + str(e) + "\"")
		sys.exit(1)
