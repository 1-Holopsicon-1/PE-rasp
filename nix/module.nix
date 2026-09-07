{ self }:

{ config, lib, pkgs, ... }:
with lib;
let
  cfg = config.services.raspisanie;
in
{
  options.services.raspisanie = {
    enable = mkEnableOption "Расписание физкультуры (статика)";

    package = mkOption {
      type = types.package;
      default = self.packages.${pkgs.system}.default;
      description = "Nix package с собранной статикой";
    };

    port = mkOption {
      type = types.port;
      default = 8080;
      description = "Порт для раздачи статики";
    };
  };

  config = mkIf cfg.enable {
    systemd.services.raspisanie = {
      description = "Расписание физкультуры — статик-сервер";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        WorkingDirectory = "${cfg.package}";
        ExecStart = "${pkgs.python3}/bin/python3 -m http.server ${toString cfg.port}";
        Restart = "on-failure";
      };
    };

    environment.systemPackages = [ cfg.package ];
  };
}