#!/usr/bin/env bash
set -o errexit

# GitPython needs the git binary for GitHub repo ingestion.
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq git >/dev/null
fi

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
