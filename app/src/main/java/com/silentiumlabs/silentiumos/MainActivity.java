package com.silentiumlabs.silentiumos;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        startConsoleGuard();
        hideSystemUi();
        setContentView(buildDashboard());
    }

    @Override
    protected void onResume() {
        super.onResume();
        startConsoleGuard();
        hideSystemUi();
    }

    @Override
    public void onBackPressed() {
        // Main dashboard is the end of the child-facing navigation stack.
        // Back must never expose the underlying Amazon launcher.
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK
                || keyCode == KeyEvent.KEYCODE_BUTTON_B) {
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    private void startConsoleGuard() {
        Intent guard = new Intent(this, ConsoleGuardService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(guard);
        } else {
            startService(guard);
        }
    }

    private View buildDashboard() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(44), dp(18), dp(44), dp(15));
        root.setBackgroundResource(R.drawable.dashboard_background);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.silentium_icon);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        header.addView(logo, new LinearLayout.LayoutParams(dp(132), dp(132)));

        LinearLayout titleGroup = new LinearLayout(this);
        titleGroup.setOrientation(LinearLayout.VERTICAL);
        titleGroup.setPadding(dp(24), 0, 0, 0);

        TextView title = new TextView(this);
        title.setText("SILENTIUMOS");
        title.setTextColor(Color.WHITE);
        title.setTextSize(36);
        title.setLetterSpacing(0.08f);
        titleGroup.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("ELLIOT EDITION  /  PLUG-AND-PLAY CONSOLE");
        subtitle.setTextColor(Color.rgb(220, 54, 54));
        subtitle.setTextSize(17);
        subtitle.setLetterSpacing(0.12f);
        titleGroup.addView(subtitle);

        TextView status = new TextView(this);
        status.setText(
                "WELCOME, ELLIOT  •  CHOOSE A GAME  •  HOME RETURNS HERE");
        status.setTextColor(Color.rgb(170, 170, 170));
        status.setTextSize(12);
        status.setPadding(0, dp(8), 0, 0);
        titleGroup.addView(status);

        header.addView(titleGroup, new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        root.addView(header, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(145)));

        TextView section = new TextView(this);
        section.setText("ELLIOT'S GAME CENTER");
        section.setTextColor(Color.rgb(210, 210, 210));
        section.setTextSize(15);
        section.setLetterSpacing(0.12f);
        section.setPadding(dp(5), dp(2), 0, dp(7));
        root.addView(section, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));

        LinearLayout firstRow = makeRow();

        Button play = makeTile("PLAY GAMES\nBrowse every system");
        play.setOnClickListener(v ->
                startActivity(new Intent(this, GameLibraryActivity.class)));
        firstRow.addView(play, tileParams());

        Button best = makeTile("BEST ONES\nElliot's top picks");
        best.setOnClickListener(v -> openGameList(SystemDefinition.BEST));
        firstRow.addView(best, tileParams());

        Button all = makeTile("ALL GAMES\nComplete legal library");
        all.setOnClickListener(v -> openGameList(SystemDefinition.ALL));
        firstRow.addView(all, tileParams());

        root.addView(firstRow, rowParams());

        LinearLayout secondRow = makeRow();

        Button controllers = makeTile("CONTROLLERS\nBluetooth pairing");
        controllers.setOnClickListener(v -> {
            ConsoleGuardService.allowExternalApps(this, 120000L);
            openSettings(Settings.ACTION_BLUETOOTH_SETTINGS);
        });
        secondRow.addView(controllers, tileParams());

        Button network = makeTile("NETWORK\nWi-Fi settings");
        network.setOnClickListener(v -> {
            ConsoleGuardService.allowExternalApps(this, 120000L);
            openSettings(Settings.ACTION_WIFI_SETTINGS);
        });
        secondRow.addView(network, tileParams());

        Button parent = makeTile("PARENT TOOLS\nPIN protected setup");
        parent.setOnClickListener(v ->
                startActivity(new Intent(this, ParentPinActivity.class)));
        secondRow.addView(parent, tileParams());

        root.addView(secondRow, rowParams());

        TextView footer = new TextView(this);
        footer.setText(
                "VIEW + MENU EXITS A GAME  •  HOME RETURNS TO SILENTIUMOS  •  "
                        + "BUILT BY SILENTIUM LABS");
        footer.setTextColor(Color.rgb(125, 125, 125));
        footer.setTextSize(10);
        footer.setGravity(Gravity.CENTER);
        footer.setPadding(0, dp(10), 0, 0);
        root.addView(footer, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));

        play.requestFocus();
        return root;
    }

    private void openGameList(String system) {
        Intent intent = new Intent(this, GameListActivity.class);
        intent.putExtra(GameListActivity.EXTRA_SYSTEM, system);
        startActivity(intent);
    }

    private LinearLayout makeRow() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER);
        return row;
    }

    private Button makeTile(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Color.WHITE);
        button.setTextSize(18);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setFocusable(true);
        button.setFocusableInTouchMode(true);
        button.setBackgroundResource(R.drawable.tile_selector);
        button.setPadding(dp(16), dp(10), dp(16), dp(10));
        button.setOnFocusChangeListener((v, hasFocus) -> v.animate()
                .scaleX(hasFocus ? 1.045f : 1f)
                .scaleY(hasFocus ? 1.045f : 1f)
                .setDuration(120)
                .start());
        return button;
    }

    private LinearLayout.LayoutParams tileParams() {
        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(0, dp(106), 1f);
        params.setMargins(dp(8), dp(7), dp(8), dp(7));
        return params;
    }

    private LinearLayout.LayoutParams rowParams() {
        return new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
    }

    private void openSettings(String action) {
        try {
            Intent intent = new Intent(action);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
        } catch (Exception error) {
            Toast.makeText(
                    this,
                    "That settings screen could not be opened.",
                    Toast.LENGTH_LONG).show();
        }
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
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
