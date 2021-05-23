#!/usr/bin/python
#-*- encoding:utf-8 -*-

import os
import sys
import time
import email
import imaplib
import json
import base64
import datetime
from secrets import token_urlsafe
from os.path import normpath as n
from email.header import Header, decode_header, make_header

# Reading Config file
class WizardError(Exception):
  pass

class inbox():
  def __init__(self):
    self.check_config()
    self.refresh_data()

    self.getServerSettings()
    self.mail = imaplib.IMAP4_SSL(self.SERVER)
    self.mail.login(self.credentials("username"), self.credentials("password"))
    self.mail.select('inbox')

    self.local_emails = []
    self.loaded = False
    self.doExit = False

  def check_config(self):
    if "local.json" not in os.listdir("archive"):
      with open(os.path.join('archive', 'local.json'), 'a+') as conf:
        toAdd = {"EMAILS": [], "LAST_CHECK": 0}
        json.dump(toAdd, conf, indent=4)
        
    if "config.json" not in os.listdir("."):
      raise WizardError("You don't have a config file yet.\n Please run the wizard first!")
    return

  def refresh_data(self):
    with open('config.json',) as self.f:
      self.data = json.load(self.f)
    with open(os.path.join('archive','local.json'),) as self.l:
      self.local = json.load(self.l)
      self.local_emails = self.local['EMAILS']

  def getServerSettings(self):
    self.emailService = self.credentials("server")
    self.s = open('mailservers.json',)
    self.servers = json.load(self.s)
    self.SERVER = self.servers[self.emailService]["imap"]["server"]
    self.PORT = self.servers[self.emailService]["imap"]["port"]

  def credentials(self, arg):
    self.refresh_data()
    if arg == "name":
      return self.data["USERINFO"]["name"]
    elif arg == "username":
      return self.data["USERINFO"]["username"]
    elif arg == "password":
      return self.data["USERINFO"]["password"]
    elif arg == "server":
      return self.data["USERINFO"]["server"]
    elif arg == "id":
      return self.data["PGP"]["id"]
    elif arg == "passphrase":
      return self.data["PGP"]["passphrase"]
    elif arg == "init":
      return self.data['INIT']

  def refresh_mail(self):
    self.loaded = False
    self.refresh_data()
    ids = []
    if self.credentials("init") == 0:
      arg = 'ALL'
      command = "self.local_emails.append([(mail_subject, mail_from, mail_date, token_urlsafe(2)), content_type, mail_content, x_header, x_magicnum, attachment_name, attachment])"
      self.data['INIT'] = 1
    else:
      arg = '(UNSEEN)'
      command = "self.local_emails.insert(0,[(mail_subject, mail_from, mail_date, token_urlsafe(2)), content_type, mail_content, x_header, x_magicnum, attachment_name, attachment])"

    self.mail.select('inbox')
    status, data = self.mail.search(None, arg)
    for block in data:
      ids += block.split()
    ids.reverse()
    if arg=='(UNSEEN)':
      print("New messages:",len(ids))
    for item in ids:
      if self.doExit:
        print("exited")
        return
      status, data = self.mail.fetch(item, '(RFC822)')
      for response_part in data:
        if isinstance(response_part, tuple):
          message = email.message_from_bytes(response_part[1])
          mail_from = str(make_header(decode_header(message['from'])))
          try:
            mail_subject = str(make_header(decode_header(message['subject'])))
          except TypeError:
            mail_subject = ""
          date_tuple = email.utils.parsedate_tz(message['Date'])
          if date_tuple:
            local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            mail_date = local_date.strftime("%a, %d %b %Y %H:%M")
          else:
            mail_date = ""
          mail_content = ""
          x_header = ""
          x_magicnum = ""
          if 'X-secretMetadata' in message.keys():
            x_header = message['X-secretMetadata']
          if 'X-magicNumber' in message.keys():
            x_magicnum = message['X-magicNumber']

          # Mail content parsing section
          i = 0
          upperType = None
          attachment = None
          attachment_name = None
          for part in message.walk():
            content_type = part.get_content_type()
            print(content_type)
            if i == 0:
              if content_type == "multipart/alternative":
                upperType = "Alternative"
              elif content_type == "multipart/mixed":
                upperType = "Mixed"
              elif content_type == "multipart/encrypted":
                upperType = "Encrypted"
              elif content_type == "multipart/related":
                upperType = "Mixed"
              elif content_type == "text/html":
                charset = part.get_content_charset()
                mail_content = part.get_payload(decode=True).decode(charset, errors='replace')
                continue
              elif content_type == "text/plain":
                mail_content = part.get_payload()
                continue
              else:
                continue

            if upperType == "Alternative":
              if content_type == "text/plain":
                mail_content = part.get_payload()
              elif content_type == "text/html":
                charset = part.get_content_charset()
                mail_content = part.get_payload(decode=True).decode(
                  charset, errors='replace')

            elif upperType == "Encrypted":
              if content_type == "application/octet-stream":
                mail_content = part.get_payload()

            elif upperType == "Mixed":
              if content_type == "text/plain":
                mail_content = part.get_payload()
              elif content_type == "text/html":
                charset = part.get_content_charset()
                mail_content = part.get_payload(decode=True).decode(
                    charset, errors='replace')
              elif content_type == "application/octet-stream":
                attachment_content = part.get_payload(decode=True)
                attachment_type = part['Content-Transfer-Encoding']
                attachment_name = part.get_filename()
                if attachment_type == "base64":
                  try:
                    attachment = str(base64.b64decode(attachment_content + b'=='))
                  except base64.binascii.Error:
                    continue
                elif attachment_type == None:
                  attachment = attachment_content.decode()
              elif content_type == "application/pdf":
                attachment_content = part.get_payload()
                attachment_type = part['Content-Transfer-Encoding']
                attachment_name = part.get_filename()
                if attachment_type == "base64":
                  attachment = base64.b64decode(attachment_content)
            i += 1
          exec(command)
    with open(os.path.join('archive','local.json'), 'w') as conf:
      self.local['EMAILS'] = self.local_emails
      json.dump(self.local, conf, indent=4)
    with open('config.json', 'w') as conf:
      json.dump(self.data, conf, indent=4)
    self.loaded = True
    print("Synchronization ended.")
    return

  def openmail(self, msg):
    #do thing
    return

