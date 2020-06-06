Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!

The party.py script allows one to create emmc_recovery images, with a specified
partition layout, for boxes like Zgemma H7, Mut@nt HD51, AX/Opticum HD51,
Vimastec VS1200, and maybe others.

It's currently based on OpenATV 6.4 emmc_recovery images, and it probably
requires code tweaks so it can extract the necessary information from other
distribution images.

Usage: the script expects 2 arguments on the command line, a path to the
directory of the OpenATV 6.4 disk.img file, and a partition layout string.

The partition layout string is a sequence of partition type/size (in MiB),
where the type is indicated by a single lower case letter.

The following partition types are supported:
b - boot
k - kernel
l - linuxrootfs
u - userdata
s - swap

Example, to create an equivalent image to the original OpenATV 6.4 image, the
partition layout string would be similar to:

b3k8l1024k8k8k8s256u2411

This defined a layout with a 3MiB boot partition, 4 kernel partitions with 8MiB
each, the first one immediately followed by a 1GiB linuxrootfs partition;
additionally a 256MiB swap partition is defined, as well as ~2.4GiB userdata
partition.

If both a linuxrootfs and userdata partitions are defined, the linuxrootfs one
will be used as the root file system by the kernel in the first kernel
partition; all other kernels will have their root file systems in the userdata
partition.

If only one of linuxrootfs or userdata partitions are defined, all kernels
will use it as the root file system. Typically it's preferable to create a
userdata partition instead of a linuxrootfs one, for this scenario.

See the other adjacent text files for some examples on how to create different
types of layouts.
