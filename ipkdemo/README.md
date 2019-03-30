Enigma2 IPK building demo.

VERSION=0.0.0

How to run this demo:
* Create a directory on your Enigma2 box, whatever path, e.g.: mkdir /tmp/ipkdemo
* Copy all the files to that directory
* Set executable permissions on the relevant files: cd /tmp/ipkdemo ; chmod +x make.sh myar.sh postinst postrm preinst
* Run make.sh: cd /tmp/ipkdemo ; ./make.sh
* You should now be able to install the resulting package: cd /tmp/ipkdemo ; opkg install ipkdemo*ipk
* It installs a file called README.md on /tmp
* Confirm it was successful: cat /tmp/README.txt
* You should now be able to remove the package (opkg remove ipkdemo)
* Confirm the file /tmp/README.md was removed

Adjust to taste, you can also build plugins by changing the name, path, files, etc...

@oottppxx

