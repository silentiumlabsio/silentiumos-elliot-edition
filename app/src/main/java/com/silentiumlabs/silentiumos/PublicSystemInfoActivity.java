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
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Displays public build facts without reading hardware identifiers, accounts,
 * network state, installed packages, or other device-specific information.
 */
public class PublicSystemInfoActivity extends Activity {
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
    protected void onResume() {
        super.onResume();
        hideSystemUi();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK
                || keyCode == KeyEvent.KEYCODE_BUTTON_B) {
            returnToParentTools();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    private View buildScreen() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(54), dp(28), dp(54), dp(24));
        root.setBackgroundResource(R.drawable.dashboard_background);

        TextView eyebrow = makeText(
                "SILENTIUM LABS  |  PUBLIC SOURCE",
                13,
                Color.rgb(220, 54, 54));
        eyebrow.setLetterSpacing(0.13f);
        root.addView(eyebrow, fullWidth());

        TextView title = makeText("ABOUT ELLIOT EDITION", 31, Color.WHITE);
        title.setLetterSpacing(0.08f);
        title.setPadding(0, dp(5), 0, dp(18));
        root.addView(title, fullWidth());

        LinearLayout facts = new LinearLayout(this);
        facts.setOrientation(LinearLayout.HORIZONTAL);
        facts.setGravity(Gravity.CENTER);
        facts.addView(makeFactCard(
                "BUILD",
                BuildConfig.VERSION_NAME,
                "Version only; no device fingerprint"), factParams());
        facts.addView(makeFactCard(
                "TARGET",
                "2024 FIRE TV STICK HD",
                "Fire OS 7 / Android API 28+"), factParams());
        facts.addView(makeFactCard(
                "PRIVACY",
                "LOCAL-FIRST",
                "No analytics, ads, or accounts"), factParams());
        root.addView(facts, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(155)));

        TextView statement = makeText(
                "This screen intentionally shows public project facts only. "
                        + "It does not read or display the device serial number, "
                        + "IP address, Wi-Fi name, account details, or game files.",
                15,
                Color.rgb(210, 210, 210));
        statement.setBackgroundResource(R.drawable.info_panel);
        statement.setGravity(Gravity.CENTER);
        statement.setPadding(dp(32), dp(16), dp(32), dp(16));
        LinearLayout.LayoutParams statementParams = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(92));
        statementParams.setMargins(dp(8), dp(12), dp(8), dp(15));
        root.addView(statement, statementParams);

        TextView source = makeText(
                "SOURCE: github.com/silentiumlabsio/silentiumos-elliot-edition  |  "
                        + "LICENSE: SEE LICENSE.md",
                12,
                Color.rgb(145, 145, 145));
        source.setGravity(Gravity.CENTER);
        root.addView(source, fullWidth());

        ConsoleTileButton back = new ConsoleTileButton(
                this, "Return", "Back to parent tools");
        back.setOnClickListener(view -> returnToParentTools());
        LinearLayout.LayoutParams backParams = new LinearLayout.LayoutParams(
                dp(520), dp(82));
        backParams.setMargins(0, dp(18), 0, 0);
        root.addView(back, backParams);
        back.requestFocus();

        return root;
    }

    private View makeFactCard(String label, String value, String detail) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setGravity(Gravity.CENTER);
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackgroundResource(R.drawable.info_panel);

        TextView labelView = makeText(label, 11, Color.rgb(220, 54, 54));
        labelView.setLetterSpacing(0.14f);
        card.addView(labelView);

        TextView valueView = makeText(value, 18, Color.WHITE);
        valueView.setPadding(0, dp(8), 0, dp(5));
        card.addView(valueView);

        TextView detailView = makeText(detail, 12, Color.rgb(175, 175, 175));
        card.addView(detailView);
        return card;
    }

    private TextView makeText(String text, int size, int color) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(color);
        view.setTextSize(size);
        view.setGravity(Gravity.CENTER);
        return view;
    }

    private LinearLayout.LayoutParams factParams() {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.MATCH_PARENT, 1f);
        params.setMargins(dp(8), 0, dp(8), 0);
        return params;
    }

    private LinearLayout.LayoutParams fullWidth() {
        return new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
    }

    private void returnToParentTools() {
        Intent intent = new Intent(this, ParentToolsActivity.class);
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
