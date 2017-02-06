#!/bin/sh
# check current ranges with this script - or just pipe output to a cfg file.
ranges=`curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | jq -r '.prefixes[] | select(.service=="CLOUDFRONT") | .ip_prefix'`

for range in $ranges
do
  printf "set_real_ip_from %s;\n" "$range"
done
