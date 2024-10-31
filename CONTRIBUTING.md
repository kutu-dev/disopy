# Contributing

## Set up the project
Remember to set up the dependencies listed in the [README](./README.md) and the following ones:
- `addlicense`
- `just`
- `ripgrep`
- `hatch`
- `Python 3.13`
- `docstr-coverage`

If you are using Nix a `devShell` is available with all the dependencies set up:
```sh
nix develop
```
> [!WARNING]  
> Due to `pip` downloading an incompatible Ruff binary for NixOS and external binaries not aware of the local dependencies in a `venv`, a local Ruff compilation will be triggered when entering for the first time in the shell.

Then set up the environment:
```sh
just setup
```

And finally enter the `venv`:
```sh
hatch shell
```

In the `./dev` directory is located an example config file to be used in devepment, to load the bot with it start it like this:
```sh
DISOPY_SUBSONIC_PASSWORD=foo DISOPY_DISCORD_TOKEN=bar disopy -c ./dev/config
```

## Linting and formatting
You can check that your changes follow the lint and format guidelines and try to fix some of the issues by running:
```sh
just check
```

## Development extra configs
The `[developer]` section in the config is unstable, not verified or migrated and intended only for the development workflow. This section is the only living explanation of its entries:
- `discord-sync-guild`: The ID of the guild where the slash commands should always be sync in startup.
- `discord-sync-users`: The list of IDs of the users that are allowed to trigger a global slash commands cache regeneration with `/sync`.
