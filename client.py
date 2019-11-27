###############################################################################
# Name: client.py                                                             #
# Author: John Mortimore                                                      #
# Original:  09/30/2019                                                       #
# Moddified: 10/07/2019                                                       #
#                                                                             #
# POP3 client. SYNTAX: client.py [address] [port]                             #
###############################################################################

from socket import *
import sys
import glob
import re

serverName = sys.argv[1]						# Get server address from CLA
serverPort = int(sys.argv[2])					# Get server port from CLA
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

regexRETR = re.compile("^RETR \d+$") 			# Define syntax for RETR.

while True:										# Run until QUIT command
	command = input('C: ')						# Prompt user for command and
	clientSocket.send(command.encode())			# send command to server.
	response = clientSocket.recv(2048)			# Recieve response from server.
	print("S: " + response.decode().replace("\n", "\nS: "))		# Print response.
	if command == 'QUIT':						# If QUIT command,
		break									# break out of infinite loop
	# If command is RETR [msg], save the email locally. #
	if regexRETR.search(command):	
		if "-ERR no such message" not in response.decode():	
			msgID=command.split(" ")[1]				
			fileName = "email"+str(msgID)+".eml"
			email = open(fileName,"w+")
			email.write(response.decode())
			email.close()

# Extra Credit, lacks error handling #
emails = []
for file in glob.glob("*.eml"):
	emails.append(str(file))
print(str(len(emails)) + " email(s) saved locally.")
print('Enter "1" to view email 1, "2" to view email 2, etc. "QUIT" to exit')
while True:
	command = input('C: ')
	if command == 'QUIT':						# If QUIT command,
		break									# break out of infinite loop.
	else: 										# Else, print file
		f=open(str(emails[int(command)-1]), 'r')
		print(f.read())
		f.close

clientSocket.close()							# close the socket.
