#!/bin/bash

usage() {
  cat <<EOF
Usage: $(basename "$0") <jobid>

Description:
  This script queries the CHARMM-GUI API for the status of a given job ID.
  It will print the job status, the last output file, the modification time,
  and the last 30 lines from the output.

Arguments:
  jobid       The job ID to check

Options:
  -h, --help  Show this help message and exit

Notes:
  - This script requires 'jq' to be installed for JSON parsing.
    On macOS:   brew install jq
    On Ubuntu:  sudo apt-get install jq
    On CentOS:  sudo yum install jq

Examples:
  $(basename "$0") JOB12345
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

if [ "$#" -eq 0 ]; then
  echo "Illegal number of parameters"
  exit 1
fi

RESPONSE=$(curl -s -X GET "$API/check_status?jobid=$JOBID" \
    -H "Authorization: Bearer $TOKEN")

if [ -z "$RESPONSE" ]; then
  echo "Error: No response from server."
  exit 1
fi

# Extract fields

echo "$RESPONSE"
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
