Zgemma H7 BOX RECOVERY WITHOUT ERASING ALL

RECOVERY PREREQUISITES
1.
- the below uses slot 4 for the recovery, so make sure it boots/works fine;
- make a copy of the linuxkernel4 partition into a file, e.g.:
  dd if=/dev/mmcblk0p6 of=linuxkernel4 bs=1M
  (this is valid for oatv6.2)

2.
- modify all your /boot/START* files and add the following preamble:
  (ignore the triple-double-quotes and adjust the tftpserver address to your needs):
"""
ifconfig -auto eth0 && ping -c=1 192.168.0.50
boot -max=8388608 192.168.0.50:linuxkernel4 'brcm_cma=440M@328M brcm_cma=192M@768M root=/dev/mmcblk0p7 rootsubdir=linuxrootfs4 kernel=/dev/mmcblk0p6 rw rootwait h7_4.boxmode=1' || ping -c=2 192.168.0.50
ping -c=4 192.168.0.50
"""

RECOVERY HOWTO:
If a slot (other than 4) is broken, doesn't boot, or boots into a bad system
(e.g., broken libs/ld-so loader... don't ask...) then you can do the following:
- have the linuxkernel4 file ready to be served from the tftpd root (right name,
  right permissions, etc...);
- reboot the box: the 1st boot command in the STARTUP file will be able to
  netboot into slot 4 (hence why it's important that it's kept pristine).

You can just rename the file in the tftpd root to something else when not needed,
the 1st boot command will fail and the slot corresponding to the in use STARTUP_X
file (which is copied over the /boot/STARTUP file itself) will be used and booted
from/into.

NOTES:
Why not use 4 TFTP boot commands, 1 for each slot, and be done with it?
Unfortunately it seems something in the original bootloader times out after 3
boot commands are made, so we wouldn't get down to the boot command for the slot,
the boot would hang. I believe it's perfectly feasible to have 2 TFTP boot commands,
though, and might look into it.

OHTER IDEAS:
The use of the copydisk and flash commands were also attempted, to no avail.
Using this method, a single file served from tftp would overwrite the emmcflash0.boot
partition (or a few sectors within, even, to just overwrite the required STARTUP*
files), providing more flexibility about recovery slots, as long as they wouldn't
all be broken. This idea, however, was unsuccessful. Maybe if/when I get a bootloader
serial console up this can be debugged.
Booting a 2nd stage bootloader, like u-boot, that could eventually provide network
access, would also be nice and relatively generic, but didn't really work on this as
it seemed to be a lot more work and maybe a bit over my head on this system. Food
for thought.

