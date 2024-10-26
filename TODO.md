# TODO

## To be done
- Add warning for Nix/NixOS users about recompilation of ruff: https://github.com/astral-sh/ruff/issues/1699#issuecomment-2148528249.
- Add `PyPI` metadata to `pyproject.toml`.
- Add a `CONTRIBUTING.md` file with:
    - Explanation about how to set up the project.
        - `hatch shell`.
    - Packages that should be installed beforehand.
    - The unstable `developer` section.
- Add CONTRIBUTORS/CREDITS file.
- Check Subsonic on startup.
- Cache option in cli.
- Knuckles doesn't work with slashes on the names.
- Knuckles download again the files.

## To be added
- https://discordpy.readthedocs.io/en/stable/api.html#discord.utils.oauth_url

## Known issues
- The protocol prefix (`https://`) in the Subsonic config entry crash the program due to a bug in Knuckles.
