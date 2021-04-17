#!/bin/bash
FILE="${1}"
TIME="$(date "+%s")"
shift
echo "${*}"
printf "%b" '!<arch>\x0a' > "${FILE}"
for i in ${*} ; do
  printf "%-16s" "${i}/" >> "${FILE}"
  printf "%-12s" "${TIME}" >> "${FILE}"
  printf "%s" "0     0     100644  " >> "${FILE}"
  SIZE=$(ls -l ${i} | sed 's/ \+/ /g' | cut -d" " -f5 | cut -d" " -f5)
  OSIZE="${SIZE}"
  if [[ "$(( ${SIZE}%2 ))" == "1" ]]; then
    OSIZE="$((${SIZE}+1))"
  fi
  printf "%-10s" "${OSIZE}" >> "${FILE}"
  printf "%b" "\x60\x0a" >> "${FILE}"
  cat ${i} >> "${FILE}"
  if [[ "$(( ${SIZE}%2 ))" == "1" ]]; then
    printf "%b" "\x00" >> "${FILE}"
  fi
done
printf "%b" "\x0a" >> "${FILE}"
ar -vt "${FILE}"
