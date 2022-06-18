@echo off
set oscIP=0.0.0.0
set oscPort=9001

cd /D "%localappdata%/IntifaceDesktop/engine"
start IntifaceCLI --servername "Intiface Server" --stayopen --wsinsecureport 12345 --with-lovense-connect
cd /D %~dp0
start buttplug-osc --osc-listen udp://%oscIP%:%oscPort%
