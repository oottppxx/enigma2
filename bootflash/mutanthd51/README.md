![Multi Boot Image](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/hd51x8mi.jpg)

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

BIG THANKS to BazB, this wouldn't have been possible without his generosity!!!

Also, checkout the [party.py](https://github.com/oottppxx/enigma2/blob/master/bootflash/party/party.py)
script if you want to carve your own image partition layout.

To take into consideration:

* This is a developer oriented (multi-)image, with 8 slots sharing the total
  available flash space. Only the slot 1 image is currently supplied, to save
  space/download time - OpenATV 6.4 (unconfigured) - the pictures below are for
  illustration purpouses only.

* AFTER the multi-image is in place, you can flash slots 2 to 8 via the menus,
  as usual. Slot 1 can not be flashed from the menus, as ogfwrite has some
  assumptions builtin, which our partitioning scheme doesn't fulfill.
  To flash slot 1, while booted from a different image, you can try and do
  "ofgwrite --rootfs=mmcblk0p10 -k -m1 /mnt/hdd/images/hd51/"
  if an appropriate kernel and rootfs files are in the "/mnt/hdd/images/hd51"
  directory. Typically the "--rootfs" option wouldn't be required.

* OpenDroid throws a warning regarding the commands in the startup files, just
  ignore and reboot to the other slot anyway. Also, OpenDroid apparently
  allows to reboot into an empty slot, so be careful.

* OpenPLi only detects slots 1 to 4, and doesn't mount the boot partition by
  default, so just reboot to slot 1 (where you're advised to keep OpenATV 6.4
  or better) and from there reboot to any other desired slot.

* OpenSPA also only detets slots 1 to 4, but it mounts the boot partition by
  default, so just reboot to slot 1 (where you're advised to keep OpenATV 6.4
  or better) and from there reboot to any other desired slot; or manually adjust
  the startup files once we want to reboot to another slot.
  E.g., you can do "cp /boot/STARTUP_1 /boot/STARTUP ; sync ; sync ; reboot"
  to reboot to slot 1.

* If you flash other images, namely older ones (e.g., OpenATV 6.2), they might
  not support the configured 8 slots (just like OpenPLi). A similar procedure as
  for OpenSPA or for OpenPLi should be followed.

@oottppxx

[Image Download GDrive](https://drive.google.com/file/d/1Hbao9h3dSWhBHsRh11XYyDY9_4BfiEB_/)

![Multi Boot Image Slot 1](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot1.jpg)
![Multi Boot Image Slot 2](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot2.jpg)
![Multi Boot Image Slot 3](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot3.jpg)
![Multi Boot Image Slot 4](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot4.jpg)
![Multi Boot Image Slot 5](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot5.jpg)
![Multi Boot Image Slot 6](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot6.jpg)
![Multi Boot Image Slot 7](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot7.jpg)

