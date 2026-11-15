package com.asjohn720.ball.utils

import android.content.res.Resources

object DensityUtils {
    fun dp2px(dpValue: Float): Int {
        val scale = Resources.getSystem().displayMetrics.density
        return (dpValue * scale + 0.5f).toInt()
    }
}