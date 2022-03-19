![Multi Boot Image](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/hd51x8mi.jpg)

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

BIG THANKS to BazB, this wouldn't have been possible without his generosity!!!

Checkout the [party.py](https://github.com/oottppxx/enigma2/blob/master/bootflash/party/party.py)
script if you want to carve your own image partition layout.

To take into consideration:

* This was a developer oriented (multi-)image, with 8 slots sharing the total
  available flash space.  The pictures below are for illustration purpouses
  only.

* OpenDroid would throw a warning regarding the commands in the startup files,
  just ignore and reboot to the other slot anyway. Also, OpenDroid apparently
  allows to reboot into an empty slot, so be careful.

* OpenPLi only detects slots 1 to 4, and doesn't mount the boot partition by
  default, so just reboot to slot 1 (where you're advised to keep OpenATV 6.4
  or better) and from there reboot to any other desired slot.

* OpenSPA also only detects slots 1 to 4, but it mounts the boot partition by
  default, so just reboot to slot 1 (where you're advised to keep OpenATV 6.4
  or better) and from there reboot to any other desired slot; or manually adjust
  the startup files once we want to reboot to another slot.
  E.g., you can do "cp /boot/STARTUP_1 /boot/STARTUP ; sync ; sync ; reboot"
  to reboot to slot 1.

* If you flash other images, namely older ones (e.g., OpenATV 6.2), they might
  not support the configured 8 slots (just like OpenPLi). A similar procedure as
  for OpenSPA or for OpenPLi should be followed.

@oottppxx

![Multi Boot Image Slot 1](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot1.jpg)
![Multi Boot Image Slot 2](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot2.jpg)
![Multi Boot Image Slot 3](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot3.jpg)
![Multi Boot Image Slot 4](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot4.jpg)
![Multi Boot Image Slot 5](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot5.jpg)
![Multi Boot Image Slot 6](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot6.jpg)
![Multi Boot Image Slot 7](https://github.com/oottppxx/enigma2/blob/master/bootflash/mutanthd51/slot7.jpg)

