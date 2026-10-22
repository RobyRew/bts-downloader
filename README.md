# bts-downloader

A [BlockTheSpot](https://github.com/Nuzair46/BlockTheSpot) **mod** for the
experimental loader (`bts-loader.dll`). It changes two Remote Config defaults
that the Spotify desktop client consults around downloads and the offline
content capability.

This is not a patcher, not a client, and not a downloader implementation. It is a
declarative INI mod that the loader's patch engine applies to the app bundle, the
same way BlockTheSpot applies its own frontend patches.

- Target: Spotify **1.3.1.234** x64 (the version the experimental branch targets)
- Loader: `patches/` in BlockTheSpot's experimental layout
- Format: standalone INI mod, no DLL, nothing to compile

## What it changes

`[Buffer_modify]` names one SPA file, `pip-mini-player-snapshot.js`, and attaches
two patch groups:

| group | edit |
|---|---|
| `enableContentCapabilityEpisodeDownload-1` | `default:!1` → `default:!0` |
| `enableRemoteDownloads-2` | `default:!1` → `default:!0` |

Both are equal-length byte swaps inside the flag definitions. The loader's engine
rejects a replacement longer than its signature, so this is the only kind of
edit a declarative mod can express.

**Precedence matters:** the client resolves a property as
**local override → server value → default**. This mod changes the default. If the
server sends a value for either property, the server wins. The mod API (v2)
exposes `register_ini` and logging only — no override or memory API — so the
fallback is the developer menu the experimental build enables:
*Develop → Show debug window → Remote Config*. A local override set there does
outrank the server value.

## Install

1. Have the experimental BlockTheSpot loader installed: the `chrome_elf.dll`
   proxy, `bts-loader.dll` and `config.ini` in `%APPDATA%\Spotify`, with a
   `patches\` directory next to them.
2. Copy `spdl-offline.ini` into `%APPDATA%\Spotify\patches\`.
3. Quit Spotify completely, including the tray icon, and start it again.
4. Read `blockthespot-status.txt`. Expect `Mod spdl-offline.ini` with `ready`,
   and one row per patch target at `ready` or `applied`.

Optional validation, if `patch-tool.exe` ships with your loader build:

```
.\out\tools\patch-tool.exe inspect-mod .\patches\spdl-offline.ini
```

`skipped` or `failed` in the status file means the bytes did not match your
build. Regenerate — do not hand-edit the hex.

## Verify by observation, not by the UI

- Press download on a track.
- Watch for `storage-resolve/v2/files/audio/offline/…` in the client's traffic.
- Watch `%LOCALAPPDATA%\Spotify\Storage\` for new files.
- In the debug window, confirm the property's `localValue` / `remoteValue`
  actually changed; rows that differ from the default are flagged.

If the control appears but no resolve request fires, the gate is server-side and
no local edit moves it.

## Rebuild for another build

Signatures embed the flag's description text, and the file name must match the
zip entry, so the mod is build-specific. `tools/make-bts-pack.py` regenerates it
from an unpacked `xpui.spa`:

```
python3 tools/make-bts-pack.py xpui --list
```

```
python3 tools/make-bts-pack.py xpui enableContentCapabilityEpisodeDownload enableRemoteDownloads --to true --mod --version 1.3.1.234 > mod/spdl-offline.ini
```

On Windows the bundle lives at `%APPDATA%\Spotify\Apps\xpui.spa`. Use the version
the loader reports for your client in `[Compatibility]`.

## Repository layout

```
mod/spdl-offline.ini        the mod
tools/make-bts-pack.py      generator (--list, --mod, --version)
tools/validate_mod.py       CI check: sections, hex, equal-length rule
.github/workflows/release.yml   validate, package, publish
```

## Releases

Every push to `main` validates the mod and, if it passes, creates a release
tagged `v<date>-<short sha>` with `spdl-offline.zip` and the raw
`spdl-offline.ini`.

## Status

The current signatures were generated from the 1.3.1.234 app bundle. They have
not been loaded by `bts-loader.dll` on a Windows client. Treat this as
experimental: check `blockthespot-status.txt` before drawing conclusions, and
regenerate per build.

## Disclaimer

This project is **not affiliated with, endorsed by, or sponsored by Spotify AB or
the BlockTheSpot project**. "Spotify" is a trademark of Spotify AB. No Spotify
binary is redistributed here; the mod contains configuration that a third-party
loader applies to a client you already have installed.

If you are a rights holder, a maintainer, or anyone with a concern about this
repository, please open an issue or reach the maintainer through the GitHub
profile **before** taking any other action. We will respond and remove material
where appropriate.
