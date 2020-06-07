Join us in the [Enigma2Talk Telegram chatroom](https://t.me/talkenigma2)
to help with testing, provide ideas and all kind of suggestions or comments!


## Summary

The party.py script allows one to create disk images, with a specified partition
layout, for boxes like Zgemma H7, Mut@nt HD51, Opticum/AX51, Vimastec VS1500,
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
the OpenATV 6.4 disk.img file, and a partition layout string.

The partition layout string is a sequence of partition type/size (in MiB), where
the type is indicated by a single lower case letter.

The following partition types are supported:
* b - boot
* k - kernel
* l - linuxrootfs
* u - userdata
* s - swap


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


## RootFS

If both a linuxrootfs and userdata partitions are defined, the linuxrootfs one
will be used as the root file system by the kernel in the first kernel
partition; all other kernels will have their root file systems in the userdata
partition.

If only one of linuxrootfs or userdata partitions are defined, all kernels
will use it as the root file system. Typically it's preferable to create a
userdata partition instead of a linuxrootfs one, for this scenario.

