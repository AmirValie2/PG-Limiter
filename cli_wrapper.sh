#!/bin/bash
# CLI wrapper for PG-Limiter
# Usage: pasarguard-limiter-cli [command]

cd /app
exec python cli_main.py "$@"
