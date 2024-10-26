#!/bin/bash
sudo lsof -i :9000 | grep LISTEN | awk '{print $2}' | xargs -r kill -9
