# Johnny Crash browser player

A browser interface for the user-provided Java ME game, running on FreeJ2ME Plus. The emulator runs on the server and streams frames to the browser; this is not an offline JavaScript port. One game session is shared by all viewers of the server.

## Run

Requires Python 3 and Java 17 or newer. If Java is not installed, run:

```sh
python3 -m pip install --target .runtime 'jdk4py==17.0.9.2'
```

Then start `python3 server.py` and open port 8001. Set `PORT` or `JAVA_BIN` to override the port or Java executable. The game JAR in `vendor/` was supplied by the user and may be subject to its original copyright; do not redistribute it without permission.

Controls: arrows, 5 / Enter / Space, Q (left soft key), W (right soft key), or on-screen buttons.

The emulator is [FreeJ2ME Plus](https://github.com/TASEmulators/freej2me-plus), licensed GPL-3.0-or-later; see `vendor/FREEJ2ME-LICENSE`. The included emulator was compiled from that project's source. The earlier independently created Worm Flight game remains in `legacy/`.

The emulator binary was compiled from FreeJ2ME Plus commit `3933e75ef927a95eab9f5e065f0b76dabf336069`: https://github.com/TASEmulators/freej2me-plus/tree/3933e75ef927a95eab9f5e065f0b76dabf336069

The bundled emulator initializes its frame limiter to 60 FPS before settings are loaded. Without this fix, the game can run too fast for tutorial input to respond. The modified source file is included at `vendor/freej2me-source/org/recompile/mobile/MobilePlatform.java`; all other emulator source is available at the upstream commit above. At the Texas tutorial, press Down repeatedly to scroll and close the instructions, then press 5 to launch.
