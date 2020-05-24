![Multi Boot Image](https://github.com/oottppxx/enigma2/blob/master/mutanthd51/hd51x8mi.jpg)

Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

To take into consideration:

* This is a developer oriented (multi-)image, if you don't know how to flash it
  then it's probable that you shouldn't be trying it!
  If you still want to try, flash it just like any recovery image.

* AFTER the multi-image is in place, flashing of each slot should be done from
  the command line, not from the menus, as ogfwrite has some assumptions
  builtin, which our partitioning scheme doesn't fulfill.
  E.g., you can do "ofgwrite --rootfs=mmcblk0p10 -k -m2 /media/hdd/images/hd51/"
  to flash a multiboot image to slot 2, if the kernel and rootfs files are in
  the /media/hdd/images/hd51 directory. Typically the --rootfs option wouldn't
  be required.

* OpenSPA crashes on multiboot selection menu, so one needs to manually adjust
  the startup files once we want to reboot to another slot.
  E.g., you can do "cp /boot/STARTUP_1 /boot/STARTUP ; sync ; sync ; reboot"
  to reboot to slot 1.

* OpenPLi only detects slot 1, and doesn't mount the boot partition by default,
  so just reboot to slot 1 (where you're advised to keep OpenATV 6.3 or better)
  and from there reboot to any other desired slot.

* OpenDroid throws a warning regarding the commands in the startup files, just
  ignore and reboot to the other slot anyway.

* If you flash other images, namely older ones (e.g., OpenATV 6.2), they might
  not support the configured 8 slots (just like OpenPLi). A similar procedure as
  for OpenSPA or for OpenPLi should be followed.

* OpenSPA was left in Spanish instead of English, sorry.

* OpenDroid was left in the Rome timezone, not Dublin, sorry.

@oottppxx


[Image Download GDrive](https://drive.google.com/file/d/1-j1j9eB8mA6mQuFQL5mC6y0MlclNZfa7/)
