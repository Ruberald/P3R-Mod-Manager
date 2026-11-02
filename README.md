# P3R Mod Manager v2

Run `run.bat` with Python 3 installed. Choose Downloads, click **Scan recursively**, select packages, then **Import selected**. Choose the game's `P3R\Content\Paks` folder and toggle imported mods.

The scanner recognizes extracted `.pak` packages at any depth. Matching `.ucas` and `.utoc` files with the same normalized basename are imported with the `.pak` as one package. Normalization ignores spaces, underscores, and punctuation, accommodating filenames such as `Yukari Apron_P.ucas` alongside `YukariApron_P.pak`.

Screenshots are ignored. Source files are copied, not moved.

This version does not extract `.7z` archives. Extract them first, then scan the parent Downloads folder. It does not resolve incompatible mods or install mod-specific dependencies. Back up `~mods` before use.
