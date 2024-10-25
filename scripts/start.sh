#!/bin/bash

# Generate date.txt with current date
date +%Y-%m-%d > date.txt

# Make version script executable
chmod +x scripts/version.sh

echo "Generated date.txt with current date: $(cat date.txt)"
echo "Made version.sh executable"
