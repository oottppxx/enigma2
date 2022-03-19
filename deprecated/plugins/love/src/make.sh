#!/bin/bash
PKG_NAME=$(grep OE control.tmpl | cut -d" " -f2)
CONTROL_FILES="postrm postinst preinst"
DATA_PATH=/usr/lib/enigma2/python/Plugins/Extensions/Love
DATA_FILES="README.txt love.png setup.xml plugin.pyo __init__.pyo"
VERSION_FILE=plugin.py
VERSION=$(grep VERSION= ${VERSION_FILE} | cut -d= -f2 | tr -d \')

rm -rf ipk
rm -rf control.tar.gz data.tar.gz ${PKG_NAME}*ipk
mkdir -p ipk/${DATA_PATH}
touch plugin.py __init__.py
python -O -m compileall plugin.py __init__.py
cp ${DATA_FILES} ipk/${DATA_PATH}
cat control.tmpl | sed "s#VERSION#${VERSION}#g" > control
tar czvf control.tar.gz control ${CONTROL_FILES}
cd ipk; tar czvf ../data.tar.gz *; cd ..
echo 2.0 > debian-binary
./myar.sh $(echo ${PKG_NAME}-VERSION.ipk | sed "s/VERSION/${VERSION}/g") debian-binary data.tar.gz control.tar.gz
