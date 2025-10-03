#!/bin/bash

usage() {
  cat <<EOF
Usage: $(basename "$0") <jobid> <token>

Description:
  Download the output tarball for a given job ID using the CHARMM-GUI API.
  If no output file is available, the script will show the error message
  instead of a .tgz archive.

Arguments:
  jobid       The job ID to download

Options:
  -h, --help  Show this help message and exit

Notes:
  - This script requires 'jq' for parsing JSON error messages.
EOF
}

# handle help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  usage
  exit 0
fi

# main
API="https://charmm-gui.org"

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

OUTFILE="charmm-gui-$JOBID.tgz"

# Perform request
curl -s -H "Authorization: Bearer $TOKEN" \
  -o "$OUTFILE" \
  "$API/?doc=jwt_download&jobid=$JOBID"

# Check if file is JSON (error) or tar archive
FILETYPE=$(file --mime-type -b "$OUTFILE")

if [[ "$FILETYPE" == "application/x-gzip" || "$FILETYPE" == "application/gzip" || "$FILETYPE" == "application/x-tgz" ]]; then
  echo "Download successful: $OUTFILE"
else
  echo "No output file available for job $JOBID."
  echo "Server response:"
  rm -f "$OUTFILE"
fi
