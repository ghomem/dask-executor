#!/bin/bash

HOST=$1

if [ -z $HOST ]; then
  echo $( basename $0 ) HOST[:PORT]
  exit
fi

URL=$HOST/check_load

while true; do
  result=$(curl -s $URL)
  clear
  echo "Processing           | Queued"
  echo "---------------------+--------------------------------------------"
  echo $result | jq -r '
    def bar(n): (reduce range(0; n) as $i ([]; . + ["#"]) + (reduce range(n; 20) as $i ([]; . + [" "])) | join(""));
    [bar(.processing), bar(.queued)] | join(" | ")
  '
  echo
  sleep 1
done
