{
  description = "Borealis - Atmospheric & Astronomical Dynamic Wallpaper Engine";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }: let
    systems = flake-utils.lib.defaultSystems;
  in
    flake-utils.lib.eachSystem systems (system: let
      pkgs = import nixpkgs {inherit system;};
      lib = pkgs.lib;

      borealisPackage = pkgs.python3Packages.buildPythonApplication {
        pname = "borealis-wallpaper";
        version = "0.1.0";
        src = ./.;
        pyproject = true;

        build-system = [
          pkgs.python3Packages.setuptools
        ];

        nativeBuildInputs = [
          pkgs.makeWrapper
        ];

        # Add procps for pgrep (daemon checking)
        postFixup = ''
          wrapProgram $out/bin/borealis \
            --prefix PATH : ${lib.makeBinPath [pkgs.procps]}
        '';

        doCheck = false;

        meta = with lib; {
          description = "Atmospheric, astronomical, and space-weather dynamic wallpaper engine";
          homepage = "https://github.com/SpanishSyntax/Borealis";
          license = licenses.mit;
          mainProgram = "borealis";
        };
      };

      wallpapersPackage = pkgs.fetchzip {
        url = "https://github.com/SpanishSyntax/Borealis/releases/download/v0.1.0/wallpapers.tar.gz";
        hash = "sha256-S7mz5jrkJa2fF0B0zc/luO/c+rmRDLGzYfsrdamn040=";
        stripRoot = false;
      };
    in {
      packages = {
        default = borealisPackage;
        borealis = borealisPackage;
        wallpapers = wallpapersPackage;
      };

      apps.default = {
        type = "app";
        program = "${borealisPackage}/bin/borealis";
      };

      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          python3
          python3Packages.setuptools
          procps
          awww
        ];
      };
    })
    // {
      homeManagerModules = {
        default = self.homeManagerModules.borealis;
        borealis = {
          config,
          lib,
          pkgs,
          ...
        }: let
          cfg = config.services.borealis;
          tomlFormat = pkgs.formats.toml {};

          system = pkgs.stdenv.hostPlatform.system;
          defaultBorealis = self.packages.${system}.default;
          defaultWallpapers = self.packages.${system}.wallpapers;

          finalSettings = lib.recursiveUpdate {
            general = {
              backend = cfg.backend;
              interval = cfg.interval;
              telemetry_interval = cfg.telemetryInterval;
            };
          } cfg.settings;

          # Determine the directories to index
          resolvedDirs =
            (lib.optional cfg.includeDefaultWallpapers defaultWallpapers)
            ++ (lib.optional (cfg.wallpaperDir != null) cfg.wallpaperDir)
            ++ cfg.extraWallpaperDirs;

          dirArgs =
            if resolvedDirs == []
            then "-d ${config.home.homeDirectory}/.local/share/wallpapers"
            else lib.concatMapStringsSep " " (d: "-d ${toString d}") resolvedDirs;
        in {
          options.services.borealis = {
            enable = lib.mkEnableOption "Borealis dynamic atmospheric wallpaper daemon";

            package = lib.mkOption {
              type = lib.types.package;
              default = defaultBorealis;
              description = "The Borealis package to use.";
            };

            includeDefaultWallpapers = lib.mkOption {
              type = lib.types.bool;
              default = true;
              description = "Whether to download and include the bundled curated wallpapers from GitHub release.";
            };

            wallpaperDir = lib.mkOption {
              type = lib.types.nullOr (lib.types.either lib.types.path lib.types.str);
              default = null;
              description = "Primary directory containing wallpapers. If null, uses defaultWallpapers or ~/.local/share/wallpapers.";
            };

            extraWallpaperDirs = lib.mkOption {
              type = lib.types.listOf (lib.types.either lib.types.path lib.types.str);
              default = [];
              description = "Additional directories of user wallpapers to index alongside primary/default wallpapers.";
            };

            backend = lib.mkOption {
              type = lib.types.enum ["awww" "swww" "hyprpaper" "command"];
              default = "awww";
              description = "Wallpaper display backend to use.";
            };

            interval = lib.mkOption {
              type = lib.types.int;
              default = 20;
              description = "Wallpaper rotation interval in seconds.";
            };

            telemetryInterval = lib.mkOption {
              type = lib.types.int;
              default = 900;
              description = "Telemetry refresh interval in seconds.";
            };

            settings = lib.mkOption {
              type = tomlFormat.type;
              default = {};
              description = "Extra settings to merge into borealis.toml.";
            };
          };

          config = lib.mkIf cfg.enable {
            home.packages =
              [cfg.package]
              ++ lib.optional (cfg.backend == "awww" && (pkgs ? awww)) pkgs.awww
              ++ lib.optional (cfg.backend == "swww" && (pkgs ? swww)) pkgs.swww;

            xdg.configFile."borealis/borealis.toml" = lib.mkIf (cfg.settings != {}) {
              source = tomlFormat.generate "borealis.toml" finalSettings;
            };

            systemd.user.services.borealis = {
              Unit = {
                Description = "Borealis Dynamic Atmospheric Wallpaper Daemon";
                PartOf = ["graphical-session.target"];
                After = ["graphical-session.target"];
              };
              Service = {
                ExecStart = "${cfg.package}/bin/borealis ${dirArgs} -b ${cfg.backend} run";
                Restart = "on-failure";
                RestartSec = 5;
              };
              Install = {
                WantedBy = ["graphical-session.target"];
              };
            };
          };
        };
      };
    };
}
