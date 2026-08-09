package com.silentiumlabs.silentiumos;

import java.io.File;

/** Immutable description of one launchable library item. */
public final class GameEntry {
    private final SystemDefinition system;
    private final File file;
    private final String displayName;
    private final String coreFile;

    private GameEntry(
            SystemDefinition system,
            File file,
            String displayName,
            String coreFile) {
        if (system == null) {
            throw new IllegalArgumentException("system is required");
        }
        if (displayName == null || displayName.trim().length() == 0) {
            throw new IllegalArgumentException("displayName is required");
        }
        this.system = system;
        this.file = file;
        this.displayName = displayName.trim();
        this.coreFile = coreFile;
    }

    public static GameEntry forFile(
            SystemDefinition system,
            File file,
            String displayName) {
        if (file == null) {
            throw new IllegalArgumentException("file is required");
        }
        return new GameEntry(system, file, displayName, null);
    }

    public static GameEntry withoutContent(
            SystemDefinition system,
            String displayName,
            String coreFile) {
        if (coreFile == null || coreFile.trim().length() == 0) {
            throw new IllegalArgumentException("coreFile is required");
        }
        return new GameEntry(system, null, displayName, coreFile.trim());
    }

    public SystemDefinition getSystem() {
        return system;
    }

    public File getFile() {
        return file;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getCoreFile() {
        return coreFile;
    }

    public String getResolvedCoreFile() {
        return coreFile != null ? coreFile : system.getCoreFile();
    }
}
