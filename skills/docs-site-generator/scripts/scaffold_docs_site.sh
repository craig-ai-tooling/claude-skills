#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: scaffold_docs_site.sh <dest> --site-name <name>" >&2
}

if [ $# -lt 1 ]; then
  usage
  exit 1
fi

dest="$1"
shift

site_name=""
while [ $# -gt 0 ]; do
  case "$1" in
    --site-name)
      site_name="${2:-}"
      shift 2
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

if [ -z "$site_name" ]; then
  usage
  exit 1
fi

if [ -d "$dest" ] && [ -n "$(ls -A "$dest" 2>/dev/null)" ]; then
  echo "error: destination '$dest' already exists and is not empty; refusing to overwrite" >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
assets_dir="$script_dir/../assets"

mkdir -p "$dest/docs/overrides/stylesheets"

sed "s|__SITE_NAME__|$site_name|g" "$assets_dir/mkdocs.yml.tmpl" > "$dest/mkdocs.yml"
sed "s|__SITE_NAME__|$site_name|g" "$assets_dir/index.md.tmpl" > "$dest/docs/index.md"
cp "$assets_dir/brand.css" "$dest/docs/overrides/stylesheets/brand.css"
