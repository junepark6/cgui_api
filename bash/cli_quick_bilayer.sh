#!/bin/bash

usage() {
cat <<EOF
Usage: $0 [OPTIONS]

Required (choose one set):
  --jobid STR           Job identifier from PDB Reader (required unless --membrane_only)
  --membrane_only       Build membrane_only system (no jobid required)

Membrane composition:
  --upper STR           Upper leaflet composition (e.g., "DOPC:POPC:CHL1=1:1:2")
  --lower STR           Lower leaflet composition (e.g., "DOPC:POPC:CHL1=1:2:1")
  --membtype STR        Preset membrane type (e.g., PMm, PMf, PMp, ENDm, aPM)

System settings:
  --margin FLOAT        Box boundary margin (required, e.g. 20)
  --wdist FLOAT         Z-length water boundary (default: 22.5)
  --ion_conc FLOAT      Ion concentration in M (default: 0.15)
  --ion_type STR        Ion type (default: NaCl)

General:
  -h, --help            Show this help and exit
  --clone-job           Clone the existing job folder before running setup.
                        Useful for generating multiple membrane systems from a single protein configuration.
  --run-ffconverter     Run FF-Converter to generate full MD input files (NAMD, GROMACS, OpenMM, etc.)
  --run-ppm             Run the PPM algorithm (Positioning of Proteins in Membranes) 
                        to optimize protein orientation in the lipid bilayer.
  --prot-projection-upper   Enable protein projection on the upper leaflet
  --prot-projection-lower   Enable protein projection on the lower leaflet

Notes:
  - Either (--upper and --lower) OR --membtype must be provided.
  - Either --jobid OR --membrane_only must be provided.
  - Requires 'jq' and 'curl'.
  - Export CHARMMGUI_TOKEN for the Bearer token.
EOF
}

# auth
TOKEN=$(cat session.token)
if [ ! -f session.token ]; then
  echo "Please login first."
  exit 1
fi

# defaults
JOBID=""; MEMBRANE_ONLY="false"; UPPER=""; LOWER=""; MEMBTYPE=""
MARGIN=""; WDIST="22.5"; ION_CONC="0.15"; ION_TYPE="NaCl"
CLONE_JOB="false"
RUN_FFCONVERTER="false"
RUN_PPM="false"
PROT_PROJECTION_UPPER="false"
PROT_PROJECTION_LOWER="false"

# --- Allowed presets ---
ALLOWED_PRESETS=(PMm PMf PMp ERm ERf GOLm GOLf ENDm LYSm VAC
                 MOM MIM THYp THYb aPM G-OM G-IM G+PM)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --jobid=*) JOBID="${1#*=}"; shift;;
    --jobid)
      JOBID="$2"; shift 2;;
    --membrane_only) MEMBRANE_ONLY="true"; shift;;
    --upper=*) UPPER="${1#*=}"; shift;;
    --upper)
      UPPER="$2"; shift 2;;
    --lower=*) LOWER="${1#*=}"; shift;;
    --lower)
      LOWER="$2"; shift 2;;
    --membtype=*) MEMBTYPE="${1#*=}"; shift;;
    --membtype)
      MEMBTYPE="$2"; shift 2;;
    --margin=*) MARGIN="${1#*=}"; shift;;
    --margin)
      MARGIN="$2"; shift 2;;
    --wdist=*) WDIST="${1#*=}"; shift;;
    --wdist)
      WDIST="$2"; shift 2;;
    --ion_conc=*) ION_CONC="${1#*=}"; shift;;
    --ion_conc)
      ION_CONC="$2"; shift 2;;
    --ion_type=*) ION_TYPE="${1#*=}"; shift;;
    --ion_type)
      ION_TYPE="$2"; shift 2;;
    --clone-job) 
      CLONE_JOB="true"; shift;;
    --run-ffconverter) 
      RUN_FFCONVERTER="true"; shift;;
    --run-ppm) 
      RUN_PPM="true"; shift;;
    --prot-projection-upper) 
      PROT_PROJECTION_UPPER="true"; shift;;
    --prot-projection-lower) 
      PROT_PROJECTION_LOWER="true"; shift;;
    -h|--help) usage; exit 0;;
    --) shift; break;;
    -*)
      echo "Unknown option: $1"
      exit 1;;
    *) # positional or stray arg
      echo "Unknown argument: $1"
      exit 1;;
  esac
done

# --- Validation ---
if [[ "$MEMBRANE_ONLY" != "true" && -z "$JOBID" ]]; then
  echo "Must specify --jobid unless --membrane_only is used"
  exit 1
fi

if [[ -z "$MARGIN" ]]; then
  echo "--margin is required"
  exit 1
fi

if [[ ( -z "$UPPER" || -z "$LOWER" ) && -z "$MEMBTYPE" ]]; then
  echo "Must specify either (--upper and --lower) OR --membtype"
  exit 1
fi

if [[ "$CLONE_JOB" == "true" && -z "$JOBID" ]]; then
  echo "--clone-job requires --jobid because it must copy an existing job directory."
  exit 1
fi

# endpoint
API="https://www.charmm-gui.org/api"

# Build curl args
CURL_STR="";
CURL_STR+="?margin=$MARGIN"
CURL_STR+="&wdist=$WDIST"
CURL_STR+="&ion_conc=$ION_CONC"
CURL_STR+="&ion_type=$ION_TYPE"

if [[ "$MEMBRANE_ONLY" == "true" ]]; then
  CURL_STR+="&membrane_only=true"
else
  CURL_STR+="&jobid=$JOBID"
fi

if [[ "$CLONE_JOB" == "true" ]]; then
  CURL_STR+="&clone_job=true"
fi

if [[ "$RUN_FFCONVERTER" == "true" ]]; then
  CURL_STR+="&run_ffconverter=true"
fi

if [[ "$RUN_PPM" == "true" ]]; then
  CURL_STR+="&ppm=true"
fi

if [[ "$PROT_PROJECTION_UPPER" == "true" ]]; then
  CURL_STR+="&prot_projection_upper=true"
fi
if [[ "$PROT_PROJECTION_LOWER" == "true" ]]; then
  CURL_STR+="&prot_projection_lower=true"
fi

if [[ -n "$MEMBTYPE" ]]; then
  valid=false
  for preset in "${ALLOWED_PRESETS[@]}"; do
    if [[ "$MEMBTYPE" == "$preset" ]]; then
      valid=true
      break
    fi
  done
  if [[ $valid == false ]]; then
    echo "Invalid --membtype '$MEMBTYPE'"
    echo "   Allowed values: ${ALLOWED_PRESETS[*]}"
    exit 1
  fi
  #CURL_STR+="&membtype=$MEMBTYPE"
  #curl -H "Authorization: Bearer $TOKEN" \
  #  -s -X POST "$API/quick_bilayer$CURL_STR"

  curl --data-urlencode "membtype=$MEMBTYPE" \
       -H "Authorization: Bearer $TOKEN" \
    -s -X POST "$API/quick_bilayer$CURL_STR"
else
  curl -d "upper=$UPPER" \
       -d "lower=$LOWER" \
       -H "Authorization: Bearer $TOKEN" \
    -s -X POST "$API/quick_bilayer$CURL_STR"
fi
