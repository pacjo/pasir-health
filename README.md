# PASIR health

## Getting started

> [!IMPORTANT]
> This was tested on a fresh VM running Ubuntu Server 26.04


### Prerequisites

- Docker Engine with Compose support
- [just](https://github.com/casey/just) command runner
- `protoc` (protobuf compiler)


### Running

1. Generate protobuf Python stubs:
  ```bash
  just generate_protobuf
  ```
2. Start the project:
  ```bash
  docker compose up
  ```


## TODO:

- [ ] actually implement stuff
- [ ] maybe figure out permissions instead of running all containers as root
