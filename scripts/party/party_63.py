#!/usr/bin/python
# 2020, @oottppxx

import os
import re
import sys
import zlib

VERSION='202006141136'

TFTPD='192.168.0.50'

# 3726MiB max across partitions.
# for alignment, 7632895 works better?!
MAX_LBA=7634910

RECO_KLABEL='kernel'

IMG='disk.img'
TMP_PARTY='/mnt/hdd/party'
NEW_IMG=os.path.join(TMP_PARTY, 'new_disk.img')

TMP_GPT=os.path.join(TMP_PARTY, 'gpt')
TMP_BOOT=os.path.join(TMP_PARTY, 'boot')
TMP_KERNEL=os.path.join(TMP_PARTY, 'kernel')
TMP_ROOTFS=os.path.join(TMP_PARTY, 'rootfs')

TMP_MBOOT=os.path.join(TMP_PARTY, 'mboot')
TMP_STARTUP=os.path.join(TMP_PARTY, 'startup')

TMP_MRECO=os.path.join(TMP_PARTY, 'mreco')
TMP_MROOTFS=os.path.join(TMP_PARTY, 'mrootfs')

NEW_GPT=os.path.join(TMP_PARTY, 'new_gpt')
NEW_BOOT=os.path.join(TMP_PARTY, 'new_boot')
NEW_KERNEL=os.path.join(TMP_PARTY, 'new_kernel')
NEW_ROOTFS=os.path.join(TMP_PARTY, 'new_rootfs')
NEW_SWAP=os.path.join(TMP_PARTY, 'new_swap')
NEW_RECO=os.path.join(TMP_PARTY, 'new_reco')
NEW_KRECO=os.path.join(TMP_PARTY, 'new_kreco')

BOXMODE=''
BOXMODE_RE='^.*(?P<boxmode> [^ ]*)\'$'
BLINE=('ifconfig eth0 -auto && batch %(TFTPD)s:TFTPBOOT\n'
       'testenv -n INT && '
       'boot emmcflash0.%(LABELINDEX)s \'brcm_cma=440M@328M brcm_cma=192M@768M'
       ' root=/dev/mmcblk0p%(ROOTINDEX)s'
       ' rootsubdir=linuxrootfs%(SUBDIRINDEX)s'
       ' kernel=/dev/mmcblk0p%(KERNELINDEX)s'
       ' rw rootwait%(BOXMODE)s\'\n')

###

PBOOT=False
PRECO=False
PKRECO=False
PLINUXROOTFS=False
PUSERDATA=False
PSWAP=False
KNUM=0
FSNUM=0
# Stores tuples of (label, size in MiB).
GPT=[]
# Stores file names to be concatenated as to create the new image.
FILES=[]

BOOT_GUID='\xa2\xa0\xd0\xeb\xe5\xb9\x33\x44\x87\xc0\x68\xb6\xb7\x26\x99\xc7'
LINUX_GUID='\xaf\x3d\xc6\x0f\x83\x84\x72\x47\x8e\x79\x3d\x69\xd8\x47\x7d\xe4'
SWAP_GUID='\x6d\xfd\x57\x06\xab\xa4\xc4\x43\x84\xe5\x09\x33\xc8\x4b\x4f\x4f'
UNIQUE_GUID='\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
ZERO_4='\x00\x00\x00\x00'
ZERO_8='\x00\x00\x00\x00\x00\x00\x00\x00'

OK=0
E_ARGTOOFEW=1
E_ARGTOOMANY=2
E_READDISK=3
E_PARTYMKDIR=4
E_GPTWRITE=5
E_BOOTWRITE=6
E_KERNELWRITE=7
E_ROOTFSWRITE=8
E_LOOPMOUNT=9
E_COPYSTARTUP=10
E_UMOUNT=11
E_READSTARTUP=12
E_NEWBOOT=13
E_NEWRECO=14
E_NEWKERNEL=15
E_NEWROOTFS=16
E_NEWSWAP=17
E_ARGSCHEME=18
E_NOBOOT=19
E_NOKERNEL=20
E_NOFS=21
E_TOOMANY=22
E_CREATESTARTUP=23
E_EXCEEDLBA=24
E_CREATEGPT=25
E_CREATEIMAGE=26
E_PATCH=254

def number(s):
  acc = 0
  while s:
    n = NUMBER.get(s[0], None)
    if n is None:
      break
    acc = acc*10 + n
    s = s[1:]
  return acc, s

def boot(s):
  global GPT
  global FILES
  global PBOOT
  label='boot'
  if PBOOT:
    return True, 'only 1 boot partition allowed!'
#  if len(GPT):
#    return True, 'boot partition must be the 1st partition exactly!'
  size, s = number(s[1:])
  if not size:
    return True, 'boot partition requires a size > 0!'
  bs = 2048*512
  count = size
  try:
    error = os.system('dd if=/dev/zero of=%s bs=%d count=%d && mkfs.fat %s && mount %s %s' % (
        NEW_BOOT, bs, count, NEW_BOOT, NEW_BOOT, TMP_MBOOT))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file!' % NEW_BOOT
    sys.exit(E_NEWBOOT)
  GPT.append((label, size))
  FILES.append(NEW_BOOT)
  print '%s(%d)' % (label, size)
  PBOOT = True
  return False, s

def recovery(s):
  global GPT
  global FILES
  global PRECO
  label='recovery'
  if PRECO:
    return True, 'only 1 recovery partition allowed!'
  if KNUM > 0:
    return True, 'recovery partition must come before any kernel partition!'
  if len(GPT) != 1:
    return True, 'recovery partition must be the 2nd partition exactly!'
  size, s = number(s[1:])
  if not size:
    return True, 'recovery partition requires a size > 0!'
  bs = 2048*512
  count = size
  try:
    error = os.system('umount -f %s ; dd if=/dev/zero of=%s bs=%d count=%d && mkfs.ext4 %s && mount %s %s' % (
        TMP_MRECO, NEW_RECO, bs, count, NEW_RECO, NEW_RECO, TMP_MRECO))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file!' % NEW_RECO
    sys.exit(E_NEWRECO)
  try:
    error = os.system('umount -f %s ; mount %s %s' % (TMP_MROOTFS, TMP_ROOTFS, TMP_MROOTFS))
  except:
    error = -1
  if error:
    print 'Error: can\'t loop mount %s file in the %s directory!' % (TMP_ROOTFS, TMP_MROOTFS)
    sys.exit(E_LOOPMOUNT)
  try:
    error = os.system('cd %s/linuxrootfs1 && cp -aRf bin boot dev etc home lib proc run sbin sys tmp var %s' % (
        TMP_MROOTFS, TMP_MRECO))
    error += os.system('mkdir -p %s/usr && cd %s/linuxrootfs1/usr && cp -aRf bin sbin libexec %s/usr' % (
        TMP_MRECO, TMP_MROOTFS, TMP_MRECO))
    error += os.system('mkdir -p %s/usr/share && cd %s/linuxrootfs1/usr/share && cp -aRf udhcpc %s/usr/share' % (
        TMP_MRECO, TMP_MROOTFS, TMP_MRECO))
    error += os.system('mkdir -p %s/usr/lib && cp -af %s/linuxrootfs1/usr/lib/lib* %s/usr/lib' % (
        TMP_MRECO, TMP_MROOTFS, TMP_MRECO))
    error += os.system('sed -i -e "s/id:3/id:5/" %s/etc/inittab' % TMP_MRECO)
  except:
    error = -1
  if error:
    print 'Error: can\'t create recovery rootfs in %s!' % TMP_MRECO
    sys.exit(E_NEWRECO)
  try:
    error = os.system('cd / ; umount %s ; umount %s' % (TMP_MROOTFS, TMP_MRECO))
  except:
    error = -1
  if error:
    print 'Error: can\'t unmount %s or %s!' % (TMP_MROOTFS, TMP_MRECO)
    sys.exit(E_UMOUNT)
  GPT.append((label, size))
  FILES.append(NEW_RECO)
  PRECO = True
  return False, s

def rkernel(s):
  global GPT
  global FILES
  global PKRECO
  label = RECO_KLABEL
  kernel = NEW_KRECO
  if PKRECO:
    return True, 'only 1 recovery kernel partition allowed!'
  size, s = number(s[1:])
  if not size:
    return True, 'kernel partition requires a size > 0!'
  bs = 2048*512
  count = size
  try:
    error = 0
    if not KNUM:
      error = os.system('dd if=%s of=%s bs=%d count=%d' % (TMP_KERNEL, kernel, bs, count))
    else:
      label = '%s%d' % (label, KNUM+1)
      kernel = '%s%d' % (kernel, KNUM+1)
      if not (PBOOT and bool(FSNUM)):
        error = os.system('dd if=/dev/zero of=%s bs=%d count=%d' % (kernel, bs, count))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file!' % kernel
    sys.exit(E_NEWKERNEL)
  print '%s(%d)' % (label, size)
  GPT.append((label, size))
  FILES.append(NEW_KRECO)
  PKRECO = True
  return False, s

def kernel(s):
  global GPT
  global FILES
  global KNUM
  label = 'linuxkernel'
  kernel = NEW_KERNEL
  size, s = number(s[1:])
  if not size:
    return True, 'kernel partition requires a size > 0!'
  bs = 2048*512
  count = size
  try:
    error = 0
    if not KNUM:
      error = os.system('dd if=%s of=%s bs=%d count=%d' % (TMP_KERNEL, kernel, bs, count))
    else:
      label = '%s%d' % (label, KNUM+1)
      kernel = '%s%d' % (kernel, KNUM+1)
      if not (PBOOT and bool(FSNUM)):
        error = os.system('dd if=/dev/zero of=%s bs=%d count=%d' % (kernel, bs, count))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file!' % kernel
    sys.exit(E_NEWKERNEL)
  print '%s(%d)' % (label, size)
  GPT.append((label, size))
  if PRECO and not bool(KNUM) and not PKRECO:
    GPT.append((RECO_KLABEL, size))
  if not (PBOOT and bool(KNUM) and bool(FSNUM)):
    FILES.append(kernel)
  KNUM += 1
  return False, s

def data(s, l):
  global GPT
  global FILES
  global FSNUM
  label = l
  rootfs = NEW_ROOTFS
  size, s = number(s[1:])
  if not size:
    return True, 'rootfs partition requires a size > 0!'
  bs = 2048*512
  count = size
  try:
    error = 0
    if not FSNUM:
      error = os.system('dd if=%s of=%s bs=%d count=%d' % (TMP_ROOTFS, rootfs, bs, count))
      pass
    else:
      if not (PBOOT and bool(KNUM)):
        rootfs = '%s2' % rootfs
        error = os.system('dd if=/dev/zero of=%s bs=%d count=%d' % (rootfs, bs, count))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file!' % rootfs
    sys.exit(E_NEWROOTFS)
  print '%s(%d)' % (label, size)
  GPT.append((label, size))
  if not (PBOOT and bool(KNUM) and bool(FSNUM)):
    FILES.append(rootfs)
  FSNUM += 1
  return False, s

def linuxrootfs(s):
  global PLINUXROOTFS
  if PLINUXROOTFS:
    return True, 'only 1 linuxrootfs partition allowed!'
  PLINUXROOTFS = True
  label = 'linuxrootfs'
  return data(s, label)

def userdata(s):
  global PUSERDATA
  if PUSERDATA:
    return True, 'only 1 userdata partition allowed!'
  PUSERDATA = True
  label = 'userdata'
  return data(s, label)

def swap(s):
  global GPT
  global FILES
  global PSWAP
  if PSWAP:
    return True, 'only 1 swap partition allowed!'
  label = 'swap'
  swap = NEW_SWAP
  size, s = number(s[1:])
  if not size:
    return True, 'swap partition requires a size > 0!'
  bs = 2048*512
  count = size
  try:
    error = 0
    if not (PBOOT and bool(KNUM) and bool(FSNUM)):
      error = os.system('dd if=/dev/zero of=%s bs=%d count=%d' % (swap, bs, count))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file!' % swap
    sys.exit(E_NEWSWAP)
  print '%s(%d)' % (label, size)
  GPT.append((label, size))
  if not (PBOOT and bool(KNUM) and bool(FSNUM)):
    FILES.append(swap)
  PSWAP = True
  return False, s

def error(s):
  return True, '%s unknown partition type, aborting...' % s[0]

NUMBER={
  '0': 0,
  '1': 1,
  '2': 2,
  '3': 3,
  '4': 4,
  '5': 5,
  '6': 6,
  '7': 7,
  '8': 8,
  '9': 9,
}

FUN={
  'b': boot,
  'r': recovery,
  'K': rkernel,
  'k': kernel,
  'l': linuxrootfs,
  'u': userdata,
  's': swap,
}

def partition(s):
  while s:
    f = FUN.get(s[0], error)
    err, s = f(s)
    if err:
      print 'Error: %s' % s
      sys.exit(E_ARGSCHEME)

def patch_63():
  try:
    error = os.system('dd if=/dev/zero of=zeropadfs bs=29360128 count=8')
    error += os.system('cat %s zeropadfs > zprootfs && mv zprootfs %s' % (TMP_ROOTFS, TMP_ROOTFS))
    error += os.system('umount -f %s ; mount %s %s' % (TMP_MROOTFS, TMP_ROOTFS, TMP_MROOTFS))
    error += os.system('cd %s && mkdir linuxrootfs1 && mv * linuxrootfs1 ; mv linuxrootfs1/lost+found .' % TMP_MROOTFS)
  except:
    error = -1
  if error:
    print 'Error: can\'t patch 6.3 rootfs in %s!' % TMP_MROOTFS
    sys.exit(E_PATCH)

def create_party():
  try:
    error = os.system('mkdir -p %s && mkdir -p %s && mkdir -p %s && mkdir -p %s' % (
        TMP_PARTY, TMP_MBOOT, TMP_MRECO, TMP_MROOTFS))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s directory!' % TMP_PARTY
    sys.exit(E_PARTYMKDIR)
  bs = 2048*512
  skip = 0
  count = 1
  try:
    error = os.system('dd if=%s of=%s bs=%d skip=%d count=%d' % (IMG, TMP_GPT, bs, skip, count))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file from %s!' % (TMP_GPT, IMG)
    sys.exit(E_GPTWRITE)
  skip = 1
  count = 3
  try:
    error = os.system('dd if=%s of=%s bs=%d skip=%d count=%d' % (IMG, TMP_BOOT, bs, skip, count))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file from %s!' % (TMP_BOOT, IMG)
    sys.exit(E_BOOTWRITE)
  skip = 4
  count = 8
  try:
    error = os.system('dd if=%s of=%s bs=%d skip=%d count=%d' % (IMG, TMP_KERNEL, bs, skip, count))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file from %s!' % (TMP_KERNEL, IMG)
    sys.exit(E_KERNELWRITE)
  bs = 12*2048*512
  skip = 1
  try:
    error = os.system('dd if=%s of=%s bs=%d skip=%d' % (IMG, TMP_ROOTFS, bs, skip))
  except:
    error = -1
  if error:
    print 'Error: can\'t create %s file from %s!' % (TMP_ROOTFS, IMG)
    sys.exit(E_ROOTFSWRITE)

  patch_63()

  try:
    error = os.system('umount -f %s ; mount -t vfat,ro,loop %s %s' % (TMP_MBOOT, TMP_BOOT, TMP_MBOOT))
  except:
    error = -1
  if error:
    print 'Error: can\'t loop mount %s file in the %s directory!' % (TMP_BOOT, TMP_MBOOT)
    sys.exit(E_LOOPMOUNT)
  try:
    error = os.system('cp %s %s' % (os.path.join(TMP_MBOOT, 'STARTUP'), TMP_STARTUP))
  except:
    error = -1
  if error:
    print 'Error: can\'t copy STARTUP file in the %s directory to %s!' % (TMP_MBOOT, TMP_STARTUP)
    sys.exit(E_COPYSTARTUP)
  try:
    error = os.system('umount %s' % TMP_MBOOT)
  except:
    error = -1
  if error:
    print 'Error: can\'t unmount %s!' % TMP_MBOOT
    sys.exit(E_UMOUNT)

def get_boxmode():
  global BOXMODE
  try:
    with open(TMP_STARTUP, 'r') as startup:
      boot_line = startup.readlines()[0]
  except:
    print 'Error: can\'t read %s!' % TMP_STARTUP
    sys.exit(E_READSTARTUP)
  m = re.match(BOXMODE_RE, boot_line)
  if m:
    BOXMODE = m.group('boxmode')
    print 'Found boxmode: %s' % BOXMODE
  else:
    print 'Warning: couldn\'t find boxmode in boot line!'

def create_startup():
  linuxrootfs_index = 0
  userdata_index = 0
  partition_index = 0
  kernels = []
  labels = []
  for l, _ in GPT:
    partition_index += 1
    if 'linuxrootfs' in l:
      linuxrootfs_index = partition_index
    if 'userdata' in l:
      userdata_index = partition_index
    if 'linuxkernel' in l:
      kernels.append(partition_index)
      labels.append(l)
  if not (linuxrootfs_index or userdata_index):
    print 'Error: at least 1 linuxrootfs or userdata partition is required!'
    sys.exit(E_NOFS)
  label_index = 0
  for k in kernels:
    label = str(labels[label_index])
    label_index += 1
    subdir_index = label_index
    kernel_index = k
    if (label_index == 1 and linuxrootfs_index) or not userdata_index:
      root_index = linuxrootfs_index
    else:
      root_index = userdata_index
    startup_file = os.path.join(TMP_MBOOT, 'STARTUP_%d' % subdir_index)
    try:
      with open(startup_file, 'w') as f:
        line = BLINE % {'TFTPD': TFTPD,
                        'LABELINDEX': label,
                        'ROOTINDEX': root_index,
                        'SUBDIRINDEX': subdir_index,
                        'KERNELINDEX': kernel_index,
                        'BOXMODE': BOXMODE}
        f.writelines([line])
    except:
      print 'Error: couldn\'t create file %s!' % startup_file
      sys.exit(E_CREATESTARTUP)
  startup_file = os.path.join(TMP_MBOOT, 'STARTUP')
  startup_1_file = os.path.join(TMP_MBOOT, 'STARTUP_1')
  try:
    error = os.system('cp %s %s' % (startup_1_file, startup_file))
  except:
    error = -1
  if error:
    print 'Error: couldn\'t create file %s!' % startup_file
    sys.exit(E_CREATESTARTUP)
  try:
    error = os.system('sync && umount %s' % TMP_MBOOT)
  except:
    error = -1
  if error:
    print 'Error: couldn\'t unmount %s!' % TMP_MBOOT
    sys.exit(E_UMOUNT)

def le32(x):
  x4 = chr((x & 0xff000000) >> 24)
  x3 = chr((x & 0x00ff0000) >> 16)
  x2 = chr((x & 0x0000ff00) >> 8)
  x1 = chr((x & 0x000000ff))
  return x1+x2+x3+x4

def lba_block(first_lba, s):
  next_lba = first_lba+s*2048
  last_lba = next_lba-1
  return (le32(first_lba & 0xffffffff)
          +le32((first_lba>>32&0xffffffff))
          +le32(last_lba & 0xffffffff)
          +le32((last_lba>>32)&0xffffffff)), next_lba
  
def label_block(label):
  if len(label) > 36:
    print 'Warning: label %s too big, truncating to 36 characters!' % label
  ulabel = label[:36].encode('utf-16')[2:]
  pad = 72-len(ulabel)
  return ulabel+pad*'\x00'

def fix_gpt_crc(gpt):
  pte_crc = zlib.crc32(gpt[0x400:0x4400])
  if pte_crc < 0:
    pte_crc = 0x100000000+pte_crc
  pc4 = chr((pte_crc & 0xff000000) >> 24)
  pc3 = chr((pte_crc & 0x00ff0000) >> 16)
  pc2 = chr((pte_crc & 0x0000ff00) >> 8)
  pc1 = chr((pte_crc & 0x000000ff))
  gpt = gpt[:0x258]+pc1+pc2+pc3+pc4+gpt[0x25c:]
  gpt = gpt[:0x210]+ZERO_4+gpt[0x214:]
  head_crc = zlib.crc32(gpt[0x200:0x25c])
  if head_crc < 0:
    head_crc = 0x100000000+head_crc
  hc4 = chr((head_crc & 0xff000000) >> 24)
  hc3 = chr((head_crc & 0x00ff0000) >> 16)
  hc2 = chr((head_crc & 0x0000ff00) >> 8)
  hc1 = chr((head_crc & 0x000000ff))
  return gpt[:0x210]+hc1+hc2+hc3+hc4+gpt[0x214:]

def create_gpt():
  global FILES
  try:
    with open(TMP_GPT, 'rb') as f:
      gpt = f.read(0x400)
    with open(NEW_GPT, 'wb') as f:
      previous_first_lba = 0
      first_lba = 2048
      index = 0
      for l, s in GPT:
        if 'recovery' == l or RECO_KLABEL == l or 'linuxrootfs' in l or 'userdata' == l or 'linuxkernel' in l:
          guid = LINUX_GUID
        if 'boot' == l:
          guid = BOOT_GUID
        if 'swap' == l:
          guid = SWAP_GUID
        if not RECO_KLABEL == l or PKRECO:
          previous_first_lba = first_lba
        print '>>> %s %d %d %d' % (l, s, previous_first_lba, first_lba)
        lba, first_lba = lba_block(previous_first_lba, s)
        print '<<< %s %d %d %d' % (l, s, previous_first_lba, first_lba)
        if first_lba > MAX_LBA:
          print 'Error: your partition layout exceeds the available space!'
          sys.exit(E_EXCEEDLBA)
        label = label_block(l)
        index += 1
        gpt += (guid+UNIQUE_GUID+chr(index)+lba+ZERO_8+label)
      pad = 2048*512-len(gpt)
      gpt += (pad*'\x00')
      f.write(fix_gpt_crc(gpt))
  except:
    print 'Error: can\'t generate new GPT!'
    sys.exit(E_CREATEGPT)
  FILES.insert(0, NEW_GPT)

def create_image():
  sources = ''
  for f in FILES:
    sources += ' %s' % f
  try:
    error = os.system('cat %s > %s' % (sources, NEW_IMG))
  except:
    error = -1
  if error:
    print 'Error: can\'t generate new image file %s!'
    sys.exit(E_CREATEIMAGE)

###


if len(sys.argv) < 3:
  print 'I\'m going to a path to disk.img and a partition layout string!'
  print 'Optionally, you can also indicate the TFTP server address'
  sys.exit(E_ARGTOOFEW)

if len(sys.argv) > 4:
  print 'Too many arguments!'
  sys.exit(E_ARGTOOMANY)

if len(sys.argv) > 3:
  TFTPD=sys.argv[3]

IMG = os.path.join(sys.argv[1], IMG)

create_party()
get_boxmode()
partition(sys.argv[2])

if not PBOOT:
  print 'Error: boot partition is required!'
  sys.exit(E_NOBOOT)

if not KNUM:
  print 'Error: at least 1 kernel partition is required!'
  sys.exit(E_NOKERNEL)
  
if not FSNUM:
  print 'Error: at least 1 linuxrootfs or userdata partition is required!'
  sys.exit(E_NOFS)

if len(NEW_GPT) > 128:
  print 'Error: too many partitions, max is 128!'
  sys.exit(E_TOOMANY)
  
print GPT
print FILES

create_startup()
create_gpt()
create_image()

print 'Ok'
sys.exit(OK)

