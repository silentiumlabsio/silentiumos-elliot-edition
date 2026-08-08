package com.silentiumlabs.silentiumos;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import android.view.accessibility.AccessibilityEvent;

public class HomeRedirectAccessibilityService
        extends AccessibilityService {

    private static final String AMAZON_LAUNCHER =
            "com.amazon.tv.launcher";
    private static final String AMAZON_HOME_STARTER =
            "com.amazon.firehomestarter";
    private static final long REDIRECT_COOLDOWN_MS = 900L;

    private final Handler handler =
            new Handler(Looper.getMainLooper());
    private long lastRedirectAt = 0L;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();

        // On boot, Amazon Home may already be visible before the first
        // accessibility event reaches us. Open SilentiumOS once after the
        // system finishes binding this service.
        handler.postDelayed(this::openSilentiumDashboard, 900L);
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null || event.getPackageName() == null) {
            return;
        }

        String packageName =
                event.getPackageName().toString();

        if (!AMAZON_LAUNCHER.equals(packageName)
                && !AMAZON_HOME_STARTER.equals(packageName)) {
            return;
        }

        if (parentAccessIsActive()) {
            return;
        }

        long now = System.currentTimeMillis();
        if (now - lastRedirectAt < REDIRECT_COOLDOWN_MS) {
            return;
        }

        lastRedirectAt = now;
        handler.removeCallbacksAndMessages(null);
        handler.postDelayed(this::openSilentiumDashboard, 90L);
    }

    @Override
    public void onInterrupt() {
        // No spoken or haptic feedback is used.
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    private boolean parentAccessIsActive() {
        long externalUntil = getSharedPreferences(
                "console_guard",
                MODE_PRIVATE)
                .getLong("external_until", 0L);
        return System.currentTimeMillis() < externalUntil;
    }

    private void openSilentiumDashboard() {
        if (parentAccessIsActive()) {
            return;
        }

        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK
                        | Intent.FLAG_ACTIVITY_CLEAR_TOP
                        | Intent.FLAG_ACTIVITY_SINGLE_TOP
                        | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);

        try {
            startActivity(intent);
        } catch (Exception ignored) {
            Intent splash = new Intent(this, SplashActivity.class);
            splash.addFlags(
                    Intent.FLAG_ACTIVITY_NEW_TASK
                            | Intent.FLAG_ACTIVITY_CLEAR_TOP
                            | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(splash);
        }
    }
}
