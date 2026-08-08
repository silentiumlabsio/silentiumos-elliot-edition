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
import android.widget.Toast;

public class RetroToolsActivity extends Activity {
    private static final String RETROARCH_PACKAGE = "com.retroarch.ra32";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
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
        if (keyCode == KeyEvent.KEYCODE_BUTTON_B
                || keyCode == KeyEvent.KEYCODE_BACK) {
            Intent intent = new Intent(this, ParentToolsActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP
                    | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(intent);
            finish();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    private View buildScreen() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(52), dp(22), dp(52), dp(22));
        root.setBackgroundResource(R.drawable.dashboard_background);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.silentium_icon);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        header.addView(logo, new LinearLayout.LayoutParams(dp(115), dp(115)));

        LinearLayout titleGroup = new LinearLayout(this);
        titleGroup.setOrientation(LinearLayout.VERTICAL);
        titleGroup.setPadding(dp(22), 0, 0, 0);

        TextView title = new TextView(this);
        title.setText("RETROARCH TOOLS");
        title.setTextColor(Color.WHITE);
        title.setTextSize(31);
        title.setLetterSpacing(0.08f);
        titleGroup.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("ADULT SETUP AREA");
        subtitle.setTextColor(Color.rgb(220, 54, 54));
        subtitle.setTextSize(16);
        subtitle.setLetterSpacing(0.14f);
        titleGroup.addView(subtitle);

        header.addView(titleGroup, new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        root.addView(header, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(125)));

        TextView returnTitle = new TextView(this);
        returnTitle.setText("RETURN TO SILENTIUMOS ANYTIME");
        returnTitle.setTextColor(Color.WHITE);
        returnTitle.setTextSize(24);
        returnTitle.setGravity(Gravity.CENTER);
        returnTitle.setPadding(0, dp(8), 0, dp(8));
        root.addView(returnTitle);

        TextView returnHelp = new TextView(this);
        returnHelp.setText(
                "Hold the Xbox VIEW button (two squares) and "
                        + "MENU button (three lines) together.\n"
                        + "RetroArch will close and return to Elliot's "
                        + "SilentiumOS screen.");
        returnHelp.setTextColor(Color.rgb(200, 200, 200));
        returnHelp.setTextSize(18);
        returnHelp.setGravity(Gravity.CENTER);
        returnHelp.setLineSpacing(0f, 1.15f);
        returnHelp.setPadding(dp(30), 0, dp(30), dp(20));
        root.addView(returnHelp);

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER);

        Button open = makeTile("OPEN RETROARCH\nCore downloads & settings");
        open.setOnClickListener(v -> launchRetroArch());
        row.addView(open, tileParams());

        Button coreHelp = makeTile("CORE SETUP\nRequired emulator engines");
        coreHelp.setOnClickListener(v -> showCoreHelp());
        row.addView(coreHelp, tileParams());

        Button back = makeTile("BACK TO SILENTIUMOS\nReturn to dashboard");
        back.setOnClickListener(v -> {
            Intent intent = new Intent(this, ParentToolsActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP
                    | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(intent);
            finish();
        });
        row.addView(back, tileParams());

        root.addView(row, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));

        TextView footer = new TextView(this);
        footer.setText(
                "VIEW + MENU = RETURN  •  MADE FOR ELLIOT  •  "
                        + "BUILT BY SILENTIUM LABS");
        footer.setTextColor(Color.rgb(130, 130, 130));
        footer.setTextSize(11);
        footer.setGravity(Gravity.CENTER);
        footer.setPadding(0, dp(18), 0, 0);
        root.addView(footer);

        open.requestFocus();
        return root;
    }

    private void launchRetroArch() {
        Intent launch = getPackageManager()
                .getLaunchIntentForPackage(RETROARCH_PACKAGE);
        if (launch == null) {
            Toast.makeText(
                    this,
                    "RetroArch is not installed.",
                    Toast.LENGTH_LONG).show();
            return;
        }
        startActivity(launch);
    }

    private void showCoreHelp() {
        Toast.makeText(
                this,
                "In RetroArch: Online Updater > Core Downloader. "
                        + "Install FCEUmm, Snes9x 2010, Gambatte, "
                        + "mGBA, Genesis Plus GX, 2048, Mr. Boom and Craft.",
                Toast.LENGTH_LONG).show();
    }

    private Button makeTile(String text) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(Color.WHITE);
        button.setTextSize(17);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setFocusable(true);
        button.setFocusableInTouchMode(true);
        button.setBackgroundResource(R.drawable.tile_selector);
        button.setPadding(dp(14), dp(10), dp(14), dp(10));
        button.setOnFocusChangeListener((v, hasFocus) -> v.animate()
                .scaleX(hasFocus ? 1.045f : 1f)
                .scaleY(hasFocus ? 1.045f : 1f)
                .setDuration(120)
                .start());
        return button;
    }

    private LinearLayout.LayoutParams tileParams() {
        LinearLayout.LayoutParams params =
                new LinearLayout.LayoutParams(0, dp(116), 1f);
        params.setMargins(dp(8), dp(8), dp(8), dp(8));
        return params;
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
}
