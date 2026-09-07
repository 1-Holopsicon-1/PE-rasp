{ self }:

{ config, lib, pkgs, ... }:
with lib;
let
  cfg = config.services.raspisanie;
in
{
  options.services.raspisanie = {
    enable = mkEnableOption "Расписание физкультуры (статика)";

    dataDir = mkOption {
      type = types.path;
      default = "/opt/PE-rasp/build";
      description = "Путь к собранной статике (build/)";
    };

    parseScript = mkOption {
      type = types.package;
      default = self.packages.${pkgs.system}.parse;
      description = "Nix package с обёрткой парсера";
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
        WorkingDirectory = "${cfg.dataDir}";
        ExecStart = "${pkgs.python3}/bin/python3 -m http.server ${toString cfg.port}";
        Restart = "on-failure";
      };
    };

    environment.systemPackages = [ cfg.parseScript ];
  };
}