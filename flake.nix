{
  description = "Расписание элективных дисциплин — статика + парсер";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        yarn-berry = pkgs.yarn-berry_4;

        # Собираем фронтенд: stdenv + yarn-berry offline cache
        frontend = pkgs.stdenv.mkDerivation (finalAttrs: {
          pname = "raspisanie-frontend";
          version = "0.1.0";
          src = ./.;

          offlineCache = yarn-berry.fetchYarnBerryDeps {
            inherit (finalAttrs) src;
            hash = "";
          };

          nativeBuildInputs = [
            pkgs.nodejs
            yarn-berry.yarnBerryConfigHook
          ];

          buildPhase = ''
            runHook preBuild
            yarn build
            runHook postBuild
          '';

          installPhase = ''
            runHook preInstall
            mkdir -p $out
            cp -r build/* $out/
            runHook postInstall
          '';
        });

        # Python-окружение для парсера
        pythonEnv = pkgs.python3.withPackages (p: [ p.pdfplumber ]);

        # Обёртка парсера
        parseScript = pkgs.writeShellApplication {
          name = "raspisanie-parse";
          runtimeInputs = [ pythonEnv ];
          text = ''
            exec python3 ${./scripts/parse.py} "$@"
          '';
        };

        # Итоговый пакет: статика + парсер
        default = pkgs.symlinkJoin {
          name = "raspisanie";
          paths = [ frontend ];
          buildInputs = [ pkgs.makeWrapper ];
          postBuild = ''
            mkdir -p $out/bin
            makeWrapper ${parseScript}/bin/raspisanie-parse $out/bin/raspisanie-parse
          '';
        };
      in
      {
        packages.default = default;
        packages.frontend = frontend;
        packages.parse = parseScript;

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [ nodejs yarn python3 python3Packages.pdfplumber ];
        };
      }) // {
        nixosModules.default = import ./nix/module.nix { inherit self; };
      };
}