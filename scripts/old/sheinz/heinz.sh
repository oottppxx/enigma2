#!/bin/bash
# Xp To, 2018 ;-)
# With big thanks to Ed, Bill, and Billy, and others at PMC:Enigma.


info () {
  echo
  echo "This is a poor-man's version of catch up support for PMC streams on Enigma boxes."
  echo "Tested under Zgemma w/OpenATV 6.0."
  echo
  echo "You'll need to place this script under /home/root/ and move the other scripts to /usr/script/."
  echo "Don't forget to chmod +x at least the ones under /usr/script/."
  echo
  echo "You'll also need to edit this file and fill in your username/password."
  echo
}



USERNAME=
PASSWORD=



# Don't left pad offsets with 0 (i.e., +8 is good, +08 isn't).
PREVIOUS="-30"
NEXT="+30"
REWIND="-5" # Short intervals might give you a far than perfect stream...
FORWARD="+5"
DEFDURATION="240" # No idea if the duration is really used, setting to 4h...
TS_OFFSET="+60" # Streams seem to be off by 1h when accessing timeshift.

BOUQUET="/etc/enigma2/userbouquet.favourites.tv"

KETCHUP='1:0:1:0:0:0:0:0:0:0:http%3a//service.the-pm.club/streaming/timeshift.php?username=USERNAME&password=PASSWORD&stream=STREAM&start=START&duration=DURATION:HEINZ'




### END OF SETTINGS ###

GET='wget -q -O - http://127.0.0.1/web/'

DATEFMT="+%Y-%m-%d:%H-%M"
NOSTART="1092-01-01:00-00"

### END OF HELPERS ###

escape () {
  echo "${1}" \
    | sed 's#%#%25#g;s#\&#%26#g;s#:#%3A#g;s#=#%3D#g;s#?#%3F#g'
}

zap () {
  ESCREF=$(escape "${1}")
# Uncommenting this can show your username/password on screen!
  #echo "${ESCREF}"
  ${GET}zap?sRef=${ESCREF} 2>&1 >/dev/null
}

reload_bouquets () {
  ${GET}servicelistreload?mode=0 2>&1 >/dev/null
}

new_ref () {
  STREAM="${1}"
  START=$(echo "${2}" | sed 's#:#%3a#')
  DURATION="${3}"
  NEWREF=$( \
    echo ${KETCHUP} \
      | sed "s#USERNAME#${USERNAME}#g" \
      | sed "s#PASSWORD#${PASSWORD}#g" \
      | sed "s#STREAM#${STREAM}#g" \
      | sed "s#START#${START}#g" \
      | sed "s#DURATION#${DURATION}#g" \
  )
  echo "${NEWREF}"
}

write_fav () {
  REF="${1}"
  echo "#NAME Favourites (TV)" > ${BOUQUET}
  echo "#SERVICE ${REF}" >> ${BOUQUET}
  echo "#DESCRIPTION HEINZ" >> ${BOUQUET}
}

get_current () {
  ${GET}getcurrent \
    | grep e2servicereference \
    | sed 's#^.*<e2servicereference>##g;s#</e2servicereference>##g;s#\&amp;#\&#g;s#%253a#%3a#g'
}

get_stream () {
  REF="${1}"
  if [[ "${REF}" == *timeshift* ]]; then
    echo "${REF}" | sed 's#.*stream=##g;s#&.*##g'
    return
  fi
  if [[ "${REF}" == *.ts* ]]; then
    echo "${REF}" | sed 's#.*/##g;s#\.ts.*##g'
    return
  fi
  echo ""
}

get_start () {
  REF="${1}"
  if [[ "${REF}" == *timeshift* ]]; then
    echo "${REF}" | sed 's#.*start=##g;s#&.*##g;s#%3a#:#g'
    return
  fi
  if [[ "${REF}" == *.ts* ]]; then
    NOW=$(date "${DATEFMT}")
    offset_minutes "${NOW}" "${TS_OFFSET}"
    return
  fi
  echo "${NOSTART}"
}

offset_minutes () {
  START="${1}"
#  echo "ST: ${START}"
  OFFSET="${2}"
#  echo "OFS: ${OFFSET}"
  MINUTES=$(echo "${START}" | sed 's#^.*:...##;s#^0*##g')
# echo "MINS: ${MINUTES}"
  MINUTES=$((${MINUTES}${OFFSET}))
#  echo "OFS_MINS: ${MINUTES}"
  YMDH=$(echo "${START}" | sed 's#^\(.*:..\).*#\1#;s#-#\.#g;s#:#-#g')
#  echo "YMDH: ${YMDH}"
  NEWSTART="${YMDH}:${MINUTES}"
#  echo "NS: ${NEWSTART}"
  date "${DATEFMT}" -d "${NEWSTART}"
}

move () {
  OFFSET="${1}"
  REF=$(get_current)
# Uncommenting this can show your username/password on screen!
#  echo "REF: ${REF}"
  STREAM=$(get_stream "${REF}")
  echo "ST: ${STREAM}"
  if [[ "x${STREAM}x" != "xx" ]]; then
    START=$(get_start "${REF}")
    echo "FROM: ${START}"
    NEWSTART=$(offset_minutes "${START}" "${OFFSET}")
    echo "TO: ${NEWSTART}"
    NEWREF=$(new_ref "${STREAM}" "${NEWSTART}" "${DEFDURATION}")
# Uncommenting this can show your username/password on screen!
#    echo "${NEWREF}"
    write_fav "${NEWREF}"
    reload_bouquets
    zap "${NEWREF}"
  fi
}

previous () {
  move "${PREVIOUS}"
}

next () {
  move "${NEXT}"
}

rewind () {
  move "${REWIND}"
}

forward () {
  move "${FORWARD}"
}

info
