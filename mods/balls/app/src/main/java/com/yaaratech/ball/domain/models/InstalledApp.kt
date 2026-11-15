package com.yaaratech.ball.domain.models

import android.graphics.drawable.Drawable

data class InstalledApp(
    val packageName: String,
    val appName: String,
    val icon: Drawable,
    var isSelected: Boolean = false
)
