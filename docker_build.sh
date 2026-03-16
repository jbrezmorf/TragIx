#!/bin/bash
# Build a songbook variant inside Docker.
# Usage: ./docker_build.sh <variant> [target] [edition]
# Example: ./docker_build.sh zboznej all 2026
#          ./docker_build.sh nezboznej rebuild 2025
#          ./docker_build.sh zboznej rebuild        # legacy: reads from input/

set -e

VARIANT="${1:?Usage: $0 <variant> [target] [edition]}"
TARGET="${2:-all}"
EDITION="${3:-}"
IMAGE_NAME="tragix-songbook"

EDITION_ARG=""
if [ -n "$EDITION" ]; then
  EDITION_ARG="--edition $EDITION"
fi

docker build -t "$IMAGE_NAME" .

docker run --rm \
  -v "$(pwd)/${VARIANT}/build:/songbook/${VARIANT}/build" \
  "$IMAGE_NAME" \
  --variant "$VARIANT" --target "$TARGET" $EDITION_ARG

echo "Done. Output in ${VARIANT}/build/"
