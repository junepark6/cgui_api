#!/bin/bash

usage() {
  cat <<EOF
Usage: $(basename "$0") [jobid]

Description:
  This script queries the CHARMM-GUI API for job status.
  If jobid is provided, it prints detailed status for that job.
  If jobid is omitted, it prints a table of all jobs for the logged-in user.

Arguments:
  jobid       Optional job ID to check

Options:
  -h, --help  Show this help message and exit

Notes:
  - This script requires 'jq' to be installed for JSON parsing.
    On macOS:   brew install jq
    On Ubuntu:  sudo apt-get install jq
    On CentOS:  sudo yum install jq

Examples:
  $(basename "$0") JOB12345
  $(basename "$0")
EOF
}

# Check for --help or -h
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  usage
  exit 0
fi

# main
API="https://www.charmm-gui.org/api"

if [ ! -f session.token ]; then
  echo "Please login first."
  exit 1
fi

TOKEN=$(cat session.token)
JOBID="$1"
DATE_TZ="${TZ:-America/New_York}"

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required but not installed."
  exit 1
fi

if [ "$#" -gt 1 ]; then
  echo "Illegal number of parameters"
  usage
  exit 1
fi

if [ -n "$JOBID" ]; then
  RESPONSE=$(curl -s -X GET "$API/check_status?jobid=$JOBID" \
      -H "Authorization: Bearer $TOKEN")
else
  RESPONSE=$(curl -s -X GET "$API/check_status?check_rq=true" \
      -H "Authorization: Bearer $TOKEN")
fi
#echo $RESPONSE;
#exit;

if [ -z "$RESPONSE" ]; then
  echo "Error: No response from server."
  exit 1
fi

if ! echo "$RESPONSE" | jq -e . >/dev/null 2>&1; then
  echo "Error: Invalid JSON response from server."
  echo "$RESPONSE"
  exit 1
fi

# Stop early on API error payloads such as:
# {"error":"Invalid token","detail":"Expired token"}
if echo "$RESPONSE" | jq -e 'has("error") and has("detail")' >/dev/null 2>&1; then
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error')
  DETAIL_MSG=$(echo "$RESPONSE" | jq -r '.detail')
  echo "Error: $ERROR_MSG"
  echo "Detail: $DETAIL_MSG"
  exit 1
fi

format_created_date() {
  local value="$1"
  local ts

  if [[ "$value" =~ ^[0-9]+$ ]]; then
    ts="$value"
    if [ "${#ts}" -ge 13 ]; then
      ts=$((ts / 1000))
    fi

    TZ="$DATE_TZ" date -r "$ts" "+%B %-d, %Y, %-I:%M:%S %p %Z" 2>/dev/null \
      || TZ="$DATE_TZ" date -d "@$ts" "+%B %-d, %Y, %-I:%M:%S %p %Z" 2>/dev/null \
      || printf "%s" "$value"
  else
    printf "%s" "$value"
  fi
}

if [ -z "$JOBID" ]; then
  JOB_COUNT=$(echo "$RESPONSE" | jq '
    def jobs:
      if type == "array" then .
      elif has("jobs") and (.jobs | type == "array") then .jobs
      elif has("data") and (.data | type == "array") then .data
      elif has("results") and (.results | type == "array") then .results
      elif has("jobid") or has("JobID") then [.]
      else []
      end;
    jobs | length
  ')

  if [ "$JOB_COUNT" -eq 0 ]; then
    echo "No jobs found."
    exit 0
  fi

  printf "%-14s %-24s %-24s %-12s %-32s\n" "JobID" "Project" "module" "status" "date created"
  printf "%-14s %-24s %-24s %-12s %-32s\n" "--------------" "------------------------" "------------------------" "------------" "--------------------------------"

  echo "$RESPONSE" | jq -r '
    def text_or_na:
      if . == null or . == "" or (type == "boolean") then "N/A"
      else tostring
      end;
    def jobs:
      if type == "array" then .
      elif has("jobs") and (.jobs | type == "array") then .jobs
      elif has("data") and (.data | type == "array") then .data
      elif has("results") and (.results | type == "array") then .results
      elif has("jobid") or has("JobID") then [.]
      else []
      end;
    jobs[]
    | [
        (.jobid // .JobID // .id // .request.jobid | text_or_na),
        (.project // .Project // .request.project // .parameters.project | text_or_na),
        (.module // .modules // .Module // .request.module // .request.modules // .parameters.module | text_or_na),
        (.status // .state // .job_status // .request.status | text_or_na),
        (.date_created // .created_at // .created // .submitted_at // .creation_date // .dateCreated | text_or_na)
      ]
    | @tsv
  ' | while IFS=$'\t' read -r jobid project module status created; do
    created=$(format_created_date "$created")
    printf "%-14s %-24s %-24s %-12s %-32s\n" "$jobid" "$project" "$module" "$status" "$created"
  done

  exit 0
fi

# Extract fields

RANK=$(echo "$RESPONSE" | jq -r '.rank')
STATUS=$(echo "$RESPONSE" | jq -r '.status')
RQINFO=$(echo "$RESPONSE" | jq -r '.rqinfo')
HAS_TAR_FILE=$(echo "$RESPONSE" | jq -r '.hasTarFile')
LAST_OUT_FILE=$(echo "$RESPONSE" | jq -r '.lastOutFile')
LAST_OUT_TIME=$(echo "$RESPONSE" | jq -r '.lastOutTime')

# Pretty print
echo "======================================"
echo " Job ID          : $JOBID"
echo " Job Rank        : $RANK"
echo " Job Status      : $STATUS"
echo " Has Tar Archive : $HAS_TAR_FILE"
echo " Last Output File: $LAST_OUT_FILE"
echo " Last Modified   : $LAST_OUT_TIME"
echo "======================================"
echo "RQ Queue Status"
echo "--------------------------------------"
echo " Queue info      : $RQINFO"
echo "--------------------------------------"
echo " Last 30 Lines:"
echo "--------------------------------------"
echo "$RESPONSE" | jq -r '.lastOutLine'
echo "--------------------------------------"
