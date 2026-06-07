{ pkgs, lib, config, ... }:
{
  languages.python = {
    enable = true;
    venv = {
      enable = true;
      directory = "gateway";
      requirements = ./requirements.txt;
    };
  };

  packages = with pkgs; [
    just
    protobuf
  ];
}
