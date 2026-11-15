package com.asjohn720.ball.domain.models

import androidx.annotation.Keep
import androidx.annotation.StringRes
import com.google.gson.annotations.SerializedName
import com.asjohn720.ball.R

@Keep
enum class HapticIntensity(@field:StringRes val titleRes: Int) {
    @SerializedName("LIGHT")
    LIGHT(R.string.haptic_light),
    @SerializedName("MEDIUM")
    MEDIUM(R.string.haptic_medium),
    @SerializedName("STRONG")
    STRONG(R.string.haptic_strong)
}