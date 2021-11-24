Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!


## Summary

The party.py script allows one to create disk images, with a specified partition
layout, for boxes like Zgemma H7, Mut@nt/Opticum/AX HD51, Vimastec VS1500,
and maybe others.

It's currently hard coded for OpenATV 6.4 recovery_emmc images, and it probably
requires code tweaks if their layout is ever modified, and the same for being
able to extract the necessary information from images of different distributions.

It could also benefit from a few more smarts instead of blindly delegating a lot
of the work to shell commands and hoping for the best; e.g., verifying that a
valid GPT was extracted, and/or reading the extracted GPT to locate the kernel
and root filesystem, instead of using hard coded values.


## Usage

The script expects 2 arguments on the command line, a path to the directory of
the OpenATV 6.4 disk.img file, and a partition layout string. A 3rd argument can
also be provided, which will replace the IP address of the TFTP server to use
(note that no verification is done on the address).

The partition layout string is a sequence of partition type/size (in MiB), where
the type is indicated by a single lower case letter.

The following partition types are supported:
* b - boot
* r - recovery
* K - recovery kernel
* k - kernel
* l - linuxrootfs
* u - userdata
* s - swap


## Recovery

There are 2 safety measures for recovery from a bad install, in these images.

The 1st is always trying to get boot commands via TFTP, from the server address
specified either in the script or overriden via the command line. This is
done via specific commands included in the STARTUP files in the boot partition.

The 2nd is (optionally) creating a recovery partition and taking advantage of
the capability of some receivers (e.g., Mut@nt HD51) to boot from selected
partitions for recovery, if the front panel button is kept pressed during the
power up boot process (and provided no ready to flash USB is inserted). This
capability is, unfortunately, lost by default on newer partition schemes,
unless the receiver boot loader supports it (not all do, and it generally
requires a boot loader update anyway). This capability is also lost if we'd
just create strange partition layouts, like the ones in this script, without
creating said recovery partition explicitly.

The recovery partition will take some space and it will only be used in case of
the recovery procedure being actuated. For now, it is only somehow optimized
(could be better) so around 128MiB of space is the recommended value for it.
This value might need to grow if we target newer images with the script (and can
possibly be reduced if we target older images, but didn't test this, OpenATV 6.4
was used while developing).

Creating a recovery kernel entry is optional but recommended, so one has the
flexibility of updating slot 1 at will - if one isn't created, the recovery
partition will boot with the slot 1 kernel, so be careful not to mess that one
if that's the case!


## RootFS

If both a linuxrootfs and userdata partitions are defined, the linuxrootfs one
will be used as the root file system by the kernel in the first kernel
partition; all other kernels will have their root file systems in the userdata
partition.

If only one of linuxrootfs or userdata partitions are defined, all kernels
will use it as the root file system. Typically it's preferable to create a
userdata partition instead of a linuxrootfs one, for this scenario.


## Example

To create an equivalent image to the original OpenATV 6.4 image, the partition
layout string would be similar to:

b3k8l1024k8k8k8s256u2411

This defines a layout with a 3MiB boot partition, 4 kernel partitions with 8MiB
each, the first one immediately followed by a 1GiB linuxrootfs partition;
additionally, a 256MiB swap partition is defined, as well as ~2.4GiB userdata
partition.

See the other adjacent text files for some other examples on how to create
different types of layouts.


## See also

* https://github.com/oottppxx/enigma2/tree/master/axhd51
* https://github.com/oottppxx/enigma2/tree/master/mutanthd51
* https://github.com/oottppxx/enigma2/tree/master/zgemmah7
