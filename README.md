# GOCKER

`Gui on dOCKER`

![CI](https://github.com/micoli/gocker/actions/workflows/ci.yml/badge.svg)

`gocker` purpose is to add a GUI/TUI to local docker instances, it is largely inspired by [K9S](https://k9scli.io/)
- view logs / all logs
- inspect a container
- sort containers by name/cpu usage/memory usage
- kill an existing container
- open a shell in docker instances
- start/stop services in docker-compose
- interact with supervisord instance within a container

[![asciicast](https://asciinema.org/a/548247.svg)](https://asciinema.org/a/548247)

## Shortcuts
[//]: <> (command-placeholder-start "gocker --action shortcut-list")
```
╒═══════════╤═════════════════════════════╕
│ Key       │ Message                     │
╞═══════════╪═════════════════════════════╡
│ q         │ quit                        │
├───────────┼─────────────────────────────┤
│ ?         │ show help                   │
├───────────┼─────────────────────────────┤
│ k         │ kill container              │
├───────────┼─────────────────────────────┤
│           │ tag container               │
├───────────┼─────────────────────────────┤
│ i         │ inspect container           │
├───────────┼─────────────────────────────┤
│ s         │ shell in container          │
├───────────┼─────────────────────────────┤
│ s         │ start/stop in subprocess    │
├───────────┼─────────────────────────────┤
│ r         │ restart in subprocess       │
├───────────┼─────────────────────────────┤
│ s         │ start/stop composer service │
├───────────┼─────────────────────────────┤
│ <         │ previous sort column        │
├───────────┼─────────────────────────────┤
│ >         │ next sort column            │
├───────────┼─────────────────────────────┤
│ o         │ toggle sort order           │
├───────────┼─────────────────────────────┤
│ l         │ show logs                   │
├───────────┼─────────────────────────────┤
│ L         │ show all logs               │
├───────────┼─────────────────────────────┤
│ M         │ Add a marker in logs        │
├───────────┼─────────────────────────────┤
│ tab       │ select next pane            │
├───────────┼─────────────────────────────┤
│ shift tab │ select previous pane        │
╘═══════════╧═════════════════════════════╛
```
[//]: <> (command-placeholder-end)

## Docker Installation
```
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -it ghcr.io/micoli/gocker
```
or for upgrade
```
docker image rm ghcr.io/micoli/gocker:latest
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -it ghcr.io/micoli/gocker
```

## Local Installation
```
pip install git+https://github.com/micoli/gocker.git
```
or for upgrade
```
pip install --upgrade --force-reinstall git+https://github.com/micoli/gocker.git
```

depending of your installation `pip` can be replaced by `pip3`

## Container specific labels

### supervisord

```
  svc-XXXX:
    ...
    labels:
      - 'gocker-pm2={"host":"127.0.0.1","port": 13129,"username": "admin","password": "admin"}'
    ...
    ports:
      - 13129:9615
```

### auto open log

```
  svc-XXXX:
    ...
    labels:
      - 'gocker-log=true'
    ...
```

example:

## Commands

### Help
[//]: <> (command-placeholder-start "gocker --help")
```
usage: gocker [-h] [--action {gui,shortcut-list}] [--verbose] [--debug]
              [--docker-host DOCKER_HOST]
              [--fsevents-address FSEVENTS_ADDRESS]
              [--fsevents-port FSEVENTS_PORT]

gocker

optional arguments:
  -h, --help            show this help message and exit
  --action {gui,shortcut-list}
  --verbose             Be verbose
  --debug               Be very verbose
  --docker-host DOCKER_HOST
                        docker-host
  --fsevents-address FSEVENTS_ADDRESS
                        fsevents log address
  --fsevents-port FSEVENTS_PORT
                        fsevents log port
```
[//]: <> (command-placeholder-end)


Merge requests are welcomed


# TODO
- plugin events messenger
- pm2 subprocesses
- local minimalist htop


# Test with different python version:

```
docker run --rm -it -v $PWD:/app -v /var/run/docker.sock:/var/run/docker.sock python:3.7.13-buster bash
```

in docker :
```
cd /app;
export DOCKERVERSION=18.03.1-ce;
curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKERVERSION}.tgz && tar xzvf docker-${DOCKERVERSION}.tgz --strip 1 -C /usr/local/bin docker/docker && rm docker-${DOCKERVERSION}.tgz
docker ps
curl --silent -XGET --unix-socket /run/docker.sock http://localhost/version
./setup.py develop
gocker --docker-host unix:///var/run/docker.sock
```
