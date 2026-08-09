package com.silentiumlabs.silentiumos;

import java.io.File;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

public final class SystemDefinition {
    public static final String BEST = "BEST";
    public static final String ALL = "ALL";
    public static final String NES = "NES";
    public static final String SNES = "SNES";
    public static final String GB = "GB";
    public static final String GBA = "GBA";
    public static final String GENESIS = "GENESIS";
    public static final String ARCADE = "ARCADE";

    public static final String ROOT =
            "/storage/emulated/0/SilentiumOS/Games";

    private final String id;
    private final String displayName;
    private final String subtitle;
    private final String folder;
    private final String coreFile;
    private final List<String> extensions;

    private SystemDefinition(
            String id,
            String displayName,
            String subtitle,
            String folder,
            String coreFile,
            String... extensions) {
        this.id = id;
        this.displayName = displayName;
        this.subtitle = subtitle;
        this.folder = folder;
        this.coreFile = coreFile;
        this.extensions = Collections.unmodifiableList(
                Arrays.asList(extensions));
    }

    public String getId() {
        return id;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getSubtitle() {
        return subtitle;
    }

    public String getFolder() {
        return folder;
    }

    public String getDirectoryPath() {
        return getDirectory(new File(ROOT)).getPath();
    }

    public File getDirectory(File libraryRoot) {
        if (libraryRoot == null) {
            throw new IllegalArgumentException("libraryRoot is required");
        }
        if (folder == null || folder.length() == 0) {
            return libraryRoot;
        }
        return new File(libraryRoot, folder);
    }

    public String getCoreFile() {
        return coreFile;
    }

    public boolean accepts(File file) {
        if (file == null || !file.isFile()) {
            return false;
        }

        String name = file.getName().toLowerCase(Locale.US);
        for (String extension : extensions) {
            if (name.endsWith(extension)) {
                return true;
            }
        }
        return false;
    }

    public static List<SystemDefinition> physicalSystems() {
        return Arrays.asList(
                get(NES),
                get(SNES),
                get(GB),
                get(GBA),
                get(GENESIS),
                get(ARCADE)
        );
    }

    public static List<SystemDefinition> menuSystems() {
        return Arrays.asList(
                get(BEST),
                get(NES),
                get(SNES),
                get(GB),
                get(GBA),
                get(GENESIS),
                get(ARCADE),
                get(ALL)
        );
    }

    public static SystemDefinition get(String id) {
        if (BEST.equals(id)) {
            return new SystemDefinition(
                    BEST,
                    "BEST ONES",
                    "Top picks for Elliot",
                    "",
                    "");
        }

        if (ALL.equals(id)) {
            return new SystemDefinition(
                    ALL,
                    "ALL GAMES",
                    "Everything installed",
                    "",
                    "");
        }

        if (SNES.equals(id)) {
            return new SystemDefinition(
                    SNES,
                    "SUPER NINTENDO",
                    "16-bit homebrew",
                    "SNES",
                    "snes9x2010_libretro_android.so",
                    ".sfc", ".smc", ".zip");
        }

        if (GB.equals(id)) {
            return new SystemDefinition(
                    GB,
                    "GAME BOY",
                    "GB and Game Boy Color",
                    "GameBoy",
                    "gambatte_libretro_android.so",
                    ".gb", ".gbc", ".zip");
        }

        if (GBA.equals(id)) {
            return new SystemDefinition(
                    GBA,
                    "GAME BOY ADVANCE",
                    "32-bit handheld homebrew",
                    "GBA",
                    "mgba_libretro_android.so",
                    ".gba", ".zip");
        }

        if (GENESIS.equals(id)) {
            return new SystemDefinition(
                    GENESIS,
                    "SEGA",
                    "Genesis, Mega Drive and Master System",
                    "Sega",
                    "genesis_plus_gx_libretro_android.so",
                    ".md", ".gen", ".bin", ".sms", ".zip");
        }

        if (ARCADE.equals(id)) {
            return new SystemDefinition(
                    ARCADE,
                    "SILENTIUM ARCADE",
                    "Instant-play retro games",
                    "Arcade",
                    "",
                    ".game", ".tic");
        }

        return new SystemDefinition(
                NES,
                "NINTENDO",
                "8-bit homebrew",
                "NES",
                "fceumm_libretro_android.so",
                ".nes", ".zip");
    }

    private SystemDefinition() {
        throw new UnsupportedOperationException();
    }
}
