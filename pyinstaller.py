
added_files = ["Sources/*.py;utils","Sources/pimicon.png;."] 

pyinstaller --noconsole --icon=64x64-Emoji-Finished.ico -F --add-data=added_files .\main.py --windowed