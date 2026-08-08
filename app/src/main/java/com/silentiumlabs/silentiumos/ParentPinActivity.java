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
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class ParentPinActivity extends Activity {
    private final StringBuilder entered = new StringBuilder();
    private TextView dots;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        hideSystemUi();
        setContentView(buildScreen());
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
        root.setPadding(dp(80), dp(25), dp(80), dp(25));
        root.setBackgroundResource(R.drawable.dashboard_background);

        TextView title = new TextView(this);
        title.setText("PARENT TOOLS");
        title.setTextColor(Color.WHITE);
        title.setTextSize(32);
        title.setLetterSpacing(0.10f);
        title.setGravity(Gravity.CENTER);
        root.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("ENTER THE FOUR-DIGIT PIN");
        subtitle.setTextColor(Color.rgb(220, 54, 54));
        subtitle.setTextSize(15);
        subtitle.setLetterSpacing(0.12f);
        subtitle.setGravity(Gravity.CENTER);
        subtitle.setPadding(0, dp(8), 0, dp(12));
        root.addView(subtitle);

        dots = new TextView(this);
        dots.setText("○  ○  ○  ○");
        dots.setTextColor(Color.WHITE);
        dots.setTextSize(27);
        dots.setGravity(Gravity.CENTER);
        dots.setPadding(0, 0, 0, dp(12));
        root.addView(dots);

        int[][] digits = {
                {1, 2, 3},
                {4, 5, 6},
                {7, 8, 9},
                {-1, 0, -2}
        };

        Button first = null;
        for (int[] rowDigits : digits) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            row.setGravity(Gravity.CENTER);

            for (int value : rowDigits) {
                Button button;
                if (value == -1) {
                    button = makeButton("CLEAR");
                    button.setOnClickListener(v -> clearPin());
                } else if (value == -2) {
                    button = makeButton("BACK");
                    button.setOnClickListener(v -> returnToDashboard());
                } else {
                    button = makeButton(Integer.toString(value));
                    final int digit = value;
                    button.setOnClickListener(v -> addDigit(digit));
                    if (first == null) {
                        first = button;
                    }
                }

                LinearLayout.LayoutParams params =
                        new LinearLayout.LayoutParams(dp(150), dp(66));
                params.setMargins(dp(6), dp(4), dp(6), dp(4));
                row.addView(button, params);
            }
            root.addView(row);
        }



        if (first != null) {
            first.requestFocus();
        }
        return root;
    }

    private Button makeButton(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Color.WHITE);
        button.setTextSize(18);
        button.setAllCaps(false);
        button.setFocusable(true);
        button.setFocusableInTouchMode(true);
        button.setBackgroundResource(R.drawable.tile_selector);
        return button;
    }

    private void addDigit(int digit) {
        if (entered.length() >= 4) {
            return;
        }

        entered.append(digit);
        updateDots();

        if (entered.length() == 4) {
            if (isPinCorrect(entered)) {
                ConsoleGuardService.allowExternalApps(this, 300000L);
                startActivity(new Intent(this, ParentToolsActivity.class));
                finish();
            } else {
                Toast.makeText(
                        this,
                        "Incorrect PIN.",
                        Toast.LENGTH_SHORT).show();
                clearPin();
            }
        }
    }

    private void clearPin() {
        entered.setLength(0);
        updateDots();
    }

    private boolean isPinCorrect(CharSequence candidate) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] value = digest.digest(
                    candidate.toString().getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder(value.length * 2);
            for (byte item : value) {
                hex.append(String.format("%02x", item & 0xff));
            }
            return MessageDigest.isEqual(
                    BuildConfig.PARENT_PIN_SHA256.getBytes(
                            StandardCharsets.US_ASCII),
                    hex.toString().getBytes(StandardCharsets.US_ASCII));
        } catch (NoSuchAlgorithmException ignored) {
            return false;
        }
    }

    private void updateDots() {
        StringBuilder display = new StringBuilder();
        for (int index = 0; index < 4; index++) {
            display.append(index < entered.length() ? "●" : "○");
            if (index < 3) {
                display.append("  ");
            }
        }
        dots.setText(display.toString());
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
