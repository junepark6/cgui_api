#!/bin/bash

usage() {
  cat <<EOF
Usage: $(basename "$0") <email> <password>

Description:
  This script logs in to the CHARMM-GUI API and retrieves a Bearer token
  using the provided email and password. The token can then be used
  for subsequent API requests.

Arguments:
  email       The email address registered with CHARMM-GUI
  password    The corresponding password

Options:
  -h, --help  Show this help message and exit

Examples:
  $(basename "$0") user@example.com mypassword123

Notes:
  - The script will print the Bearer token on success.
  - Keep your token and password secure. Do not share them in logs or scripts.
  - Tokens may expire after 12 hours; you will need to re-login to get a new one.
  - This script requires 'jq' to be installed for JSON parsing.
    On macOS:   brew install jq
    On Ubuntu:  sudo apt-get install jq
    On CentOS:  sudo yum install jq
EOF
}

# check for --help or -h
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  usage
  exit 0
fi

# main
API="https://charmm-gui.org"

read -p "Email: " USERNAME
read -sp "Password: " PASSWORD
echo ""

RESPONSE=$(curl -s -X POST "$API/?doc=jwt_login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")
# Check for jq
if command -v jq >/dev/null 2>&1; then
  TOKEN=$(echo "$RESPONSE" | jq -r '.token')
else
  echo "Please install jq executable... (sudo apt-get install jq or brew install jq)."
  exit;
fi

if [[ "$TOKEN" == "null" || -z "$TOKEN" ]]; then
  echo "Login failed."
  echo "$RESPONSE"
  exit 1
else
  echo "$TOKEN" > session.token
  echo "Login successful. Token saved."
fi

