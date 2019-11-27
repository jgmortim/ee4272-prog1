###############################################################################
# Name: server.py                                                             #
# Author: John Mortimore                                                      #
# Original:  09/30/2019                                                       #
# Moddified: 10/04/2019                                                       #
#                                                                             #
# POP3 server. Implements all minimal implementation TRANSACTION state POP3   #
# commands as dictated by RFC1081 (STAT, LIST, RETR, DELE, NOOP, LAST, RSET)  # 
# and the UPDATE state command QUIT. Also implements one optional TRANSACTION #
# state command (TOP). AUTHORIZATION state commands are beyond the scope of   #
# this assignment.                                                            #
###############################################################################

from socket import *
import sys
import glob
import re
import os

###############################################################################
# Class: Mail                                                                 #
# Description: An object that represents an email                             #
###############################################################################
class Mail:
	def __init__(self, toAddr, fromAddr, subject, date, content, mailID, filename):
		self.toAddr = toAddr
		self.fromAddr = fromAddr
		self.subject = subject
		self.date = date
		self.content = content
		self.mailID = mailID
		self.filename = filename
		self.delete = False		# True if email marked as deleted

###############################################################################
# Func: GetMail                                                               #
# Desc: Loads all of the emails in the same directory as the server and       #
#       returns a list of the emails.                                         #
# Args: N/A                                                                   #
# Retn: {list} - list of emails                                               #
###############################################################################
def GetMail():
	emailList = []
	emailCount = 0
	for file in glob.glob("*.eml"):
		emailCount += 1
		content = []
		toAd=''
		fromAd=''
		subj=''
		date=''
		for line in open(file, 'r'):
			if 'To: ' in line:
				 toAd=line.split('To: ')[1]
			elif 'From: ' in line:
				 fromAd=line.split('From: ')[1]
			elif 'Subject: ' in line:
				 subj=line.split('Subject: ')[1]
			elif 'Date: ' in line:
				 date=line.split('Date: ')[1]
			else:
				content.append(line)
		content.pop(0) 					# remove the empty line
		emailList.append(Mail(toAd, fromAd, subj, date, content, emailCount, str(file)))
	return emailList

###############################################################################
# Func: CommandSTAT                                                           #
# Desc: Implements the STAT command as defined by RFC 1081.                   #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def CommandSTAT():
	length = 0
	count = 0
	for mail in inBox:						# For each email:
		if mail.delete == False:			# If the mail has not been marked as deleted,
			count += 1						# Count the mail
			for line in mail.content:		# and add length of email to total length.
				length += len(line)
	response='+OK ' + str(count)+' '+str(length)
	connectionSocket.send(response.encode())

###############################################################################
# Func: CommandLIST                                                           #
# Desc: Implements the LIST command (see RFC 1081), but does not implement    #
#       LIST [msg].                                                           #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def CommandLIST():
	response = []
	totalLength = 0
	count = 0
	for mail in inBox:					# For each email:
		if mail.delete == False:		# If the mail has not been marked as deleted,
			count += 1					# Count the mail
			length = 0					
			for line in mail.content:	# and
				length += len(line)		# measure length of email
			totalLength += length		# and add that to the combined length.
			response.append(str(mail.mailID) + " " + str(length) + "\n")
	response.insert(0,"+OK "+str(count)+" messages ("+str(totalLength)+" octets)\n")
	response.append(".")
	connectionSocket.send(("".join(response)).encode())

###############################################################################
# Func: CommandRETR                                                           #
# Desc: Implements the RETR [msg] command as defined by RFC 1081.             #
# Args: msgID {int} - the number of the message to return                     #      
# Retn: N/A                                                                   #
###############################################################################
def CommandRETR(msgID):
	global highestNumberAccessed
	response = []
	size = 0
	found = False
	for mail in inBox:									# For each email:
		if mail.delete == False:						# If it has not be marked as deleted,
			if int(mail.mailID) == int(msgID):			# and has the correct message id.
				found = True
				if int(msgID) > int(highestNumberAccessed):	# Change HNA if necessary.
					highestNumberAccessed = msgID
				# Create and send response. #
				response.append("To: " + str(mail.toAddr))
				response.append("From: " + str(mail.fromAddr))
				response.append("Subject: " + str(mail.subject))
				response.append("Date: " + str(mail.date))
				response.append("\n")
				for line in mail.content:
					response.append(line)
					size += len(line)
				response.insert(0,"+OK " + str(size) + " octets\n")
				response.append(".")
				connectionSocket.send(("".join(response)).encode())
				break
	if found == False:									# If email does not exist.
		response.append("-ERR no such message")
		connectionSocket.send(("".join(response)).encode())

###############################################################################
# Func: CommandDELE                                                           #
# Desc: Implements the DELE [msg] command as defined by RFC 1081.             #
# Args: msgID {int} - the number of the message to return                     # 
# Retn: N/A                                                                   #
###############################################################################
def CommandDELE(msgID):
	global inBox, highestNumberAccessed
	found = False
	for mail in inBox:							# For each email:
		if mail.delete == False:				# If it has not been marked as deleted,
			if int(mail.mailID) == int(msgID):	# and has the correct message id.
				found = True
				if int(msgID) > int(highestNumberAccessed):	# Change HNA if necessary.
					highestNumberAccessed = msgID
				mail.delete = True							# Mark as deleted.
				response = "+OK message " + str(msgID) + " deleted"
	if found == False:							# If email does not exist.
		response = "-ERR no such message"
	connectionSocket.send(response.encode())


###############################################################################
# Func: CommandNOOP                                                           #
# Desc: Implements the NOOP command as defined by RFC 1081.                   #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def CommandNOOP():
	response = "+OK"
	connectionSocket.send(response.encode())

###############################################################################
# Func: CommandLAST                                                           #
# Desc: Implements the LAST command as defined by RFC 1081.                   #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def CommandLAST():
	response = "+OK " + str(highestNumberAccessed)
	connectionSocket.send(response.encode())

###############################################################################
# Func: CommandRSET                                                           #
# Desc: Implements the RSET command as defined by RFC 1081.                   #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def CommandRSET():
	global inBox, highestNumberAccessed
	for mail in inBox:				# For each email:
		if mail.delete == True:		# If the mail has been marked as deleted,
			mail.delete = False		# remove mark.
	highestNumberAccessed = 0		# Reset the highest number accessed.
	response = "+OK"
	connectionSocket.send(response.encode())

###############################################################################
# Func: CommandTOP                                                            #
# Desc: Implements the TOP command as defined by RFC 1081.                    #
# Args: msgID {int} - the number of the message to return                     # 
#       numLines {int} - number of lines of email to send                     #
# Retn: N/A                                                                   #
###############################################################################
def CommandTOP(msgID, numLines):
	global highestNumberAccessed
	response = []
	size = 0
	found = False
	for mail in inBox:									# For each email:
		if mail.delete == False:						# If it has not be marked as deleted,
			if int(mail.mailID) == int(msgID):			# and has the correct message id.
				found = True
				if int(msgID) > int(highestNumberAccessed):	# Change HNA if necessary.
					highestNumberAccessed = msgID
				# Create and send response. #
				response.append("To: " + str(mail.toAddr))
				response.append("From: " + str(mail.fromAddr))
				response.append("Subject: " + str(mail.subject))
				response.append("Date: " + str(mail.date))
				response.append("\n")
				for line in mail.content[:int(numLines)]:
					response.append(line)
					size += len(line)
				response.insert(0,"+OK " + str(size) + " octets\n")
				response.append(".")
				connectionSocket.send(("".join(response)).encode())
				break
	if found == False:									# If email does not exist.
		response.append("-ERR no such message")
		connectionSocket.send(("".join(response)).encode())

###############################################################################
# Func: CommandQUIT                                                           #
# Desc: Implements the QUIT command as defined by RFC 1081.                   #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def CommandQUIT():
	response='+OK Adios'						# Create response.
	connectionSocket.send(response.encode())	# Send response.
	connectionSocket.close()					# Close the socket.
	print("Connection terminated")
	UpdateState()

###############################################################################
# Func: UpdateState                                                           #
# Desc: Implements the Update State as defined by RFC 1081.                   #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def UpdateState():
	for mail in inBox:					# For each email:
		if mail.delete == True:			# If it has been marked as deleted,
			os.remove(mail.filename)	# delete the file from the system.

###############################################################################
serverPort = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)
print("server listening on port", serverPort)
while True:											# Run Forever.
	connectionSocket, addr = serverSocket.accept() 	# Accept a client connection.
	print("Connection accepted")
	inBox = GetMail()								# Load the mail.
	highestNumberAccessed = 0						# Initialized to 0.
	regexRETR = re.compile("^RETR \d+$") 			# Define syntax for RETR.
	regexDELE = re.compile("^DELE \d+$") 			# Define syntax for DELE.
	regexTOP = re.compile("^TOP \d+ \d+$") 			# Define syntax for TOP.
	while True: 									# Maintain connection with client.
		command = connectionSocket.recv(2048).decode()	# Recieve a command from client.
		if command == 'STAT':						# STAT
			CommandSTAT()
		elif command == 'LIST':						# LIST
			CommandLIST()
		elif regexRETR.search(command):				# RETR [msg]
			reqID=command.split(" ")[1]
			CommandRETR(reqID)
		elif regexDELE.search(command):				# DELE [msg]
			delID=command.split(" ")[1]
			CommandDELE(delID)
		elif regexTOP.search(command):				# TOP [msg] [lines]
			msgID=command.split(" ")[1]
			numLines=command.split(" ")[2]
			CommandTOP(msgID, numLines)
		elif command == 'QUIT':						# QUIT
			CommandQUIT()
			break		# To listen for new connection
		elif command == 'NOOP':						# NOOP
			CommandNOOP()
		elif command == 'RSET':						# RSET
			CommandRSET()
		elif command == 'LAST':						# LAST
			CommandLAST()
		else:										# Unkown
			response="-ERR"
			connectionSocket.send(response.encode())



