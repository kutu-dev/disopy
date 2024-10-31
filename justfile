# The default recipe of the justfile
default: run

# Setup the environment for the package
setup:
  hatch env prune
  hatch -vvv env create

# Run the project
run:
  hatch env run -- disopy -d -c ./dev/config

# Fix formatting and linting issues
check:
  addlicense -l mpl .
  # Run the flake formatting if the `nix` CLI is available
  command -v nix && nix fmt
  hatch env run -- mypy -p disopy
  hatch env run -- ruff check --fix
  hatch env run -- ruff format

# Check the docstrings coverage of the project
docstrings:
  docstr-coverage .

# See all the things that need to be done
todo:
  rg TODO:
  cat TODO.md

# Show this info message
help:
  just --list
