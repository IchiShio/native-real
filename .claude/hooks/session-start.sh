#!/bin/bash
set -euo pipefail

# Only run in remote (web) environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install HTML linter
if ! command -v htmlhint &>/dev/null; then
  npm install -g htmlhint
fi

# Install Python dependencies for content generation scripts
pip3 install --quiet anthropic openai requests
