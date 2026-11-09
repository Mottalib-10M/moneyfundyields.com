#!/bin/bash
# Monthly refresh, run by hand (no scheduled workflow yet — the site says "updated by hand").
# Downloads, into data/raw/ (outside git):
#   1. the last four monthly Form N-MFP data sets published by the SEC (DERA), for the daily 7-day yields
#      and the quarter-end holdings;
#   2. the Form N-MFP3 reports filed in the first business days of the current month (EDGAR daily
#      indexes), which carry the latest month-end before the DERA data set comes out;
#   3. the SEC mutual-fund ticker file and the Treasury daily bill rates.
# SEC fair-access policy: declared User-Agent, at most 10 requests per second (we stay near 4).
# Usage: bash scripts/fetch-nmfp.sh YYYYMMDD-YYYYMMDD [...]   (DERA file stems)  --days YYYYMMDD,YYYYMMDD,...
set -euo pipefail
UA="moneyfundyields.com contact@moneyfundyields.com"
RAW="$(cd "$(dirname "$0")/.." && pwd)/data/raw"
mkdir -p "$RAW/edgar/filings" "$RAW/tickers" "$RAW/treasury"
DAYS=""
STEMS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --days) DAYS="$2"; shift 2;;
    *) STEMS+=("$1"); shift;;
  esac
done
for s in "${STEMS[@]}"; do
  d="$RAW/dera-$s"; mkdir -p "$d"
  [ -s "$d/nmfp.zip" ] || curl -sf -A "$UA" -o "$d/nmfp.zip" "https://www.sec.gov/files/dera/data/form-n-mfp-data-sets/${s}_nmfp.zip"
  (cd "$d" && unzip -o -q nmfp.zip)
  sleep 0.5
done
: > "$RAW/edgar/index-lines.txt"
for day in ${DAYS//,/ }; do
  q=$(( (10#${day:4:2} - 1) / 3 + 1 ))
  f="$RAW/edgar/form.$day.idx"
  [ -s "$f" ] || curl -sf -A "$UA" -o "$f" "https://www.sec.gov/Archives/edgar/daily-index/${day:0:4}/QTR$q/form.$day.idx"
  grep -E '^N-MFP3' "$f" >> "$RAW/edgar/index-lines.txt" || true
  sleep 0.3
done
awk '{print $NF}' "$RAW/edgar/index-lines.txt" | while read -r p; do
  out="$RAW/edgar/filings/$(basename "$p")"
  [ -s "$out" ] && continue
  curl -sf -A "$UA" -o "$out" "https://www.sec.gov/Archives/$p"
  sleep 0.25
done
curl -sf -A "$UA" -o "$RAW/tickers/company_tickers_mf.json" https://www.sec.gov/files/company_tickers_mf.json
Y=$(date +%Y)
curl -sf -A "Mozilla/5.0" -o "$RAW/treasury/bills.csv" "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/$Y/all?type=daily_treasury_bill_rates&field_tdr_date_value=$Y&page&_format=csv"
echo "fetched: $(ls "$RAW/edgar/filings" | wc -l) N-MFP3 reports, ${#STEMS[@]} DERA data sets"
