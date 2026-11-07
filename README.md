# FrameGen Manager

A Linux desktop interface for installing and configuring [MFG Unlocker](https://github.com/dashdogy/MFG-Unlocker) for individual Windows games running through Steam and Proton. It provides multiplier selection, generates Proton launch options, and reads the unlocker's status file.

## Compatibility

- The DLSS route requires an NVIDIA RTX GPU and a game that already integrates DLSS Frame Generation. A 6× option is not guaranteed to work in every game or runtime.
- The app installs a DLL beside the game's actual executable. Loader names vary by game; check the [upstream compatibility guide](https://github.com/dashdogy/MFG-Unlocker/blob/main/docs/compatibility.md).
- Do not use the unlocker in games with anti-cheat.
- The app does not automatically edit Steam settings or manage existing mod installations it did not create.

## Requirements and launch

Linux with Steam, Proton, Python 3, Tkinter, and PyQt5. On Ubuntu-based systems these Python bindings are available as `python3-tk` and `python3-pyqt5`.

```bash
python3 app.py
```

1. Close the game and choose it in the Steam list, then browse to its real `.exe` file.
2. Select a loader name and multiplier; click **Install / update**.
3. Paste the game's existing Steam launch options into the app (use `%command%` if empty). Generate and copy the result into Steam → Properties → Launch Options.
4. Launch the game, enable DLSS Frame Generation in its settings, and check status in the app. Backspace opens the unlocker menu where supported.

To uninstall, close the game, use **Remove managed install**, and remove the added CUDA and DLL override from the Steam launch options. Existing DLLs and configurations are not overwritten. If managed files were changed outside the app, removal refuses to delete them; inspect and back them up before manual removal.

## Attribution

This project bundles **MFG Unlocker v1.7.0** by dashdogy. The bundled DLL is verified against the release SHA-256 at install time. See [MFG-UNLOCKER-LICENSE.txt](MFG-UNLOCKER-LICENSE.txt) and the [upstream project](https://github.com/dashdogy/MFG-Unlocker). This interface is independent of NVIDIA and the upstream project.
