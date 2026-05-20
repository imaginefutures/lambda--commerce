#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/.build"
ZIP_PATH="$DIST_DIR/naver-commerce-api.zip"

rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

rsync -a \
  --exclude '.build' \
  --exclude 'dist' \
  --exclude 'tests' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  --exclude '.pytest_cache' \
  "$ROOT_DIR/" "$BUILD_DIR/"

cd "$BUILD_DIR"
zip -qr "$ZIP_PATH" .
rm -rf "$BUILD_DIR"

echo "$ZIP_PATH"
