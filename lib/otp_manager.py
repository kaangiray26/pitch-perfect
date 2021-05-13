#!/usr/bin/python

import os
import sys
import json
from os.path import normpath as n

class OTPManager:
    def __init__(self):
        self.refresh_data()
        self.available_keys = os.listdir("otp_keys")

    def refresh_data(self):
        with open('config.json',) as self.f:
            self.data = json.load(self.f)

    def find_key(self, email):
        self.refresh_data()
        for k in self.available_keys:
            if email in k:
                offset = self.data["OTP"][email]
                with open(n(os.path.join('otp_keys', k)),) as f:
                    keydata = json.load(f)
                    return keydata[str(offset)], offset

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

    def update_offset(self, email):
        self.refresh_data()
        self.data["OTP"][email] += 1
        with open('config.json', 'w') as conf:
            json.dump(self.data, conf, indent=4)

    def export_key(self):
        self.refresh_data()
        offset = self.data["OTP"][self.credentials("username")]
        for k in self.available_keys:
            if self.credentials("username") in k:
                with open(n(os.path.join('otp_keys', k)),) as f:
                    keydata = json.load(f)
        return (keydata, n(os.path.join("otp_keys", "%s-otp.json" % (self.credentials("username")))), offset)
