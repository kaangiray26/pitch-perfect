#!/usr/bin/python
#-*- encoding:utf-8 -*-
import os
import pgpy
import json
from os.path import normpath as n

class DecryptionError(Exception):
  pass

class decryption:
  def __init__(self):
    self.refresh_data()
    self.available_keys = os.listdir("pgp_keys")
    self.otp_keys = os.listdir("otp_keys")

    for k in self.available_keys:
      if self.credentials("username") in k and "secret" in k:
        self.privkey, _ = pgpy.PGPKey.from_file(n(os.path.join('pgp_keys',k)))

  def refresh_data(self):
    with open('config.json',) as self.f:
      self.data = json.load(self.f)

  def credentials(self, arg):
    self.refresh_data()
    if arg == "name":
      return self.data["USERINFO"]["name"]
    elif arg == "username":
      return self.data["USERINFO"]["username"]
    elif arg == "password":
      return self.data["USERINFO"]["password"]
    elif arg == "id":
      return self.data["PGP"]["id"]
    elif arg == "passphrase":
      return self.data["PGP"]["passphrase"]

  # Find otp key
  def find_key(self, email_addr, offset):
    self.refresh_data()
    for k in self.otp_keys:
      if email_addr in k:
        with open(n(os.path.join('otp_keys',k)), 'r') as f:
          key = f.read().splitlines()[int(offset)]
        return key

  # Encrypt with otp
  def otp_decrypt(self, encrypted_message, from_addr, offset):
    key = self.find_key(from_addr, offset).encode()
    return bytes([key[i] ^ encrypted_message[i] for i in range(len(encrypted_message))])

  def decryptMessage(self, msg, from_addr, magicNumber):
    message_from_blob = pgpy.PGPMessage.from_blob(msg)
    try:
      with self.privkey.unlock(self.credentials("passphrase")):
        decrypted_message = self.privkey.decrypt(message_from_blob)
    except pgpy.errors.PGPError:
      raise DecryptionError(
          'Cannot decrypt the provided message with this key')

    byte_message = decrypted_message.message
    return self.otp_decrypt(byte_message, from_addr, magicNumber).decode()
