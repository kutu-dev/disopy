# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
{
  # TODO: Add description
  description = "";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    allSystems = [
      "x86_64-linux"
      "aarch64-darwin"
    ];

    forAllSystems = callback: nixpkgs.lib.genAttrs allSystems (system: callback {pkgs = import nixpkgs {inherit system;};});
  in {
    formatter = forAllSystems ({pkgs}: pkgs.alejandra);

    devShells = forAllSystems ({pkgs}: {
      default = pkgs.mkShell {
        # TODO: Maybe change its name
        name = "disopy";

        shellHook = ''
          export PIP_NO_BINARY="ruff"
        '';

        packages = with pkgs; [
          addlicense
          just
          ripgrep
          hatch
          python313

          ffmpeg
          libopus

          rustc
          cargo
        ];
      };
    });
  };
}
