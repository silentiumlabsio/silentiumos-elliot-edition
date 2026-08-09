package com.silentiumlabs.silentiumos;

import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.text.Spannable;
import android.text.SpannableString;
import android.text.style.ForegroundColorSpan;
import android.text.style.RelativeSizeSpan;
import android.text.style.StyleSpan;
import android.view.Gravity;
import android.widget.Button;

import java.util.Locale;

/**
 * A controller-focused dashboard tile with consistent title, subtitle, and
 * focus treatment. The class only renders local text and does not collect or
 * transmit interaction data.
 */
public final class ConsoleTileButton extends Button {
    private static final int TITLE_COLOR = Color.WHITE;
    private static final int SUBTITLE_COLOR = Color.rgb(205, 205, 205);

    public ConsoleTileButton(Context context, String title, String subtitle) {
        super(context);
        configureView();
        setLabels(title, subtitle);
    }

    public void setLabels(String title, String subtitle) {
        String normalizedTitle = title.trim().toUpperCase(Locale.US);
        String normalizedSubtitle = subtitle.trim();
        String combined = normalizedTitle + "\n" + normalizedSubtitle;
        int subtitleStart = normalizedTitle.length() + 1;

        SpannableString label = new SpannableString(combined);
        label.setSpan(
                new StyleSpan(Typeface.BOLD),
                0,
                normalizedTitle.length(),
                Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
        label.setSpan(
                new ForegroundColorSpan(TITLE_COLOR),
                0,
                normalizedTitle.length(),
                Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
        label.setSpan(
                new RelativeSizeSpan(0.72f),
                subtitleStart,
                combined.length(),
                Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);
        label.setSpan(
                new ForegroundColorSpan(SUBTITLE_COLOR),
                subtitleStart,
                combined.length(),
                Spannable.SPAN_EXCLUSIVE_EXCLUSIVE);

        setText(label);
        setContentDescription(normalizedTitle + ". " + normalizedSubtitle);
    }

    private void configureView() {
        setAllCaps(false);
        setBackgroundResource(R.drawable.tile_selector);
        setFocusable(true);
        setFocusableInTouchMode(true);
        setGravity(Gravity.CENTER);
        setIncludeFontPadding(false);
        setLineSpacing(dp(3), 1f);
        setMaxLines(2);
        setMinHeight(0);
        setMinWidth(0);
        setPadding(dp(16), dp(10), dp(16), dp(10));
        setStateListAnimator(null);
        setTextColor(TITLE_COLOR);
        setTextSize(18);

        setOnFocusChangeListener((view, hasFocus) -> {
            view.animate()
                    .scaleX(hasFocus ? 1.045f : 1f)
                    .scaleY(hasFocus ? 1.045f : 1f)
                    .setDuration(120)
                    .start();
            view.setElevation(hasFocus ? dp(10) : 0);
        });
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
