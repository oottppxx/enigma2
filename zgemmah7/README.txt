Zgemma H7 BOX RECOVERY WITHOUT ERASING ANY BOOT SLOT

Join us in the Enigma2Talk Telegram chatroom (https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

SUMMARY
These are some notes on being able to boot a Zgemma H7 box when there is an
issue with the current slot image (either kernel or root file system), and
without having to flash a recovery image that overwrites all 4 slots, nor
erasing any of the slots, including the broken one (so to give you a chance to
recover it manually).

The below was tested with OpenATV 6.2 as a base image, booting OpenATV 6.2, 6.3,
and 6.4, but there's no real reason it won't work with other (multiboot
supporting) images, and even other similar boxes (e.g., Mutant HD51).

RECOVERY PREREQUISITES AND PREPARATION
- a working DHCP server. Your home LAN router will do fine. One can also
  modify the ifconfig line to statically configure the address, netmask, and
  gateway if DHCP isn't an option;

- a working TFTP server;

- backup all of your /boot/STARTUP* files off-box;

- modify all your /boot/START* files and INSERT the following 1 line preamble,
  ignoring the triple-double-quotes. Make sure to adjust the TFTP server address
  to your needs, as well (192.168.0.50 in the example);
"""
ifconfig eth0 -auto && batch 192.168.0.50:TFTPBOOT
"""

- it's convenient to have at least 2 slots installed beforehand, so you can boot
  from the other when the current one breaks; there are some alternatives if
  this isn't the case, though they are a lot more complicated.

RECOVERY HOWTO
If the current slot is broken in a way that doesn't boot at all, or boots into
a broken system that doesn't allow you to switch the boot to another slot,
either via the multiboot menus or via manual editing of the /boot/STARTUP file
(e.g., broken libs/ld-so loader... don't ask...), then you can do the following,
provided that you've followed the preparation steps above:

- from the backup you did earlier (or ask a friend) copy the STARTUP_n file
  (with "n" corresponding to the alternative slot you want to boot to) to a file
  called TFTPBOOT;

- have the TFTPBOOT file ready to be served from the TFTP server
  (right name, right permissions, etc...);

- reboot the box, making sure it will have network connectivity. If DHCP is
  able to assign it an address (or you adapted the 1 line preamble so the box
  has a static network configuration), then the batch command in the STARTUP
  file should be able to TFTP over the TFTPBOOT file and execute the boot
  command it contains, booting into an altenative slot.

You can just rename the file in the TFTP server to something else when not
needed, then the batch command will fail and the box will boot normally into the
currently selected slot.

Note: it's possible to play around with the commands in the TFTPBOOT file, and
if you prep right you can even enable a console over TCP/IP, but it's also
possible to brick the box messing around, so play safe!

@oottppxx

P.S. - You might also want to try my 8 slots OpenATV 6.4 recovery image, get it
at https://drive.google.com/file/d/1CTYIXOPKuODJa22h9GAWuy-CwkKHrktg/. It should
work pretty similar to the Mut@nt HD51 one, so make sure to go there and read
the README!
