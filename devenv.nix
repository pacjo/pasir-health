{ pkgs, lib, config, ... }:
let
  # Ubuntu ncurses + tinfo libs with ABI matching the precompiled binary
  ubuntuNcurses =
    pkgs.runCommand "ubuntu-ncurses"
      {
        nativeBuildInputs = [
          pkgs.zstd
          pkgs.binutils
        ];
        ncursesDeb = pkgs.fetchurl {
          url = "http://archive.ubuntu.com/ubuntu/pool/main/n/ncurses/libncurses6_6.5+20250216-2_amd64.deb";
          hash = "sha256-BmIPv4amPjJmq5KdzT3VIA8IqYOW5W0upodKZoB4eM8=";
        };
        tinfoDeb = pkgs.fetchurl {
          url = "http://archive.ubuntu.com/ubuntu/pool/main/n/ncurses/libtinfo6_6.5+20250216-2_amd64.deb";
          hash = "sha256-dKfxEtGTdMnMRZid8BjEsWD+A10vXfMc2bWsSRU1wEE=";
        };
      }
      ''
        mkdir -p $out/lib
        for deb in $ncursesDeb $tinfoDeb; do
          tmpdir=$(mktemp -d)
          (
            cd $tmpdir
            ar x $deb
            tar -xf data.tar.*
          )
          cp $tmpdir/usr/lib/x86_64-linux-gnu/*.so.* $out/lib/
          rm -rf $tmpdir
        done
      '';

  ebsimPatched = pkgs.stdenv.mkDerivation {
    name = "EBSimUnoEthCurses";
    src = ./sensor/misc;
    nativeBuildInputs = [ pkgs.makeWrapper ];
    buildInputs = [ ubuntuNcurses ];
    installPhase = ''
      mkdir -p $out/bin
      cp EBSimUnoEthCurses $out/bin/.EBSimUnoEthCurses-unwrapped
      makeWrapper $out/bin/.EBSimUnoEthCurses-unwrapped $out/bin/EBSimUnoEthCurses \
        --set LD_LIBRARY_PATH ${ubuntuNcurses}/lib
    '';
  };
in
{
  # sensor
  languages.cplusplus.enable = true;

  # gateway
  languages.python = {
    enable = true;
    directory = "./gateway";
    venv = {
      enable = true;
      requirements = ./gateway/requirements.txt;
    };
  };

  packages = with pkgs; [
    just
    protobuf
    platformio-core
    ebsimPatched
  ];
}
