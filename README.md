# pitch-perfect :see_no_evil: :hear_no_evil: :speak_no_evil:
One Time Pad Implementation with a GUI

## Features
* Provides a minimal email client
* Encrypts messages with OTP and PGP
* Uses 1024-byte long keys for OTP
* Uses RSA with size 4096 for PGP

## Installation
    $ git clone https://github.com/f34rl00/pitch-perfect.git
    $ cd pitch-perfect-main
    $ pip install -r requirements.txt
    
## Usage
    $ python qt_app.py
  This will start the application and run the setup wizard for the first time.

## Screenshots
<img src="https://github.com/f34rl00/pitch-perfect/blob/master/screenshots/image1.png" width="640">

## Documentation
Nothing much :/

## TO-DO List
- [ ] Remove used otp-key from the sender's key-list  
- [ ] Terminate old messages function sent to the receiver with a signature  
- [ ] Other mailbox fuctions  
- [x] Write email server settings in config file
- [x] Email text length limit for otp encryption
- [ ] Menubar not visible on mac os
- [ ] Google application password needed for login
- [ ] Json for otp keys

### Have you seen the movie?
No, I haven't.
