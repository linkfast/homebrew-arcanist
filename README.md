# Homebrew tap for Arcanist

[Arcanist](https://github.com/linkfast/arcanist) is a self-hosted music server. On macOS it comes as
**Arcanist.app**, which runs the server from the menu bar, opens at login and updates itself.

```sh
brew install --cask linkfast/arcanist/arcanist
```

Then open Arcanist from Applications; the admin panel is at http://localhost:8484/admin. macOS 14 or later, Apple
Silicon or Intel.

The app is not notarized yet: the first time, confirm it in **System Settings → Privacy & Security → Open Anyway**.

`brew uninstall --cask arcanist` removes the app; `brew uninstall --zap --cask arcanist` also removes its data
(`~/Library/Application Support/Arcanist`), never the music.

## How this tap is kept up to date

[`update.yml`](.github/workflows/update.yml) checks Arcanist's releases every hour and rewrites
[`Casks/arcanist.rb`](Casks/arcanist.rb) (version and SHA-256 of both disk images) with the newest one that has them,
pre-releases included while there are only pre-releases. It checks the cask with `brew style` and `brew audit` before
pushing it.

## License

MIT.
