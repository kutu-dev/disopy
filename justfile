# Fix formatting and linting issues
check:
  addlicense -l mpl .
  nix fmt

# See all the things that need to be done
todo:
  rg TODO:
  cat TODO.md

# Show this info message
help:
  just --list
