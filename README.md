# Gantry Crane

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

## Installation
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

Gocker

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
