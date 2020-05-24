Enigma2 IPK building demo.

How to run this demo:
* Create a directory on your Enigma2 box, whatever path, e.g.: mkdir /tmp/ipkdemo
* Copy all the files to that directory
* From that directory, run make.sh, e.g.: cd /tmp/ipkdemo ; ./make.sh
* You should now be able to install the resulting package, e.g.: cd /tmp/ipkdemo ; opkg install ipkdemo*ipk
* It installs a file called README.md on /tmp
* Confirm it was successful: cat /tmp/README.md
* You should now be able to remove the package (opkg remove ipkdemo)
* Confirm the file /tmp/README.md was removed

Adjust to taste, you can also build plugins by changing the name, path, files, etc...

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

@oottppxx

