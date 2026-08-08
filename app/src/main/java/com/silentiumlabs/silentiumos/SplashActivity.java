package com.silentiumlabs.silentiumos;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

public class SplashActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        hideSystemUi();
        setContentView(buildSplash());

        handler.postDelayed(() -> {
            startActivity(new Intent(this, MainActivity.class));
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
            finish();
        }, 2300);
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    private View buildSplash() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(dp(40), dp(25), dp(40), dp(25));
        root.setBackgroundColor(Color.rgb(2, 2, 2));

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.silentium_logo);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        root.addView(logo, new LinearLayout.LayoutParams(dp(460), dp(410)));

        TextView booting = new TextView(this);
        booting.setText("SILENTIUMOS");
        booting.setTextColor(Color.WHITE);
        booting.setTextSize(28);
        booting.setLetterSpacing(0.13f);
        booting.setGravity(Gravity.CENTER);
        root.addView(booting);

        TextView loading = new TextView(this);
        loading.setText("ELLIOT EDITION  •  BUILT BY SILENTIUM LABS");
        loading.setTextColor(Color.rgb(205, 45, 45));
        loading.setTextSize(12);
        loading.setLetterSpacing(0.17f);
        loading.setGravity(Gravity.CENTER);
        loading.setPadding(0, dp(10), 0, 0);
        root.addView(loading);

        TextView personal = new TextView(this);
        personal.setText("PREPARING ELLIOT'S GAME SYSTEM");
        personal.setTextColor(Color.rgb(155, 155, 155));
        personal.setTextSize(11);
        personal.setLetterSpacing(0.12f);
        personal.setGravity(Gravity.CENTER);
        personal.setPadding(0, dp(14), 0, 0);
        root.addView(personal);

        return root;
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
