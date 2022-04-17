#!/bin/sh

cd /app

npm install --production
pm2-runtime start /app/ecosystem.config.json