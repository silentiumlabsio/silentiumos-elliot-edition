package com.silentiumlabs.silentiumos;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

public class GameListActivity extends Activity {
    public static final String EXTRA_SYSTEM = "system";
    private static final int STORAGE_PERMISSION_REQUEST = 4102;
    private static final String CORE_MARKER =
            "/storage/emulated/0/SilentiumOS/System/cores.ready";

    private static final String[] BEST_PATTERNS = {
            "nova",
            "apotris",
            "minicraft",
            "tuff",
            "tobu",
            "petris",
            "evoland",
            "geometrix",
            "ucity",
            "snake",
            "lazerpong",
            "sushi",
            "adjustris",
            "gothicvania",
            "tank battle",
            "battle 4tris",
            "space shooter",
            "breakout",
            "2048",
            "mr. boom",
            "craft"
    };

    private String systemId;
    private Set<String> readyCores = new HashSet<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        hideSystemUi();

        systemId = getIntent().getStringExtra(EXTRA_SYSTEM);
        if (systemId == null) {
            systemId = SystemDefinition.BEST;
        }

        if (needsStoragePermission()) {
            requestPermissions(
                    new String[]{
                            Manifest.permission.READ_EXTERNAL_STORAGE,
                            Manifest.permission.WRITE_EXTERNAL_STORAGE
                    },
                    STORAGE_PERMISSION_REQUEST);
        } else {
            refresh();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        hideSystemUi();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BUTTON_B
                || keyCode == KeyEvent.KEYCODE_BACK) {
            returnToSystems();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            String[] permissions,
            int[] grantResults) {
        super.onRequestPermissionsResult(
                requestCode, permissions, grantResults);

        if (requestCode == STORAGE_PERMISSION_REQUEST) {
            refresh();
        }
    }

    private boolean needsStoragePermission() {
        return Build.VERSION.SDK_INT >= Build.VERSION_CODES.M
                && checkSelfPermission(
                        Manifest.permission.READ_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED;
    }

    private void refresh() {
        readyCores = loadReadyCores();
        setContentView(buildScreen());
    }

    private View buildScreen() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(44), dp(22), dp(44), dp(18));
        root.setBackgroundResource(R.drawable.dashboard_background);

        TextView title = new TextView(this);
        title.setText(getScreenTitle());
        title.setTextColor(Color.WHITE);
        title.setTextSize(30);
        title.setLetterSpacing(0.07f);
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText(
                "CHOOSE A GAME  •  VIEW + MENU EXITS  •  HOME RETURNS HERE");
        subtitle.setTextColor(Color.rgb(220, 54, 54));
        subtitle.setTextSize(13);
        subtitle.setLetterSpacing(0.08f);
        subtitle.setPadding(0, dp(5), 0, dp(14));
        root.addView(subtitle);

        List<GameEntry> games = scanGames();

        if (games.isEmpty()) {
            root.addView(buildEmptyState(), new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    0,
                    1f));
            return root;
        }

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);

        LinearLayout gameContainer = new LinearLayout(this);
        gameContainer.setOrientation(LinearLayout.VERTICAL);
        gameContainer.setPadding(0, dp(3), 0, dp(8));

        Button first = null;
        for (GameEntry game : games) {
            Button button = makeGameButton(game);
            if (first == null) {
                first = button;
            }
            gameContainer.addView(button, gameButtonParams());
        }

        scroll.addView(gameContainer);
        root.addView(scroll, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1f));

        TextView footer = new TextView(this);
        footer.setText(games.size() + " VERIFIED GAME"
                + (games.size() == 1 ? "" : "S")
                + " READY FOR ELLIOT");
        footer.setTextColor(Color.rgb(125, 125, 125));
        footer.setTextSize(11);
        footer.setGravity(Gravity.CENTER);
        footer.setPadding(0, dp(8), 0, 0);
        root.addView(footer);

        if (first != null) {
            first.requestFocus();
        }

        return root;
    }

    private String getScreenTitle() {
        if (SystemDefinition.BEST.equals(systemId)) {
            return "BEST ONES FOR ELLIOT";
        }
        if (SystemDefinition.ALL.equals(systemId)) {
            return "ELLIOT'S COMPLETE LIBRARY";
        }
        return SystemDefinition.get(systemId).getDisplayName();
    }

    private View buildEmptyState() {
        LinearLayout empty = new LinearLayout(this);
        empty.setOrientation(LinearLayout.VERTICAL);
        empty.setGravity(Gravity.CENTER);
        empty.setPadding(dp(30), dp(20), dp(30), dp(20));

        TextView message = new TextView(this);
        message.setText("NO VERIFIED GAMES READY");
        message.setTextColor(Color.WHITE);
        message.setTextSize(25);
        message.setGravity(Gravity.CENTER);
        empty.addView(message);

        TextView detail = new TextView(this);
        detail.setText(getEmptyMessage());
        detail.setTextColor(Color.rgb(165, 165, 165));
        detail.setTextSize(15);
        detail.setGravity(Gravity.CENTER);
        detail.setPadding(0, dp(12), 0, dp(18));
        empty.addView(detail);

        Button back = makeActionButton("BACK TO SYSTEMS");
        back.setOnClickListener(v -> returnToSystems());
        empty.addView(back, new LinearLayout.LayoutParams(
                dp(360), dp(82)));
        back.requestFocus();

        return empty;
    }

    private String getEmptyMessage() {
        if (readyCores.isEmpty()) {
            return "The emulator engine has not finished setup.\n"
                    + "Run BUILD_AND_INSTALL_ELLIOT.cmd on the computer.";
        }

        if (SystemDefinition.BEST.equals(systemId)
                || SystemDefinition.ALL.equals(systemId)) {
            return "Run the validated legal-library installer on the computer.";
        }

        SystemDefinition system = SystemDefinition.get(systemId);
        if (!isCoreReady(system.getCoreFile())) {
            return "The emulator core for this system is not installed.";
        }

        return "No validated games were found in:\n"
                + system.getDirectoryPath();
    }

    private List<GameEntry> scanGames() {
        List<GameEntry> games = new ArrayList<>();

        if (SystemDefinition.BEST.equals(systemId)
                || SystemDefinition.ALL.equals(systemId)) {
            for (SystemDefinition system : SystemDefinition.physicalSystems()) {
                addGamesForSystem(games, system);
            }
            addSilentiumArcade(games);

            if (SystemDefinition.BEST.equals(systemId)) {
                List<GameEntry> best = new ArrayList<>();
                for (GameEntry game : games) {
                    if (isBest(game)) {
                        best.add(game);
                    }
                }
                games = best;
            }
        } else {
            SystemDefinition selected = SystemDefinition.get(systemId);
            addGamesForSystem(games, selected);
            if (SystemDefinition.ARCADE.equals(systemId)) {
                addSilentiumArcade(games);
            }
        }

        Collections.sort(games, new Comparator<GameEntry>() {
            @Override
            public int compare(GameEntry left, GameEntry right) {
                if (SystemDefinition.ALL.equals(systemId)) {
                    int systemCompare = left.system.getDisplayName()
                            .compareToIgnoreCase(
                                    right.system.getDisplayName());
                    if (systemCompare != 0) {
                        return systemCompare;
                    }
                }
                return left.displayName.compareToIgnoreCase(
                        right.displayName);
            }
        });

        return games;
    }

    private void addSilentiumArcade(List<GameEntry> games) {
        SystemDefinition arcade =
                SystemDefinition.get(SystemDefinition.ARCADE);

        addContentlessIfReady(
                games,
                arcade,
                "2048 — SILENTIUM ARCADE",
                "2048_libretro_android.so");

        addContentlessIfReady(
                games,
                arcade,
                "MR. BOOM — SILENTIUM ARCADE",
                "mrboom_libretro_android.so");

        addContentlessIfReady(
                games,
                arcade,
                "CRAFT BLOCK WORLD — SILENTIUM ARCADE",
                "craft_libretro_android.so");
    }

    private void addContentlessIfReady(
            List<GameEntry> games,
            SystemDefinition system,
            String name,
            String coreFile) {
        if (isCoreReady(coreFile)) {
            games.add(GameEntry.noContent(system, name, coreFile));
        }
    }

    private boolean isBest(GameEntry game) {
        String name = game.displayName.toLowerCase(Locale.US);
        for (String pattern : BEST_PATTERNS) {
            if (name.contains(pattern)) {
                return true;
            }
        }
        return false;
    }

    private void addGamesForSystem(
            List<GameEntry> games,
            SystemDefinition system) {
        if (SystemDefinition.ARCADE.equals(system.getId())) {
            return;
        }

        if (!isCoreReady(system.getCoreFile())) {
            return;
        }

        File folder = new File(system.getDirectoryPath());
        if (!folder.exists()) {
            folder.mkdirs();
            return;
        }

        addGamesFromFolder(games, system, folder);
    }

    private void addGamesFromFolder(
            List<GameEntry> games,
            SystemDefinition system,
            File folder) {
        File[] files = folder.listFiles();
        if (files == null) {
            return;
        }

        for (File file : files) {
            if (file.isDirectory()) {
                addGamesFromFolder(games, system, file);
            } else if (system.accepts(file)) {
                games.add(new GameEntry(
                        system,
                        file,
                        cleanName(file.getName())));
            }
        }
    }

    private Set<String> loadReadyCores() {
        Set<String> result = new HashSet<>();
        File marker = new File(CORE_MARKER);
        if (!marker.exists()) {
            return result;
        }

        try (BufferedReader reader =
                     new BufferedReader(new FileReader(marker))) {
            String line;
            while ((line = reader.readLine()) != null) {
                String core = line.trim();
                if (core.length() > 0) {
                    result.add(core);
                }
            }
        } catch (Exception ignored) {
            result.clear();
        }
        return result;
    }

    private boolean isCoreReady(String coreFile) {
        return coreFile != null
                && coreFile.length() > 0
                && readyCores.contains(coreFile);
    }

    private String cleanName(String filename) {
        int dot = filename.lastIndexOf('.');
        String result = dot > 0
                ? filename.substring(0, dot)
                : filename;
        return result.replace('_', ' ')
                .replace('-', ' ')
                .replaceAll("\\s+", " ")
                .trim();
    }

    private Button makeGameButton(GameEntry game) {
        String label = game.displayName;
        if (SystemDefinition.ALL.equals(systemId)
                || SystemDefinition.BEST.equals(systemId)) {
            label += "\n" + game.system.getDisplayName();
        }

        Button button = makeActionButton(label);
        button.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        button.setPadding(dp(24), 0, dp(20), 0);
        button.setOnClickListener(v -> launchGame(game));
        return button;
    }

    private Button makeActionButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Color.WHITE);
        button.setTextSize(18);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setFocusable(true);
        button.setFocusableInTouchMode(true);
        button.setBackgroundResource(R.drawable.tile_selector);
        button.setOnFocusChangeListener((v, hasFocus) -> v.animate()
                .scaleX(hasFocus ? 1.02f : 1f)
                .scaleY(hasFocus ? 1.02f : 1f)
                .setDuration(100)
                .start());
        return button;
    }

    private LinearLayout.LayoutParams gameButtonParams() {
        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        dp(78));
        params.setMargins(0, dp(5), 0, dp(5));
        return params;
    }

    private void launchGame(GameEntry game) {
        String coreFile = game.coreFile != null
                ? game.coreFile
                : game.system.getCoreFile();

        if (!isCoreReady(coreFile)) {
            Toast.makeText(
                    this,
                    "That emulator core is not ready.",
                    Toast.LENGTH_LONG).show();
            return;
        }

        if (game.file != null && !game.file.exists()) {
            Toast.makeText(
                    this,
                    "That game file is missing.",
                    Toast.LENGTH_LONG).show();
            return;
        }

        try {
            // Fire OS can briefly surface Amazon Home while crossing from
            // SilentiumOS into RetroArch. Suspend both takeover layers long
            // enough for the game activity and core to finish loading.
            ConsoleGuardService.allowExternalApps(this, 20000L);

            Intent intent = new Intent();
            intent.setClassName(
                    "com.retroarch.ra32",
                    "com.retroarch.browser.retroactivity."
                            + "RetroActivityFuture");

            if (game.file != null) {
                intent.putExtra("ROM", game.file.getAbsolutePath());
            }

            intent.putExtra(
                    "LIBRETRO",
                    "/data/user/0/com.retroarch.ra32/cores/" + coreFile);
            intent.putExtra(
                    "CONFIGFILE",
                    "/storage/emulated/0/Android/data/"
                            + "com.retroarch.ra32/files/retroarch.cfg");
            intent.putExtra(
                    "DATADIR",
                    "/data/user/0/com.retroarch.ra32");
            intent.putExtra(
                    "SDCARD",
                    "/storage/emulated/0");

            try {
                String apkPath = getPackageManager()
                        .getApplicationInfo("com.retroarch.ra32", 0)
                        .sourceDir;
                intent.putExtra("APK", apkPath);
            } catch (Exception ignored) {
                // The full ROM and core paths are still provided.
            }

            intent.putExtra(
                    "EXTERNAL",
                    "/storage/emulated/0/Android/data/"
                            + "com.retroarch.ra32/files");
            intent.addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK
                            | Intent.FLAG_ACTIVITY_CLEAR_TASK
                            | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(intent);
        } catch (Exception error) {
            Toast.makeText(
                    this,
                    "The game could not start. Use Parent Tools "
                            + "for diagnostics.",
                    Toast.LENGTH_LONG).show();
        }
    }

    private void returnToSystems() {
        Intent intent = new Intent(this, GameLibraryActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(intent);
        finish();
    }

    private void hideSystemUi() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    }

    private int dp(int value) {
        return Math.round(value
                * getResources().getDisplayMetrics().density);
    }

    private static final class GameEntry {
        final SystemDefinition system;
        final File file;
        final String displayName;
        final String coreFile;

        GameEntry(
                SystemDefinition system,
                File file,
                String displayName) {
            this(system, file, displayName, null);
        }

        GameEntry(
                SystemDefinition system,
                File file,
                String displayName,
                String coreFile) {
            this.system = system;
            this.file = file;
            this.displayName = displayName;
            this.coreFile = coreFile;
        }

        static GameEntry noContent(
                SystemDefinition system,
                String displayName,
                String coreFile) {
            return new GameEntry(
                    system,
                    null,
                    displayName,
                    coreFile);
        }
    }
}
