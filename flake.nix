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

        # Собираем фронтенд через stdenv + yarn
        frontend = pkgs.stdenv.mkDerivation {
          pname = "raspisanie-frontend";
          version = "0.1.0";
          src = ./.;
          nativeBuildInputs = [ pkgs.yarn pkgs.nodejs ];
          # yarn.lock должен быть в репо. Если нужен offline-cache хеш —
          # собрать через `nix build` (он подскажет правильный фиксейшн хеш).
          yarnBuildPhase = ''
            yarn install --immutable
            yarn build
          '';
          installPhase = ''
            runHook preInstall
            mkdir -p $out
            cp -r build/* $out/
            runHook postInstall
          '';
        };

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

        # Итоговый пакет: статика + парсер в одном output
        default = pkgs.symlinkJoin {
          name = "raspisanie";
          paths = [ frontend ];
          buildInputs = [ pkgs.makeWrapper ];
          postBuild = ''
            mkdir -p $out/bin
            makeWrapper ${parseScript}/bin/raspisanie-parse $out/bin/raspisanie-parse
            mkdir -p $out/data
            cp ${frontend}/data/raspisanie.json $out/data/ 2>/dev/null || true
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