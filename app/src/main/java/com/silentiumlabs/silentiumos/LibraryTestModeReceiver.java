package com.silentiumlabs.silentiumos;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public class LibraryTestModeReceiver extends BroadcastReceiver {
    private static final long DEFAULT_TEST_WINDOW_MS =
            6L * 60L * 60L * 1000L;

    @Override
    public void onReceive(Context context, Intent intent) {
        if (context == null || intent == null) {
            return;
        }

        String mode = intent.getStringExtra("mode");

        if ("enable".equalsIgnoreCase(mode)) {
            long duration = intent.getLongExtra(
                    "duration_ms",
                    DEFAULT_TEST_WINDOW_MS);
            ConsoleGuardService.allowExternalApps(
                    context,
                    Math.min(
                            DEFAULT_TEST_WINDOW_MS,
                            Math.max(60000L, duration)));
            return;
        }

        ConsoleGuardService.lockNow(context);

        Intent guard = new Intent(
                context,
                ConsoleGuardService.class);
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(guard);
            } else {
                context.startService(guard);
            }
        } catch (Exception ignored) {
            // The dashboard also starts the guard on resume.
        }
    }
}
