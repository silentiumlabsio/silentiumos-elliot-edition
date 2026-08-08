package com.silentiumlabs.silentiumos;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.File;
import java.util.List;

public class GameLibraryActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        hideSystemUi();
        createFolders();
        setContentView(buildScreen());
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
            returnToDashboard();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    private View buildScreen() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(42), dp(18), dp(42), dp(18));
        root.setBackgroundResource(R.drawable.dashboard_background);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.silentium_icon);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        header.addView(logo, new LinearLayout.LayoutParams(dp(95), dp(95)));

        LinearLayout titles = new LinearLayout(this);
        titles.setOrientation(LinearLayout.VERTICAL);
        titles.setPadding(dp(18), 0, 0, 0);

        TextView title = new TextView(this);
        title.setText("ELLIOT'S GAMES");
        title.setTextColor(Color.WHITE);
        title.setTextSize(31);
        title.setLetterSpacing(0.08f);
        titles.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("FULL LEGAL RETRO LIBRARY");
        subtitle.setTextColor(Color.rgb(220, 54, 54));
        subtitle.setTextSize(15);
        subtitle.setLetterSpacing(0.14f);
        titles.addView(subtitle);

        header.addView(titles, new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        TextView backHint = new TextView(this);
        backHint.setText("B / BACK  •  RETURN");
        backHint.setTextColor(Color.rgb(145, 145, 145));
        backHint.setTextSize(11);
        header.addView(backHint);

        root.addView(header, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(105)));

        List<SystemDefinition> systems = SystemDefinition.menuSystems();

        LinearLayout row1 = makeRow();
        for (int index = 0; index < 4; index++) {
            row1.addView(makeSystemTile(systems.get(index)), tileParams());
        }
        root.addView(row1, rowParams());

        LinearLayout row2 = makeRow();
        for (int index = 4; index < 8; index++) {
            row2.addView(makeSystemTile(systems.get(index)), tileParams());
        }
        root.addView(row2, rowParams());

        TextView footer = new TextView(this);
        footer.setText(
                "BEST ONES • SYSTEMS • ALL GAMES  |  "
                        + "VIEW + MENU RETURNS FROM RETROARCH");
        footer.setTextColor(Color.rgb(125, 125, 125));
        footer.setTextSize(11);
        footer.setGravity(Gravity.CENTER);
        footer.setPadding(0, dp(14), 0, 0);
        root.addView(footer, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));

        row1.getChildAt(0).requestFocus();
        return root;
    }

    private Button makeSystemTile(SystemDefinition system) {
        Button button = makeTile(
                system.getDisplayName() + "\n" + system.getSubtitle());
        button.setOnClickListener(v -> openSystem(system.getId()));
        return button;
    }

    private void openSystem(String systemId) {
        Intent intent = new Intent(this, GameListActivity.class);
        intent.putExtra(GameListActivity.EXTRA_SYSTEM, systemId);
        startActivity(intent);
    }

    private void createFolders() {
        File root = new File(SystemDefinition.ROOT);
        if (!root.exists()) {
            root.mkdirs();
        }

        for (SystemDefinition system : SystemDefinition.physicalSystems()) {
            File folder = new File(system.getDirectoryPath());
            if (!folder.exists()) {
                folder.mkdirs();
            }
        }
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
        button.setTextSize(16);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setFocusable(true);
        button.setFocusableInTouchMode(true);
        button.setBackgroundResource(R.drawable.tile_selector);
        button.setPadding(dp(10), dp(8), dp(10), dp(8));
        button.setOnFocusChangeListener((v, hasFocus) -> v.animate()
                .scaleX(hasFocus ? 1.05f : 1f)
                .scaleY(hasFocus ? 1.05f : 1f)
                .setDuration(120)
                .start());
        return button;
    }

    private LinearLayout.LayoutParams tileParams() {
        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(0, dp(120), 1f);
        params.setMargins(dp(7), dp(8), dp(7), dp(8));
        return params;
    }

    private LinearLayout.LayoutParams rowParams() {
        return new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
    }

    private void returnToDashboard() {
        Intent intent = new Intent(this, MainActivity.class);
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
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
