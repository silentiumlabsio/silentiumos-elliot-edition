package com.silentiumlabs.silentiumos;

import android.app.ActivityManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.app.usage.UsageEvents;
import android.app.usage.UsageStatsManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;

import java.util.List;

public class ConsoleGuardService extends Service {
    private static final String CHANNEL_ID = "silentium_console_guard";
    private static final int NOTIFICATION_ID = 6106;
    private static final String PREFS = "console_guard";
    private static final String EXTERNAL_UNTIL = "external_until";
    private static final long CHECK_INTERVAL_MS = 700L;

    private final Handler handler = new Handler(Looper.getMainLooper());

    private final Runnable checkTask = new Runnable() {
        @Override
        public void run() {
            try {
                enforceConsoleMode();
            } finally {
                handler.postDelayed(this, CHECK_INTERVAL_MS);
            }
        }
    };

    public static void allowExternalApps(Context context, long durationMs) {
        long until = System.currentTimeMillis() + Math.max(10000L, durationMs);
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putLong(EXTERNAL_UNTIL, until)
                .apply();
    }

    public static void lockNow(Context context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit()
                .putLong(EXTERNAL_UNTIL, 0L)
                .apply();
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
        startForeground(NOTIFICATION_ID, buildNotification());
        handler.post(checkTask);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private Notification buildNotification() {
        Intent open = new Intent(this, MainActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP);

        PendingIntent pending = PendingIntent.getActivity(
                this,
                0,
                open,
                PendingIntent.FLAG_UPDATE_CURRENT
                        | PendingIntent.FLAG_IMMUTABLE);

        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);

        return builder
                .setSmallIcon(R.drawable.silentium_icon)
                .setContentTitle("SilentiumOS Console Mode")
                .setContentText("Elliot's dashboard is protected")
                .setOngoing(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .setContentIntent(pending)
                .build();
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT < 26) {
            return;
        }

        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "SilentiumOS Console Guard",
                NotificationManager.IMPORTANCE_MIN);
        channel.setDescription(
                "Keeps Elliot's Fire TV inside the SilentiumOS console.");
        channel.setShowBadge(false);

        NotificationManager manager =
                (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (manager != null) {
            manager.createNotificationChannel(channel);
        }
    }

    private void enforceConsoleMode() {
        SharedPreferences preferences =
                getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        long externalUntil = preferences.getLong(EXTERNAL_UNTIL, 0L);
        if (System.currentTimeMillis() < externalUntil) {
            return;
        }

        String topPackage = getForegroundPackage();
        if (topPackage == null || topPackage.length() == 0) {
            return;
        }

        if (isAllowed(topPackage)) {
            return;
        }

        openDashboard();
    }

    private boolean isAllowed(String packageName) {
        return packageName.equals(getPackageName())
                || packageName.startsWith(getPackageName() + ":")
                || packageName.equals("com.retroarch.ra32")
                || packageName.equals("com.android.systemui")
                || packageName.equals("android");
    }

    private String getForegroundPackage() {
        try {
            ActivityManager manager =
                    (ActivityManager) getSystemService(ACTIVITY_SERVICE);
            if (manager != null) {
                List<ActivityManager.RunningTaskInfo> tasks =
                        manager.getRunningTasks(1);
                if (tasks != null
                        && !tasks.isEmpty()
                        && tasks.get(0).topActivity != null) {
                    String current = tasks.get(0)
                            .topActivity
                            .getPackageName();
                    if (current != null && current.length() > 0) {
                        return current;
                    }
                }
            }
        } catch (Exception ignored) {
            // Usage events are the fallback.
        }

        return getForegroundFromUsageEvents();
    }

    private String getForegroundFromUsageEvents() {
        try {
            UsageStatsManager manager =
                    (UsageStatsManager) getSystemService(
                            Context.USAGE_STATS_SERVICE);
            if (manager == null) {
                return null;
            }

            long end = System.currentTimeMillis();
            UsageEvents events = manager.queryEvents(end - 3000L, end);
            UsageEvents.Event event = new UsageEvents.Event();
            String latest = null;
            long latestTimestamp = 0L;

            while (events.hasNextEvent()) {
                events.getNextEvent(event);
                if (event.getEventType()
                        == UsageEvents.Event.MOVE_TO_FOREGROUND
                        && event.getTimeStamp() >= latestTimestamp) {
                    latest = event.getPackageName();
                    latestTimestamp = event.getTimeStamp();
                }
            }

            if (latestTimestamp == 0L
                    || end - latestTimestamp > 1600L) {
                return null;
            }

            return latest;
        } catch (Exception ignored) {
            return null;
        }
    }

    private void openDashboard() {
        Intent intent = new Intent(this, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(intent);
    }
}
