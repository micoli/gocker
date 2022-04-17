#!/usr/local/bin/python3
import sys
import time

while True:
    print(time.time(), file=sys.stderr)
    time.sleep(2)
