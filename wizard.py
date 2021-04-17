#!/usr/bin/python
#-*- encoding: utf-8 -*-
import os
import pgpy
import secrets
import json
from os.path import normpath as n
from pgpy.constants import PubKeyAlgorithm, KeyFlags, HashAlgorithm, SymmetricKeyAlgorithm, CompressionAlgorithm
from os.path import normpath as n
class unsupportedEmailError(Exception):
  pass

class setup:
  def __init__(self):
    self.name = None
    self.username = None
    self.check_config()
    self.refresh_data()
  
  def check_config(self):
    if "config.json" not in os.listdir("."):
      with open('config.json', 'a+') as conf:
        conf.write("{}")
        conf.close()
    if "downloaded" not in os.listdir("."):
      os.mkdir("downloaded")
    if "pgp_keys" not in os.listdir("."):
      os.mkdir("pgp_keys")
    if "otp_keys" not in os.listdir("."):
      os.mkdir("otp_keys")
    return

  def refresh_data(self):
    with open('config.json',) as self.f:
      self.data = json.load(self.f)

  def checkEmailSettings(self, addr):
    addr = addr[addr.rfind("@")+1:]
    if addr == "gmail.com":
      return "GMAIL"
    elif addr == "hotmail.com" or addr == "windowslive.com" or addr == "outlook.com":
      return "OUTLOOK"
    elif addr == "icloud.com":
      return "ICLOUD"
    elif addr == "yahoo.com":
      return "YAHOO"
    elif addr == "yandex.com":
      return "YANDEX"
    elif addr == "gmx.com":
      return "GMX"
    else:
      raise unsupportedEmailError('Email not supported at the moment.')

  def email_setup(self, name, username, password):
    self.refresh_data()
    self.name = name
    self.username = username
    self.password = password
    server = self.checkEmailSettings(self.username)
    toAdd = {}
    toAdd["USERINFO"] = {"name": self.name,
                                 "username": self.username, "password": self.password, "server" : server}
    self.data.update(toAdd)
    with open('config.json', 'w') as conf:
      json.dump(self.data, conf, indent=4)
    return "email setup success."
    
  def pgp_setup(self, passphrase):
    self.refresh_data()
    self.passphrase = passphrase
    toAdd = {}
    key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
    uid = pgpy.PGPUID.new(self.name, comment='Pitch Perfect PGP key', email=self.username)
    key.add_uid(uid, usage={KeyFlags.Sign, KeyFlags.EncryptCommunications, KeyFlags.EncryptStorage},
      hashes=[HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512, HashAlgorithm.SHA224],
      ciphers=[SymmetricKeyAlgorithm.AES256, SymmetricKeyAlgorithm.AES192, SymmetricKeyAlgorithm.AES128],
      compression=[CompressionAlgorithm.ZLIB, CompressionAlgorithm.BZ2, CompressionAlgorithm.ZIP, CompressionAlgorithm.Uncompressed])
    subkey = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
    key.add_subkey(subkey, usage={KeyFlags.Authentication})
    key.protect(self.passphrase, SymmetricKeyAlgorithm.AES256, HashAlgorithm.SHA256)
    toAdd["PGP"] = {"id": self.username, "passphrase": self.passphrase}
    self.data.update(toAdd)
    filename = " ".join(key.userids[0].userid.split()[:-1] + [key.userids[0].userid.split()[-1][1:-1]])
    with open(n(os.path.join("pgp_keys","%s-secret.asc" %(filename))),"w") as f:
      f.write(str(key))
      f.close()
    with open(n(os.path.join("pgp_keys","%s-public.asc" % (filename))), "w") as f:
      pubkey = key.pubkey
      f.write(str(pubkey))
      f.close()
    with open('config.json', 'w') as conf:
      json.dump(self.data, conf, indent=4)
    return "pgp setup success."

  def otp_setup(self):
    self.refresh_data()
    otp_keys = []
    toAdd = {}
    otp_keys.append("signature = %s" %(secrets.token_hex(16)))
    for i in range(0, 1024):
      otp_keys.append(secrets.token_hex(512))
    with open(n(os.path.join("otp_keys","%s-otp.asc" %(self.username))), mode='wt', encoding='utf-8') as f:
      f.write(os.linesep.join(otp_keys))
    toAdd["OTP"] = {self.username: 1}
    self.data.update(toAdd)
    with open('config.json', 'w') as conf:
      json.dump(self.data, conf, indent=4)
    return "otp setup success."
