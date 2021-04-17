#!/usr/bin/python
#-*- encoding:utf-8 -*-

import os
import sys
import pgpy
import json
from os.path import normpath as n

class PGPManager:
    def __init__(self):
        self.refresh_data()
        self.available_keys = os.listdir("pgp_keys")

    def refresh_data(self):
        with open('config.json',) as self.f:
            self.data = json.load(self.f)

    def find_secret(self, sender):
        for k in self.available_keys:
            if sender in k and "secret" in k:
                key, _ = pgpy.PGPKey.from_file(n(os.path.join('pgp_keys',k)))
                return key

    def find_public(self, receiver):
        for k in self.available_keys:
            if receiver == k.split()[-1][:-11] and "public" in k:
                print(k)
                key, _ = pgpy.PGPKey.from_file(n(os.path.join('pgp_keys',k)))
                return key

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

    def export_key(self):
        privkey = self.find_secret(self.credentials("username"))
        with privkey.unlock(self.credentials("passphrase")):
            pubkey = privkey.pubkey
        filename = " ".join(privkey.userids[0].userid.split()[
                            :-1] + [privkey.userids[0].userid.split()[-1][1:-1]])
        return (str(pubkey), n(os.path.join("pgp_keys","%s-public.asc" % (filename))))