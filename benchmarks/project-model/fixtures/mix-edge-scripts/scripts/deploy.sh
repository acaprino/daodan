#!/usr/bin/env bash
set -euo pipefail

if (( BASH_VERSINFO[0] < 4 )); then
  echo "bash 4 or later is required" >&2
  exit 1
fi

source "$(dirname "$0")/lib/log.bash"

declare -A targets=([staging]=stg.example.net [production]=prod.example.net)
log "deploying to ${targets[${1:-staging}]}"
rsync -az --delete ./dist/ "deploy@${targets[${1:-staging}]}:/srv/app/"
