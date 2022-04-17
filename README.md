# Gocker

`Gui on dOCKER`

![CI](https://github.com/micoli/gocker/actions/workflows/ci.yml/badge.svg)

`gocker` purpose is to add a GUI/TUI to local docker instances, it is largely inspired by [K9S](https://k9scli.io/)


## Installation
```
pip install git+https://github.com/micoli/gocker.git
```
or for upgrade
```
pip install --upgrade --force-reinstall git+https://github.com/micoli/gocker.git
```

depending of your installation `pip` can be replaced by `pip3`

## Commands

### Help
[//]: <> (command-placeholder-start "gocker --help")
```
usage: gocker [-h] [--debug] [--verbose]
                     {fs-events,kill-fs-events,gui} ...

Colima host helper

positional arguments:
  {fs-events,kill-fs-events,gui}
                        commands
    fs-events           wath for filesystem changes and 'touch' on colima host
    kill-fs-events      kill fs-event daemon
    gui                 docker_container GUI

optional arguments:
  -h, --help            show this help message and exit
  --debug               Print lots of debugging statements
  --verbose             Be verbose
```
[//]: <> (command-placeholder-end)


### Command `gui`
[//]: <> (command-placeholder-start "gocker gui --help")
```
usage: gocker gui [-h] [--docker-host DOCKER_HOST]
                         [--fsevents-address FSEVENTS_ADDRESS]
                         [--fsevents-port FSEVENTS_PORT]

optional arguments:
  -h, --help            show this help message and exit
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
