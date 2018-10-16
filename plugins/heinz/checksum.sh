#!/bin/sh
ls enigma2-plug* > checksums.md
echo >> checksums.md
md5 enigma2-plug* | cut -d" " -f4 | xargs echo MD5 >> checksums.md
echo >> checksums.md
shasum enigma2-plug* | cut -d" " -f1 | xargs echo SHA >> checksums.md
