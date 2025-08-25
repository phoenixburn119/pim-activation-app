# PIM Activation App
 Uses Graph and an Azure app registration to interface with Entra roles in a fast and snappy way. The traditional Entra PIM site takes so much time to checkout one role and refreshes after each one you do, it can take minutes to do a handful of roles. This tkinter/Graph app allows you to activate multiple roles at once using threaded. The main activation function attempts to checkout for 8 hours then tries 4 if it returns a policy failed "ExpirationRule" response. I've attempted to write in as many possible issues that would occur but it may still have issues. In a normal day to day basis it functions great. Please install all packages from the requirements.txt and run the project. I've also included icon and pyinstaller commands.
 

Used for testing, opens console
pyinstaller --console --icon=64x64-Emoji-Finished.ico -F --add-data="Sources/*.py;." .\main.py
pyinstaller --console --icon=PIMManagement.ico -F --add-data="Sources/*.py;." .\main.py

Main command to package app
pyinstaller --noconsole --icon=64x64-Emoji-Finished.ico -F --add-data="Sources/*.py;." .\main.py --windowed
