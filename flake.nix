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
      in
      {
        packages.parse = parseScript;

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [ nodejs yarn python3 python3Packages.pdfplumber ];
        };
      }) // {
        nixosModules.default = import ./nix/module.nix { inherit self; };
      };
}