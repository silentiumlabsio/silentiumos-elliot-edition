package com.silentiumlabs.silentiumos;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;

/** Dependency-free contract tests for the pure Java library catalog. */
public final class GameCatalogContractTest {
    public static void main(String[] args) throws Exception {
        GameCatalogContractTest tests = new GameCatalogContractTest();
        tests.findsSupportedGamesAndCleansNames();
        tests.filtersTheBestList();
        tests.rejectsMalformedCoreMarkerEntries();
        tests.stopsAtTheDirectoryDepthLimit();
        tests.normalizesUnknownSystemIds();
        System.out.println("GameCatalog contract tests passed.");
    }

    private void findsSupportedGamesAndCleansNames() throws Exception {
        withRepository((library, marker) -> {
            writeMarker(marker, "fceumm_libretro_android.so");
            Path nes = Files.createDirectories(library.resolve("NES"));
            Files.write(nes.resolve("Nova_The-Game.nes"), new byte[0]);
            Files.write(nes.resolve("readme.txt"), new byte[0]);

            GameCatalog.CatalogSnapshot snapshot =
                    new GameCatalog(library.toFile(), marker.toFile())
                            .load(SystemDefinition.NES);

            assertEquals(1, snapshot.getGames().size(), "supported game count");
            assertEquals(
                    "Nova The Game",
                    snapshot.getGames().get(0).getDisplayName(),
                    "clean display name");
            assertFalse(snapshot.isTruncated(), "ordinary scan should complete");
        });
    }

    private void filtersTheBestList() throws Exception {
        withRepository((library, marker) -> {
            writeMarker(marker, "fceumm_libretro_android.so");
            Path nes = Files.createDirectories(library.resolve("NES"));
            Files.write(nes.resolve("Nova.nes"), new byte[0]);
            Files.write(nes.resolve("Ordinary_Game.nes"), new byte[0]);

            List<GameEntry> games =
                    new GameCatalog(library.toFile(), marker.toFile())
                            .load(SystemDefinition.BEST)
                            .getGames();

            assertEquals(1, games.size(), "best-list count");
            assertEquals("Nova", games.get(0).getDisplayName(), "best-list name");
        });
    }

    private void rejectsMalformedCoreMarkerEntries() throws Exception {
        withRepository((library, marker) -> {
            writeMarker(marker, "../fceumm_libretro_android.so");
            Path nes = Files.createDirectories(library.resolve("NES"));
            Files.write(nes.resolve("Nova.nes"), new byte[0]);

            GameCatalog.CatalogSnapshot snapshot =
                    new GameCatalog(library.toFile(), marker.toFile())
                            .load(SystemDefinition.NES);

            assertFalse(snapshot.hasReadyCores(), "malformed core marker");
            assertEquals(0, snapshot.getGames().size(), "unready library count");
        });
    }

    private void stopsAtTheDirectoryDepthLimit() throws Exception {
        withRepository((library, marker) -> {
            writeMarker(marker, "fceumm_libretro_android.so");
            Path nested = Files.createDirectories(library.resolve("NES"));
            for (int index = 0;
                    index <= GameCatalog.MAX_DIRECTORY_DEPTH;
                    index++) {
                nested = Files.createDirectories(
                        nested.resolve("level-" + index));
            }
            Files.write(nested.resolve("Nova.nes"), new byte[0]);

            GameCatalog.CatalogSnapshot snapshot =
                    new GameCatalog(library.toFile(), marker.toFile())
                            .load(SystemDefinition.NES);

            assertTrue(snapshot.isTruncated(), "depth-limited scan flag");
            assertEquals(0, snapshot.getGames().size(), "deep game count");
        });
    }

    private void normalizesUnknownSystemIds() throws Exception {
        withRepository((library, marker) -> {
            GameCatalog.CatalogSnapshot snapshot =
                    new GameCatalog(library.toFile(), marker.toFile())
                            .load("unknown-system");
            assertEquals(
                    SystemDefinition.BEST,
                    snapshot.getSystemId(),
                    "normalized system id");
        });
    }

    private void withRepository(RepositoryTest test) throws Exception {
        Path workspace = Files.createTempDirectory("silentium-catalog-test-");
        try {
            Path library = Files.createDirectories(workspace.resolve("library"));
            Path marker = workspace.resolve("cores.ready");
            test.run(library, marker);
        } finally {
            deleteRecursively(workspace);
        }
    }

    private void writeMarker(Path marker, String... lines) throws IOException {
        Files.write(marker, List.of(lines), StandardCharsets.UTF_8);
    }

    private void deleteRecursively(Path root) throws IOException {
        if (!Files.exists(root)) {
            return;
        }
        try (java.util.stream.Stream<Path> paths = Files.walk(root)) {
            paths.sorted(Comparator.reverseOrder()).forEach(path -> {
                try {
                    Files.deleteIfExists(path);
                } catch (IOException error) {
                    throw new RuntimeException(error);
                }
            });
        }
    }

    private static void assertEquals(
            Object expected,
            Object actual,
            String message) {
        if (!expected.equals(actual)) {
            throw new AssertionError(
                    message + ": expected " + expected + ", got " + actual);
        }
    }

    private static void assertTrue(boolean value, String message) {
        if (!value) {
            throw new AssertionError(message + ": expected true");
        }
    }

    private static void assertFalse(boolean value, String message) {
        if (value) {
            throw new AssertionError(message + ": expected false");
        }
    }

    private interface RepositoryTest {
        void run(Path library, Path marker) throws Exception;
    }

    private GameCatalogContractTest() {
    }
}
