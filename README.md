# Disopy

> A basic Discord bot for Subsonic

## Installation

```sh
$ pip install dispoy
$ disopy # First run to generate the default config file
```

_Disopy supports Python 3.11 and newer._

## Configuration

The cofig file is located in `$XDG_CONFIG_PATH/disopy/disopy.json`, in most cases you'll see it as `~/.config/disopy/disopy.json`. The default config file looks like this:

```json
{
  "user": {
    "username": "",
    "password": ""
  },
  "subsonicUrl": "https://",
  "discordToken": "",
  "caCertsPath": ""
}
```

Fill it up with your data. The deploy of the bot in Discord won't be covered in this document as it's already explained in the [Discord Developer Portal](https://discord.com/developers/docs/intro) and other sources. See [Custom certs](#custom-certs) for more info about self signed certificates.

## Using

After you have your Discord Application created and invited the bot to a server start it with:

```sh
$ disopy
```

Wait until it reports a successful connection to the Discord and Subsonic APIs, then enjoy the power of selfhosting using [slash commands](https://support.discord.com/hc/en-us/articles/1500000368501-Slash-Commands-FAQ) (`/command`) in a text channel. All slash commands are self-explanatory by its descriptions.

### Custom CA Certs

If you want to use custom certs you can point a unencrypted PEM file in `"caCertsPath"` in the [configuration](#configuration).
_Tip:_ If you just want to use the certificates installed in your machine instead of the ones bundled in the [`requests`](https://docs.python-requests.org/en/latest/user/advanced/#ca-certificates) package you can set it as `"caCertsPath": "/etc/ssl/certs/ca-certificates.crt"` and in most cases, it will work.

## Quirks

The [Subsonic API search implementation](http://www.subsonic.org/pages/api.jsp#search3) doesn't support playlists so the search for them is made with a plain substring search making it more difficult to find the desired playlist. If anyone makes a better implementation of it feel free to contribute to the project with it.

## Author

Created with :heart: by [Kutu](https://kutu-dev.github.io).

> - GitHub - [kutu-dev](https://github.com/kutu-dev)
> - Twitter - [@kutu_dev](https://twitter.com/kutu_dev)
