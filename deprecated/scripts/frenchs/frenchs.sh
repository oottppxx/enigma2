#!/bin/sh
PROVIDER="pmc"
BOUQUETS=$(ls -d /etc/enigma2/userbouquet.suls_iptv_${PROVIDER}_*.tv | grep -vi vod)
TICK="!!!"
HEINZSI="/tmp/heinz.inf"
STATUS="/tmp/frenchs.inf"

RUN="NO"
if [[ -f ${HEINZSI} ]]; then
  if [[ -f ${STATUS} ]]; then
    for CHECK in ${BOUQUETS} ${HEINZSI} ; do
      if [[ ${CHECK} -nt ${STATUS} ]]; then
        RUN="UPDATE"
      fi
    done
  else
    RUN="1ST"
  fi
  if [[ "${RUN}" != "NO" ]]; then
    while read -r LINE ; do
      FILES=$(grep -l "DESCRIPTION ${LINE}$" ${BOUQUETS})
      sed -ie "s/\(DESCRIPTION ${LINE}\)$/\\1 ${TICK}/g" ${FILES} >/dev/null 2>&1
    done < ${HEINZSI}
    wget -qO - http://127.0.0.1/web/servicelistreload?mode=0 >/dev/null 2>&1
  fi
fi

echo ${RUN} > ${STATUS}