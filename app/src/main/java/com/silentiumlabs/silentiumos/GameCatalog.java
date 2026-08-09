package com.silentiumlabs.silentiumos;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Reads the local legal-game library through a bounded, read-only scan.
 * Device paths are injected so the catalog can be tested without Android.
 */
public final class GameCatalog {
    static final int MAX_DIRECTORY_DEPTH = 8;
    static final int MAX_DIRECTORIES = 512;
    static final int MAX_GAMES = 5000;

    private static final int MAX_CORE_MARKER_BYTES = 64 * 1024;
    private static final int MAX_CORE_MARKER_LINES = 1024;
    private static final Pattern CORE_NAME =
            Pattern.compile("[A-Za-z0-9._-]{1,128}");

    private static final String DEFAULT_CORE_MARKER =
            "/storage/emulated/0/SilentiumOS/System/cores.ready";

    private static final List<String> BEST_PATTERNS =
            Collections.unmodifiableList(Arrays.asList(
                    "nova", "apotris", "minicraft", "tuff", "tobu",
                    "petris", "evoland", "geometrix", "ucity", "snake",
                    "lazerpong", "sushi", "adjustris", "gothicvania",
                    "tank battle", "battle 4tris", "space shooter",
                    "breakout", "2048", "mr. boom", "craft"));

    private final File libraryRoot;
    private final File coreMarker;

    public GameCatalog(File libraryRoot, File coreMarker) {
        if (libraryRoot == null || coreMarker == null) {
            throw new IllegalArgumentException("catalog paths are required");
        }
        this.libraryRoot = libraryRoot;
        this.coreMarker = coreMarker;
    }

    public static GameCatalog forDevice() {
        return new GameCatalog(
                new File(SystemDefinition.ROOT),
                new File(DEFAULT_CORE_MARKER));
    }

    public CatalogSnapshot load(String requestedSystemId) {
        String systemId = normalizeSystemId(requestedSystemId);
        Set<String> readyCores = loadReadyCores();
        ScanState state = new ScanState();

        if (SystemDefinition.BEST.equals(systemId)
                || SystemDefinition.ALL.equals(systemId)) {
            for (SystemDefinition system : SystemDefinition.physicalSystems()) {
                addGamesForSystem(state, system, readyCores);
                if (state.truncated) {
                    break;
                }
            }
            addSilentiumArcade(state, readyCores);
        } else {
            SystemDefinition selected = SystemDefinition.get(systemId);
            addGamesForSystem(state, selected, readyCores);
            if (SystemDefinition.ARCADE.equals(systemId)) {
                addSilentiumArcade(state, readyCores);
            }
        }

        List<GameEntry> games = state.games;
        if (SystemDefinition.BEST.equals(systemId)) {
            List<GameEntry> favorites = new ArrayList<>();
            for (GameEntry game : games) {
                if (isBest(game)) {
                    favorites.add(game);
                }
            }
            games = favorites;
        }

        sortGames(games, SystemDefinition.ALL.equals(systemId));
        return new CatalogSnapshot(
                systemId,
                games,
                readyCores,
                state.truncated);
    }

    public static String cleanDisplayName(String filename) {
        if (filename == null) {
            return "";
        }
        int dot = filename.lastIndexOf('.');
        String result = dot > 0 ? filename.substring(0, dot) : filename;
        return result.replace('_', ' ')
                .replace('-', ' ')
                .replaceAll("\\s+", " ")
                .trim();
    }

    private String normalizeSystemId(String requestedSystemId) {
        if (requestedSystemId != null) {
            for (SystemDefinition system : SystemDefinition.menuSystems()) {
                if (system.getId().equals(requestedSystemId)) {
                    return requestedSystemId;
                }
            }
        }
        return SystemDefinition.BEST;
    }

    private void addGamesForSystem(
            ScanState state,
            SystemDefinition system,
            Set<String> readyCores) {
        if (state.truncated || SystemDefinition.ARCADE.equals(system.getId())) {
            return;
        }
        if (!readyCores.contains(system.getCoreFile())) {
            return;
        }

        File folder = system.getDirectory(libraryRoot);
        if (!folder.isDirectory()) {
            return;
        }
        scanFolder(state, system, folder);
    }

    private void scanFolder(
            ScanState state,
            SystemDefinition system,
            File folder) {
        final File canonicalRoot;
        try {
            canonicalRoot = folder.getCanonicalFile();
        } catch (IOException error) {
            return;
        }

        ArrayDeque<DirectoryNode> pending = new ArrayDeque<>();
        Set<String> visited = new HashSet<>();
        pending.add(new DirectoryNode(canonicalRoot, 0));

        while (!pending.isEmpty() && !state.truncated) {
            if (state.directoriesVisited >= MAX_DIRECTORIES) {
                state.truncated = true;
                break;
            }

            DirectoryNode node = pending.removeFirst();
            final File canonicalDirectory;
            try {
                canonicalDirectory = node.directory.getCanonicalFile();
            } catch (IOException error) {
                continue;
            }

            if (!isInside(canonicalRoot, canonicalDirectory)
                    || !visited.add(canonicalDirectory.getPath())) {
                continue;
            }

            state.directoriesVisited++;
            File[] children = canonicalDirectory.listFiles();
            if (children == null) {
                continue;
            }
            Arrays.sort(children, Comparator.comparing(
                    File::getName,
                    String.CASE_INSENSITIVE_ORDER));

            for (File child : children) {
                if (state.games.size() >= MAX_GAMES) {
                    state.truncated = true;
                    break;
                }
                if (Files.isSymbolicLink(child.toPath())) {
                    continue;
                }

                final File canonicalChild;
                try {
                    canonicalChild = child.getCanonicalFile();
                } catch (IOException error) {
                    continue;
                }
                if (!isInside(canonicalRoot, canonicalChild)) {
                    continue;
                }

                if (canonicalChild.isDirectory()) {
                    if (node.depth < MAX_DIRECTORY_DEPTH) {
                        pending.addLast(new DirectoryNode(
                                canonicalChild, node.depth + 1));
                    } else {
                        state.truncated = true;
                    }
                } else if (system.accepts(canonicalChild)) {
                    state.games.add(GameEntry.forFile(
                            system,
                            canonicalChild,
                            cleanDisplayName(canonicalChild.getName())));
                }
            }
        }
    }

    private void addSilentiumArcade(
            ScanState state,
            Set<String> readyCores) {
        if (state.games.size() >= MAX_GAMES) {
            state.truncated = true;
            return;
        }

        SystemDefinition arcade = SystemDefinition.get(SystemDefinition.ARCADE);
        addContentlessIfReady(
                state, readyCores, arcade,
                "2048 — SILENTIUM ARCADE", "2048_libretro_android.so");
        addContentlessIfReady(
                state, readyCores, arcade,
                "MR. BOOM — SILENTIUM ARCADE", "mrboom_libretro_android.so");
        addContentlessIfReady(
                state, readyCores, arcade,
                "CRAFT BLOCK WORLD — SILENTIUM ARCADE", "craft_libretro_android.so");
    }

    private void addContentlessIfReady(
            ScanState state,
            Set<String> readyCores,
            SystemDefinition system,
            String name,
            String coreFile) {
        if (state.games.size() >= MAX_GAMES) {
            state.truncated = true;
        } else if (readyCores.contains(coreFile)) {
            state.games.add(GameEntry.withoutContent(
                    system, name, coreFile));
        }
    }

    private Set<String> loadReadyCores() {
        Set<String> result = new HashSet<>();
        if (!coreMarker.isFile()
                || coreMarker.length() > MAX_CORE_MARKER_BYTES) {
            return result;
        }

        try (BufferedReader reader =
                     new BufferedReader(new FileReader(coreMarker))) {
            String line;
            int lineCount = 0;
            while ((line = reader.readLine()) != null
                    && lineCount < MAX_CORE_MARKER_LINES) {
                lineCount++;
                String core = line.trim();
                if (CORE_NAME.matcher(core).matches()) {
                    result.add(core);
                }
            }
        } catch (IOException error) {
            result.clear();
        }
        return result;
    }

    private static boolean isInside(File root, File candidate) {
        String rootPath = root.getPath();
        String candidatePath = candidate.getPath();
        return candidatePath.equals(rootPath)
                || candidatePath.startsWith(rootPath + File.separator);
    }

    private static boolean isBest(GameEntry game) {
        String name = game.getDisplayName().toLowerCase(Locale.US);
        for (String pattern : BEST_PATTERNS) {
            if (name.contains(pattern)) {
                return true;
            }
        }
        return false;
    }

    private static void sortGames(
            List<GameEntry> games,
            boolean groupBySystem) {
        Collections.sort(games, (left, right) -> {
            if (groupBySystem) {
                int systemCompare = left.getSystem().getDisplayName()
                        .compareToIgnoreCase(
                                right.getSystem().getDisplayName());
                if (systemCompare != 0) {
                    return systemCompare;
                }
            }
            return left.getDisplayName().compareToIgnoreCase(
                    right.getDisplayName());
        });
    }

    public static final class CatalogSnapshot {
        private final String systemId;
        private final List<GameEntry> games;
        private final Set<String> readyCores;
        private final boolean truncated;

        private CatalogSnapshot(
                String systemId,
                List<GameEntry> games,
                Set<String> readyCores,
                boolean truncated) {
            this.systemId = systemId;
            this.games = Collections.unmodifiableList(
                    new ArrayList<>(games));
            this.readyCores = Collections.unmodifiableSet(
                    new HashSet<>(readyCores));
            this.truncated = truncated;
        }

        public String getSystemId() {
            return systemId;
        }

        public List<GameEntry> getGames() {
            return games;
        }

        public boolean hasReadyCores() {
            return !readyCores.isEmpty();
        }

        public boolean isCoreReady(String coreFile) {
            return coreFile != null && readyCores.contains(coreFile);
        }

        public boolean isTruncated() {
            return truncated;
        }
    }

    private static final class DirectoryNode {
        final File directory;
        final int depth;

        DirectoryNode(File directory, int depth) {
            this.directory = directory;
            this.depth = depth;
        }
    }

    private static final class ScanState {
        final List<GameEntry> games = new ArrayList<>();
        int directoriesVisited;
        boolean truncated;
    }
}
