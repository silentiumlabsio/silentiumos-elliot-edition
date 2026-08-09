package com.silentiumlabs.silentiumos;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class ParentToolsActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        ConsoleGuardService.allowExternalApps(this, 300000L);
        hideSystemUi();
        setContentView(buildScreen());
    }

    @Override
    protected void onResume() {
        super.onResume();
        ConsoleGuardService.allowExternalApps(this, 300000L);
        hideSystemUi();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK
                || keyCode == KeyEvent.KEYCODE_BUTTON_B) {
            returnToDashboard();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    private View buildScreen() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(55), dp(30), dp(55), dp(30));
        root.setBackgroundResource(R.drawable.dashboard_background);

        TextView title = new TextView(this);
        title.setText("SILENTIUMOS PARENT TOOLS");
        title.setTextColor(Color.WHITE);
        title.setTextSize(30);
        title.setLetterSpacing(0.08f);
        title.setGravity(Gravity.CENTER);
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("SETUP ACCESS CLOSES AUTOMATICALLY AFTER FIVE MINUTES");
        subtitle.setTextColor(Color.rgb(220, 54, 54));
        subtitle.setTextSize(13);
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, dp(8), 0, dp(20));
        root.addView(subtitle);

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER);

        ConsoleTileButton retro = makeTile(
                "RetroArch Tools", "Cores and diagnostics");
        retro.setOnClickListener(v ->
                startActivity(new Intent(this, RetroToolsActivity.class)));
        row.addView(retro, tileParams());

        ConsoleTileButton controllers = makeTile(
                "Controllers", "Bluetooth settings");
        controllers.setOnClickListener(v ->
                openSettings(Settings.ACTION_BLUETOOTH_SETTINGS));
        row.addView(controllers, tileParams());

        ConsoleTileButton network = makeTile("Network", "Wi-Fi settings");
        network.setOnClickListener(v ->
                openSettings(Settings.ACTION_WIFI_SETTINGS));
        row.addView(network, tileParams());

        ConsoleTileButton about = makeTile(
                "About & Privacy", "Public build information");
        about.setOnClickListener(v -> startActivity(
                new Intent(this, PublicSystemInfoActivity.class)));
        row.addView(about, tileParams());

        root.addView(row);

        ConsoleTileButton lock = makeTile(
                "Lock", "Return to Elliot's dashboard");
        lock.setOnClickListener(v -> {
            ConsoleGuardService.lockNow(this);
            returnToDashboard();
        });
        LinearLayout.LayoutParams lockParams =
                new LinearLayout.LayoutParams(dp(650), dp(82));
        lockParams.setMargins(0, dp(22), 0, 0);
        root.addView(lock, lockParams);

        retro.requestFocus();
        return root;
    }

    private ConsoleTileButton makeTile(String title, String subtitle) {
        return new ConsoleTileButton(this, title, subtitle);
    }

    private LinearLayout.LayoutParams tileParams() {
        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(0, dp(118), 1f);
        params.setMargins(dp(8), dp(8), dp(8), dp(8));
        return params;
    }

    private void openSettings(String action) {
        ConsoleGuardService.allowExternalApps(this, 300000L);
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
