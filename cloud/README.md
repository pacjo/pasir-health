# Cloud app

## Gettings started

1. Run whole stack as described in [../README.md](main README.md)
2. Open [http://localhost:1880/dashboard](http://localhost:1880/dashboard)


## Protobuf testing

Messages can be created and published manually. Below is an example for nushell+nix:

<!-- TODO: update for final schema -->
```nushell
(echo "data: 'hello there'" |
  nix run nixpkgs#protobuf -- --encode=Message shared/message.proto o> message.bin;
  hexdump message.bin;
  open message.bin |
  ncat -u 192.168.122.97 6000;
  rm message.bin)
```
