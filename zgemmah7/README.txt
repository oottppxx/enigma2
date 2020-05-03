Zgemma H7 BOX RECOVERY WITHOUT ERASING ALL

These are some short notes on being able to boot a Zgemma H7 box when
there is an issue with the current slot image, and without having to
flash a recovery image that overwrites all 4 slots.

RECOVERY PREREQUISITES/PREPARATION
- a working DHCP server. Your home LAN router will do fine. One can also
  modify the ifconfig line to statically configure the address, netmask,
  and gateway;
- a working TFTP server;
- the below uses slot 4 for the recovery, so make sure it boots/works fine
  (or adapt everything to use another slot, or a couple);
- make a copy of the linuxkernel4 partition into a file, e.g.:
  dd if=/dev/mmcblk0p6 of=linuxkernel4 bs=1M
  (this is valid for the latest OpenATV 6.2 partition scheme).
- modify all your /boot/START* files and add the following 3 line preamble,
  ignoring the triple-double-quotes. Make sure to adjust the TFTP server
  address to your needs, as well. If you want, you can also omit the
  various ping commands, I've put them in to help with debugging.

"""
ifconfig -auto eth0 && ping -c=1 192.168.0.50
boot -max=8388608 192.168.0.50:linuxkernel4 'brcm_cma=440M@328M brcm_cma=192M@768M root=/dev/mmcblk0p7 rootsubdir=linuxrootfs4 kernel=/dev/mmcblk0p6 rw rootwait h7_4.boxmode=1' || ping -c=2 192.168.0.50
ping -c=4 192.168.0.50
"""

RECOVERY HOWTO
If a slot (other than 4) is broken in a way that doesn't boot at all, or
boots into a broken system that doesn't allow you to switch to another boot
slot, either via the multiboot menus or via manually editing the
/boot/STARTUP file (e.g., broken libs/ld-so loader... don't ask...), then you
can do the following, provided that you've followed the preparation steps above:
- have the linuxkernel4 file ready to be served from the TFTP server
  (right name, right permissions, etc...);
- reboot the box, making sure it will have network connectivity. If DHCP is
  able to assign it an address (or you adapted the preparation steps so the box
  has a static network configuration), then the 1st boot command in the STARTUP
  file should be able to netboot into slot 4 (hence why it's important that it's
  kept pristine).

You can just rename the file in the TFTP server to something else when not
needed, the 1st boot command will fail and the slot corresponding to the in use
STARTUP_X file (which is copied over the /boot/STARTUP file itself) will be used
and booted from/into.

NOTES & OTHER IDEAS
Why not use 4 TFTP boot commands, 1 for each slot, and be done with it?
Unfortunately it seems something in the original bootloader times out after 3
boot commands are made, so we wouldn't get down to the boot command for the
slot, the boot would hang. I believe it's perfectly feasible to have 2 TFTP boot
commands, though, and might look into it. It's also possible the use of the ping
commands is interfering with a timer/watchdog or similar, eventually I might
also try to eliminate them to test.

The use of the bootloader copydisk and flash commands were also attempted, to no
avail. Using this method, a single file served from tftp would overwrite the
emmcflash0.boot partition (or a few sectors within, even, to just overwrite the
required STARTUP* files), providing more flexibility about recovery slots, as
long as they wouldn't all be broken. This idea, however, was unsuccessful. Maybe
if/when I get a bootloader serial console up this can be debugged.

Booting a 2nd stage bootloader, like u-boot, that could eventually provide
network access to the bootloader itself, if something gets stuck, would also be
nice and relatively generic, but I didn't really work on this as it seemed to be
a lot more work and maybe a bit over my head.

Better yet, have a kernel boot with a nice initramfs that only needs to allow
some form of network access and mounting the boot partition to edit the
STARTUP* files.
