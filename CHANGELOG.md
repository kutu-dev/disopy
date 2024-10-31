# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- A `volume` entry in the config file to set the base volume of all the songs.
- The following commands:
    - `/stop`.
    - `/queue`.
    - `/resume`.
    - `/pause`.
    - `/sync`.
- An acknowledgements section in the `README.md` file.
- CI/CD linting, formatting, publishing and Docker building.
- Publish the package to PyPI.
- Official `Dockerfile` and `compose.yaml` files.
- Official Docker package on the [GitHub Container Registry](ghcr.io).
- Docstrings 100% coverage.
- A [developer section](./CONTRIBUTING.md) in the config file for a better DX.

### Changed
- Bump up the Python version to `3.13.0`.
- The project is now licensed under the [MPL 2.0](https://www.mozilla.org/en-US/MPL/) license instead of the [MIT](https://opensource.org/license/MIT) license.
- The project now uses the [Hatch](https://hatch.pypa.io/latest/) Python project manager.
- Remake and clean the project from the ground up.
- The config file is now in [TOML](https://toml.io/) instead of [JSON](https://www.json.org/).
