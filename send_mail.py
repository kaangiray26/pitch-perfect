#!/usr/bin/python
import os
import pgpy
import email, smtplib, ssl
import json
from os.path import normpath as n
from smtplib import SMTPAuthenticationError
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

class AuthenticationError(Exception):
  pass

class outbox:
  def __init__(self):
    self.refresh_data()
    self.available_keys = os.listdir("pgp_keys")
    self.otp_keys = os.listdir("otp_keys")
    self.from_adress = self.credentials("id")
    self.getServerSettings()

  def refresh_data(self):
    with open('config.json',) as self.f:
      self.data = json.load(self.f)

  def getServerSettings(self):
    self.emailService = self.credentials("server")
    self.s = open('mailservers.json',)
    self.servers = json.load(self.s)
    self.smtp_host = self.servers[self.emailService]["smtp"]["server"]
    self.smtp_port = self.servers[self.emailService]["smtp"]["port"]
    self.smtp_encryption = self.servers[self.emailService]["smtp"]["encryption"]

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

  # Find private pgp key
  def find_secret(self, sender):
    for k in self.available_keys:
      if sender in k and "secret" in k:
        key, _ = pgpy.PGPKey.from_file(n(os.path.join('pgp_keys',k)))
        return key

  # Find public pgp key
  def find_public(self, receiver):
    for k in self.available_keys:
      if receiver in k and "public" in k:
        print(k)
        key, _ = pgpy.PGPKey.from_file(n(os.path.join('pgp_keys',k)))
        return key

  def find_offset(self, email_addr):
    self.refresh_data()
    for k in self.otp_keys:
      if email_addr in k:
        offset = self.data["OTP"][email_addr]
        return offset

  # Find otp key
  def find_key(self, email_addr):
    self.refresh_data()
    for k in self.otp_keys:
      if email_addr in k:
        offset = self.data["OTP"][email_addr]
        with open(n(os.path.join('otp_keys', k)),) as f:
          keydata = json.load(f)
          return keydata[str(offset)]

  # Update otp offset
  def update_offset(self, email_addr):
    self.refresh_data()
    self.data["OTP"][email_addr] += 1
    with open('config.json', 'w') as conf:
      json.dump(self.data, conf, indent=4)
  
  # Encrypt with otp
  def otp_encrypt(self, plain_message):
    key = self.find_key(self.from_adress).encode()
    encoded_msg = plain_message.encode()
    return bytes([key[i] ^ encoded_msg[i] for i in range(len(encoded_msg))])

  def send(self, subject, to, content, isEncrypted):
    m_subject        = subject
    m_sender_email   = self.from_adress
    m_receiver_email = to

    context = ssl.create_default_context()
    if self.smtp_encryption == "SSL":
      server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context)
    elif self.smtp_encryption == "STARTTLS":
      server = smtplib.SMTP(self.smtp_host, self.smtp_port)
      server.starttls(context=context)
    try:
      server.login(self.credentials("username"), self.credentials("password"))
    except SMTPAuthenticationError:
      raise AuthenticationError('Provided credentials are incorrect.')

    if isEncrypted:
      msg = MIMEMultipart(_subtype='encrypted', protocol='application/pgp-encrypted')
      msg['X-secretMetadata'] = "pitch-perfect"
      msg['X-magicNumber'] = str(self.find_offset(self.from_adress))
      msg['Subject'] = m_subject
      msg['To'] = m_receiver_email
      msg['From'] = m_sender_email

      enc = MIMEBase('application', 'pgp-encrypted')
      msg.attach(enc)
      enc_part = MIMEBase('application','octet-stream', name='encrypted.asc')

      # OTP Section
      content = self.otp_encrypt(content)
      #

      pgp_message = pgpy.PGPMessage.new(content)
      privkey = self.find_secret(m_sender_email)
      with privkey.unlock(self.credentials("passphrase")):
        pubkey = privkey.pubkey
        pgp_message |= privkey.sign(pgp_message)
      encrypted = pubkey.encrypt(pgp_message)
      enc_part.set_payload(str(encrypted))
      msg.attach(enc_part)
    else:
      msg = MIMEText(content)
      msg['Subject'] = m_subject
      msg['To'] = m_receiver_email
      msg['From'] = m_sender_email

    server.sendmail(m_sender_email, m_receiver_email, msg.as_string())

    # Update own offset
    if isEncrypted:
      self.update_offset(self.from_adress)
    return
