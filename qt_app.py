#!/usr/bin/python
#-*- encoding:utf-8 -*-
import os
import sys
import json
import platform
import shutil
import time
import requests
from threading import Thread
from os.path import normpath as n
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox,
    QTreeWidgetItem, QWidget, QDialogButtonBox,
    QWizard, QWizardPage, QLabel, QVBoxLayout,
    QLineEdit, QHBoxLayout, QFileDialog,
    QDesktopWidget, QShortcut, QMenu, QRadioButton
)
from PyQt5.QtCore import QFileInfo, Qt, QUrl, QSize
from PyQt5.Qt import QDesktopServices, QKeySequence
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.uic import loadUi
from lib.modern_window import Ui_MainWindow as MainWindow
from lib.message_modern import Ui_MainWindow as MessageWindow
from lib.addressbook_modern import Ui_MainWindow as AddressBookWindow
from lib.wizardError_dialog import Ui_Dialog as wizardErrorDialog
from lib.get_mail import inbox, WizardError
from lib.send_mail import outbox, AuthenticationError
from lib.wizard import setup
from lib.decrypt_message import decryption, DecryptionError
from lib.addressBook import contactBook, unsupportedTypeError
from lib.pgp_manager import PGPManager
from lib.otp_manager import OTPManager

def hardReset():
    pgp_keys = os.listdir("pgp_keys")
    otp_keys = os.listdir("otp_keys")
    downloaded = os.listdir("downloaded")
    if "__pycache__" in os.listdir("."):
        shutil.rmtree("__pycache__", ignore_errors=True)
    if "config.json" in os.listdir("."):
        os.remove("config.json")
    if "contacts.json" in os.listdir("."):
        os.remove("contacts.json")
    if "local.json" in os.listdir("archive"):
        os.remove(os.path.join("archive","local.json"))
    for k in pgp_keys:
        os.remove(n(os.path.join("pgp_keys", k)))
    for k in otp_keys:
        os.remove(n(os.path.join("otp_keys", k)))
    for k in downloaded:
        os.remove(n(os.path.join("downloaded", k)))

class AboutScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.icon = QLabel("<pre style='font-size: 64pt'>"+"\U0001f4ec"+"</pre>")
        self.icon.setAlignment(Qt.AlignCenter)
        self.title = QLabel("-Pitch Perfect-\nA One Time Pad implementation")
        self.title.setAlignment(Qt.AlignCenter)
        self.info = QLabel("Built with löve.")
        self.info.setAlignment(Qt.AlignCenter)
        self.link = QLabel(
            "<a href='https://github.com/f34rl00/pitch-perfect'> Github Page <\a>")
        self.link.setOpenExternalLinks(True)
        self.link.setAlignment(Qt.AlignCenter)
        row_1 = QVBoxLayout()
        row_1.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        row_1.addWidget(self.icon)
        row_1.addWidget(self.title)
        row_1.addWidget(self.info)
        row_1.addWidget(self.link)
        self.setLayout(row_1)
        self.setFixedSize(240, 200)

class FileDialog(QFileDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

class ResetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reset")

        self.info = QLabel("This will remove all settings including config files, downloaded files, contacts, pgp keys and otp keys.\nAre you sure about this?")
        self.info.setAlignment(Qt.AlignCenter)
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        row = QVBoxLayout()
        row.addWidget(self.info)
        row.addWidget(self.buttonBox)
        self.setLayout(row)
        self._connectActions()

    def _connectActions(self):
        self.buttonBox.accepted.connect(self.resetAction)
        self.buttonBox.rejected.connect(self.reject)

    def resetAction(self):
        hardReset()
        QMessageBox.about(self, "Result", "All settings removed.")
        exit()

class contactTypeDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Export type")
        self.info = QLabel("Please select export type:")
        self.csv = QRadioButton("csv")
        self.json = QRadioButton("json")
        self.buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        row = QVBoxLayout()
        row.addWidget(self.info)
        row.addWidget(self.csv)
        row.addWidget(self.json)
        row.addWidget(self.buttonBox)
        self.setLayout(row)
        self._connectActions()

    def _connectActions(self):
        self.buttonBox.accepted.connect(self.getBack)
        self.buttonBox.rejected.connect(self.reject)

    def getBack(self):
        if self.csv.isChecked():
            self.parent.exportFileType = "csv"
        else:
            self.parent.exportFileType = "json"
        self.accept()

class contactDialog(QDialog):
    def __init__(self, default, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contact info")
        self.name = QLineEdit()
        self.email = QLineEdit()
        if default:
            self.name.setText(default[0])
            self.email.setText(default[1])

        row_1 = QHBoxLayout()
        row_1.addWidget(QLabel("Name:"))
        row_1.addWidget(self.name)

        row_2 = QHBoxLayout()
        row_2.addWidget(QLabel("Email:"))
        row_2.addWidget(self.email)

        row_3 = QHBoxLayout()
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        row_3.addWidget(self.buttonBox)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.buttonBox)

        layout = QVBoxLayout()
        layout.addLayout(row_1)
        layout.addLayout(row_2)
        layout.addLayout(row_3)
        self.setLayout(layout)
        self._connectActions()
    
    def _connectActions(self):
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

class SetupWizard(QWizard):
    def __init__(self, parent=None):
        super(SetupWizard, self).__init__(parent)
        self.addPage(Page1(self))
        self.addPage(Page2(self))
        self.addPage(Page3(self))
        self.addPage(Page4(self))
        self.addPage(Page5(self))
        self.addPage(Page6(self))
        self.setWindowTitle("Pitch Perfect Wizard")
        self.resize(640, 480)
        self.setup = setup()
        self._connectActions()

    def _connectActions(self):
        self.button(QWizard.NextButton).clicked.connect(self.nextClicked)

    def nextClicked(self):
        title = self.currentPage().title()
        if title == "PGP Setup":
            name = self.page(1).input_name.text()
            email = self.page(1).input_email.text()
            password = self.page(1).input_pass.text()
            print(self.setup.email_setup(name, email, password))
        elif title == "OTP Setup":
            passphrase = self.page(2).input_passphrase.text()
            print(self.setup.pgp_setup(passphrase))
        elif title == "Wizard End":
            print(self.setup.otp_setup())
        elif title == "Dummy Page":
            os.execv(sys.executable, ['python'] + sys.argv)

class Page1(QWizardPage):
    def __init__(self, parent=None):
        super(Page1, self).__init__(parent)
        self.setTitle("Setup Wizard")
        self.label1 = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.label1)
        self.setLayout(layout)
        self.label1.setText(
            "This wizard will help you set up your email address and create pgp and otp keys.\nCaution: If you enter a used email address, the keys will be overwritten.\nDo you want to continue?")

class Page2(QWizardPage):
    def __init__(self, parent=None):
        super(Page2, self).__init__(parent)
        self.setTitle("Email Setup")
        self.label_name  = QLabel()
        self.input_name  = QLineEdit()
        self.label_email = QLabel()
        self.input_email = QLineEdit()
        self.label_pass  = QLabel()
        self.input_pass  = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.Password)
        layout = QVBoxLayout()
        layout.addWidget(self.label_name)
        layout.addWidget(self.input_name)
        layout.addWidget(self.label_email)
        layout.addWidget(self.input_email)
        layout.addWidget(self.label_pass)
        layout.addWidget(self.input_pass)
        self.setLayout(layout)
        self.label_name.setText('Please enter your name:')
        self.label_email.setText('Please type your email address:')
        self.label_pass.setText('Please type your password:')

class Page3(QWizardPage):
    def __init__(self, parent=None):
        super(Page3, self).__init__(parent)
        self.setTitle("PGP Setup")
        self.label_passphrase = QLabel()
        self.input_passphrase = QLineEdit()
        self.input_passphrase.setEchoMode(QLineEdit.Password)
        layout = QVBoxLayout()
        layout.addWidget(self.label_passphrase)
        layout.addWidget(self.input_passphrase)
        self.setLayout(layout)
        self.label_passphrase.setText('Please enter a passphrase:')

class Page4(QWizardPage):
    def __init__(self, parent=None):
        super(Page4, self).__init__(parent)
        self.setTitle("OTP Setup")
        self.label_continue = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.label_continue)
        self.setLayout(layout)
        self.label_continue.setText('Please just continue to create keys.')
    
class Page5(QWizardPage):
    def __init__(self, parent=None):
        super(Page5, self).__init__(parent)
        self.setTitle("Wizard End")
        self.label_continue = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.label_continue)
        self.setLayout(layout)
        self.label_continue.setText('Setup is done.\nThank you for using Pitch Perfect!'),

class Page6(QWizardPage):
    def __init__(self, parent=None):
        super(Page6, self).__init__(parent)
        self.setTitle("Dummy Page")
        layout = QVBoxLayout()
        self.setLayout(layout)

class Dialog1(QDialog, wizardErrorDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.retranslateUi(self)
        self._connectActions()
        self.activateWindow()

    def _connectActions(self):
        self.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.doTrue)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.doFalse)

    def doTrue(self):
        self.wizard = SetupWizard()
        self.wizard.show()
        self.close()
        
    def doFalse(self):
        exit()

class Window3(QMainWindow, AddressBookWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setupUi(self)
        self.retranslateUi(self)
        self._connectActions()
        self.contactBook = contactBook()
        self.refreshBook()
        self.exportFileType = None
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle = self.frameGeometry()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def _connectActions(self):
        self.actionAdd_Contact.triggered.connect(self.addContact)
        self.actionImport_Contacts.triggered.connect(self.importContacts)
        self.actionExport_Contacts.triggered.connect(self.exportContacts)
        self.treeWidget.itemActivated.connect(lambda: self.doWrite(self.treeWidget.selectedIndexes()))
        self.treeWidget.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, position):
        item = self.treeWidget.itemFromIndex(self.treeWidget.selectedIndexes()[0])
        self.selected = (item.text(0), item.text(1))
        menu = QMenu()
        menu.addAction("Edit person", self.editContact)
        menu.exec_(self.treeWidget.viewport().mapToGlobal(position))

    def editContact(self):
        self.d = contactDialog(self.selected)
        self.d.exec_()
        if len(self.d.email.text()) > 1:
            self.contactBook.add_contact(
                self.d.name.text(), self.d.email.text())
            self.refreshBook()
            self.parent.getContacts()

    def doWrite(self, to_addr):
        if to_addr:
            to_addr = self.treeWidget.itemFromIndex(to_addr[0]).text(1)
        self.newWin = Window2(to_addr)
        self.newWin.show()

    def addContact(self):
        self.d = contactDialog(None)
        self.d.exec_()
        if len(self.d.email.text()) > 1:
            self.contactBook.add_contact(self.d.name.text(), self.d.email.text())
            self.refreshBook()
            self.parent.getContacts()

    def importContacts(self):
        self.statusbar.showMessage("Importing...", 3000)
        self.d = FileDialog()
        locations = self.d.getOpenFileNames(self.d, 'Open File')[0]
        files = {}
        for f in locations:
            files[f] = QFileInfo(f).fileName()
        try:
            self.contactBook.import_contacts(files)
            self.refreshBook()
            self.parent.getContacts()
        except unsupportedTypeError as e:
            QMessageBox.about(self, "Error", str(e))
            return

    def exportContacts(self):
        self.statusbar.showMessage("Exporting contacts...")
        self.t = contactTypeDialog(self)
        self.t.exec_()
        if self.exportFileType == None:
            self.statusbar.showMessage("Contacts not exported.", 3000)
            return
        key, filename = self.contactBook.export_contacts(self.exportFileType)
        self.d = FileDialog()
        location = self.d.getSaveFileName(self.d, 'Save File', filename)
        try:
            with open(location[0], "w") as f:
                f.write(key)
                f.close()
            self.statusbar.showMessage("Contacts exported successfully.", 3000)
        except FileNotFoundError:
            self.statusbar.showMessage("Contacts not exported.", 3000)
    
    def refreshBook(self):
        l = []
        contacts = self.contactBook.getContacts()
        for key in contacts.keys():
            l.append(QTreeWidgetItem((contacts[key], key)))
        self.treeWidget.clear()
        self.treeWidget.addTopLevelItems(l)
        self.treeWidget.resizeColumnToContents(0)
        self.treeWidget.resizeColumnToContents(1)



class Window2(QMainWindow, MessageWindow):
    def __init__(self, to_addr, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.retranslateUi(self)
        self._connectActions()
        self.encryption = False
        self.encrypt_checkBox.setEnabled(False)
        self.sendable = True
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle = self.frameGeometry()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self.outbox = outbox()
        self.from_addresslabel.setText(self.outbox.from_adress)
        if to_addr != False:
            self.to_lineEdit.setText(to_addr)

    def _connectActions(self):
        self.actionSend.triggered.connect(self.sendMail)
        self.actionClose.triggered.connect(self.doClose)
        self.actionSecurity.triggered.connect(self.checkSecurity)
        self.encrypt_checkBox.clicked.connect(self.encryptSet)
        self.plainTextEdit.textChanged.connect(self.upLength)

    def upLength(self):
        charLen = len(self.plainTextEdit.toPlainText())
        if charLen >= 400:
            self.characterLength.setStyleSheet('color: red')
        elif charLen < 400:
            self.characterLength.setStyleSheet('color: black')
        if charLen >= 1024:
            self.sendable = False
        elif charLen < 1024:
            self.sendable = True
        self.characterLength.setText(str(charLen))

    def sendMail(self):
        if self.encryption:
            if not self.sendable:
                QMessageBox.about(
                    self, "Error", "Your message is too long, keep it shorter than 512 characters.")
                return
        try:
          self.outbox.send(
              self.subject_lineEdit.text(),
              self.to_lineEdit.text(),
              self.plainTextEdit.toPlainText(),
              self.encryption
          )
        except AuthenticationError:
            QMessageBox.about(self, "Error", "Provided credentials are incorrect.")
        self.close()

    def encryptSet(self):
        self.encryption = self.encrypt_checkBox.isChecked()

    def checkSecurity(self):
        if len(self.to_lineEdit.text()) > 1:
            to_address = self.to_lineEdit.text()
            from_address = self.from_addresslabel.text()
            self.pgpManager = PGPManager()
            self.otpManager = OTPManager()
            pubkey = self.pgpManager.find_public(to_address)
            otpkey = self.otpManager.find_key(from_address)
            warning = ""
            if pubkey != None:
                pgpMessage = "You have pgp keys for:\n%s\nYou can encrypt this message." % (
                    to_address)
                self.encrypt_checkBox.setEnabled(True)
                self.encrypt_checkBox.setChecked(True)
                self.encryption = True
            else:
                pgpMessage = "You don't have pgp keys for:\n%s\nSorry, you can't encrypt this message!" % (
                    to_address)
                self.encrypt_checkBox.setEnabled(False)
            if otpkey != None:
                otpMessage = "OTP Keys available."
            else:
                otpMessage = "OTP Keys not available.\nPlease check your configuration."
            warning = pgpMessage + "\n" + otpMessage
            QMessageBox.about(self, "Security", warning)

    def doClose(self):
        self.close()

class Window1(QMainWindow, MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.retranslateUi(self)

        self.itemBlockSize = 25
        self.menubar.setNativeMenuBar(False)

        self.inboxSc = QShortcut(QKeySequence('Alt+1'), self)
        self.mailSc = QShortcut(QKeySequence('Alt+2'), self)
        self.closeSC1 = QShortcut(QKeySequence('Ctrl+W'), self)
        self.closeSC2 = QShortcut(QKeySequence('Ctrl+Q'), self)
        self.writeSc = QShortcut(QKeySequence('Ctrl+N'), self)

        self._connectActions()
        self.tabWidget.setCurrentIndex(0)
        self.treeWidget.setFocus()
        self.treeWidget.setStyleSheet("QTreeView::item { height: 22px }")
        self.treeWidget.setColumnWidth(0, 250)
        self.text = ""
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle = self.frameGeometry()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        try:
            self.inbox = inbox()
            self.thread = Thread(target=self.inbox.refresh_mail)
            self.getMessages()
            self.getContacts()
            self.decryption = decryption()
        except WizardError as e:
            self.d = Dialog1(self)
            self.d.textBrowser.setText(str(e))
            self.d.show()

    def _connectActions(self):
        self.actionGet_Messages.triggered.connect(self.getMessages)
        self.actionExit.triggered.connect(self.doExit)
        self.actionWrite.triggered.connect(self.doWrite)
        self.treeWidget.itemActivated.connect(lambda: self.openMail(self.treeWidget.selectedItems()))
        self.treeWidget_2.itemActivated.connect(lambda: self.doWrite(self.treeWidget_2.selectedIndexes()))
        self.decryptButton.clicked.connect(self.decryptMail)
        self.attachmentButton.clicked.connect(self.openAttachment)
        self.actionAddress_Book.triggered.connect(self.openAddressBook)
        self.actionExport_pgpKeys.triggered.connect(self.exportPGPKeys)
        self.actionImport_pgpKeys.triggered.connect(self.importPGPKeys)
        self.actionExport_otpKeys.triggered.connect(self.exportOTPKeys)
        self.actionImport_otpKeys.triggered.connect(self.importOTPKeys)
        self.actionAbout.triggered.connect(self.showAbout)
        self.actionWizard.triggered.connect(self.startWizard)
        self.actionDocumentation.triggered.connect(self.openDocs)
        self.inboxSc.activated.connect(self.switchToInbox)
        self.mailSc.activated.connect(self.switchToMail)
        self.closeSC1.activated.connect(self.doExit)
        self.closeSC2.activated.connect(self.doExit)
        self.writeSc.activated.connect(lambda: self.doWrite(None))
        self.actionReset.triggered.connect(self.doReset)
        self.rightButton.clicked.connect(self.goNext)
        self.leftButton.clicked.connect(self.goBack)
        self.actionUpdate.triggered.connect(self.updateSelf)

    def updateSelf(self):
        with open(n(os.path.join("lib","VERSION"))) as v:
            version = v.read()
        check_version = requests.get(
            "https://raw.githubusercontent.com/f34rl00/pitch-perfect/master/lib/VERSION").text
        print(float(version), float(check_version))
        if (check_version > version):
            QMessageBox.about(self, "Security", "Performing update...\nThe program will close itself.")
            os.execv(sys.executable, ['python', "updater.py", "1.1"])
            self.close()

        else:
            QMessageBox.about(self, "Security", "You are already up-to-date!")
        return


    def goBack(self):
        now = self.pageIndex.text()
        if now == "1":
            return
        else:
            self.pageIndex.setText(str(int(now)-1))
        self.showMessages()

    def goNext(self):
        now = self.pageIndex.text()
        self.pageIndex.setText(str(int(now)+1))
        self.showMessages()

    def openAttachment(self):
        if len(self.mail_fromlabel.text()) < 1:
            return
        path = n(os.path.join("downloaded",self.attachment_name))
        if isinstance(self.attachment, bytes):
            writeType = "wb"
        else:
            writeType = "w"
        with open(path, writeType) as f:
            f.write(self.attachment)
            f.close()
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            os.popen("open "+path)
        else:
            os.popen("xdg-open "+path)

    def doReset(self):
        self.resetdialog = ResetDialog()
        self.resetdialog.exec_()

    def switchToInbox(self):
        self.tabWidget.setCurrentIndex(0)

    def switchToMail(self):
        self.tabWidget.setCurrentIndex(1)

    def openDocs(self):
        url = QUrl(
            "https://github.com/f34rl00/pitch-perfect#documentation")
        QDesktopServices.openUrl(url)

    def startWizard(self):
        self.wizard = SetupWizard()
        self.wizard.show()
        
    def showAbout(self):
        self.d = AboutScreen()
        self.d.show()

    def doWrite(self, to_addr):
        if to_addr:
            to_addr = self.treeWidget_2.itemFromIndex(to_addr[0]).text(0)
        self.newWin = Window2(to_addr)
        self.newWin.show()

    def showMessages(self):
        self.treeWidget.clear()
        l = []
        ind = int(self.pageIndex.text())
        if (ind-1) >= len(self.inbox.local_emails)/25:
            self.goBack()
            return
        emails = self.inbox.local_emails[(ind-1)*25 : ind*25]
        for item in emails:
            time.sleep(0.001)
            l.append(QTreeWidgetItem(item[0]))  # -> segmentation fault
            pass
        self.treeWidget.addTopLevelItems(l)
        self.statusbar.clearMessage()
        return

    def getMessages(self):
        self.statusbar.showMessage("Refreshing inbox...")
        self.inbox.doExit = True
        while self.thread.is_alive():
            pass
        self.inbox.doExit = False
        self.thread = Thread(target=self.inbox.refresh_mail, daemon=True)
        self.thread.start()
        while (self.inbox.loaded) != True:
            pass
        print("inbox is loaded!\n")
        Thread(target=self.showMessages, daemon=True).start()

    def getContacts(self):
        self.contactBook = contactBook()
        l = []
        contacts = self.contactBook.getContacts()
        for key in contacts.keys():
            l.append(QTreeWidgetItem((key,)))
        self.treeWidget_2.clear()
        self.treeWidget_2.addTopLevelItems(l)
        self.treeWidget_2.resizeColumnToContents(0)

    def openMail(self, item):
        self.statusbar.showMessage("Opening message...")
        index = self.treeWidget.indexOfTopLevelItem(item[0])
        pi = int(self.pageIndex.text())-1
        ei = pi*25+index
        text_type = self.inbox.local_emails[ei][1]
        self.text = self.inbox.local_emails[ei][2]
        self.attachment_name = self.inbox.local_emails[ei][5]
        self.attachment = self.inbox.local_emails[ei][6]
        
        xheader   = self.inbox.local_emails[ei][3]
        self.xmagicnumber = self.inbox.local_emails[ei][4]
        self.mail_subjectlabel.setText(self.inbox.local_emails[ei][0][0])
        self.mail_fromlabel.setText(self.inbox.local_emails[ei][0][1])
        self.mail_date.setText(self.inbox.local_emails[ei][0][2])

        if self.attachment_name == None:
            self.attachmentButton.hide()
        else:
            self.attachmentButton.show()

        if isinstance(self.text, bytes):
            self.text = self.text.decode("iso-8859-1")

        if xheader == "pitch-perfect":
            self.decryptButton.show()
            self.statusbar.showMessage("This message has pitch-perfect encrypted data.")
        else:
            self.decryptButton.hide()

        if text_type == "text/html":
            self.webEngineView.setHtml(self.text)
        else:
            self.webEngineView.setHtml("<pre>"+self.text+"</pre> <br>")
            
        self.tabWidget.setCurrentIndex(1)
        self.statusbar.clearMessage()

    def decryptMail(self):
        if len(self.mail_fromlabel.text()) < 1:
            return
        self.statusbar.showMessage("Decrypting...")
        try:
            decrypted_text = self.decryption.decryptMessage(
                self.text, self.mail_fromlabel.text(), self.xmagicnumber)
            self.decryptButton.hide()
            self.webEngineView.setHtml("<pre>"+decrypted_text+"</pre> <br>")
        except DecryptionError as e:
            QMessageBox.about(self, "Error", str(e))
        except ValueError:
            pass
        self.statusbar.clearMessage()

    def openAddressBook(self):
        self.newWin = Window3(self)
        self.newWin.show()

    def importPGPKeys(self):
        self.statusbar.showMessage("Importing keys...")
        self.d = FileDialog()
        location = self.d.getOpenFileName(self.d, 'Open File')
        filename = QFileInfo(location[0]).fileName()
        try:
            with open(location[0], "r") as origin:
                key = origin.read()
                with open(n(os.path.join("pgp_keys","%s" %(filename))), "w") as f:
                    f.write(key)
                    f.close()
            self.statusbar.showMessage("Key imported successfully.", 3000)
        except FileNotFoundError:
            self.statusbar.showMessage("Key not exported.", 3000)

    def exportPGPKeys(self):
        self.statusbar.showMessage("Exporting keys...")
        self.pgpManager = PGPManager()
        pubkey, filename = self.pgpManager.export_key()
        self.d = FileDialog()
        location = self.d.getSaveFileName(self.d, 'Save File', filename)
        try:
            with open(location[0], "w") as f:
                f.write(pubkey)
                f.close()
            self.statusbar.showMessage("Key exported successfully.", 3000)
        except FileNotFoundError:
            self.statusbar.showMessage("Key not exported.", 3000)

    def importOTPKeys(self):
        self.statusbar.showMessage("Importing keys...")
        self.d = FileDialog()
        location = self.d.getOpenFileName(self.d, 'Open File')
        filename = QFileInfo(location[0]).fileName()
        try:
            with open(location[0], "r") as origin:
                key = origin.read()
                with open(n(os.path.join("otp_keys","%s" % (filename))), "w") as f:
                    f.write(key)
            self.statusbar.showMessage("Key imported successfully.", 3000)
        except FileNotFoundError:
            self.statusbar.showMessage("Key not imported.", 3000)

    def exportOTPKeys(self):
        self.statusbar.showMessage("Exporting keys...")
        self.otpManager = OTPManager()
        pubkey, filename , offset = self.otpManager.export_key()
        self.d = FileDialog()
        location = self.d.getSaveFileName(self.d, 'Save File', filename)
        try:
            with open(location[0], "w") as f:
                json.dump(pubkey, f, indent=4)
            self.statusbar.showMessage("Key exported successfully.", 3000)
            QMessageBox.about(self, 'Important', "Do not forget to save your offset: \n % s" % (offset))
        except FileNotFoundError:
            self.statusbar.showMessage("Key not exported.", 3000)

    def doExit(self):
        #do save action
        exit()

if __name__ == "__main__":
    arg = sys.argv[1:]
    if "--reset" in arg:
        hardReset()
        print("All settings removed.")
        exit()
    app = QApplication(sys.argv)
    win = Window1()
    win.show()
    sys.exit(app.exec())

