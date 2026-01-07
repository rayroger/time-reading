package com.timereading.app.ml

/**
 * Data class representing the time extracted from an analog watch dial.
 *
 * @property hours Hours component (0-11)
 * @property minutes Minutes component (0-59)
 * @property seconds Seconds component (0-59), may be -1 if second hand not detected
 * @property confidence Confidence score of the detection (0.0-1.0)
 */
data class WatchTime(
    val hours: Int,
    val minutes: Int,
    val seconds: Int = -1,
    val confidence: Float
) {
    /**
     * Returns a formatted time string in HH:mm:ss or HH:mm format.
     * Hours are displayed in 12-hour format (12, 1-11).
     */
    fun toFormattedString(): String {
        // Convert 0 to 12 for 12-hour format display
        val displayHours = if (hours == 0) 12 else hours
        return if (seconds >= 0) {
            String.format("%02d:%02d:%02d", displayHours, minutes, seconds)
        } else {
            String.format("%02d:%02d", displayHours, minutes)
        }
    }

    /**
     * Returns true if this is a valid time reading.
     */
    fun isValid(): Boolean {
        return hours in 0..11 && minutes in 0..59 && (seconds < 0 || seconds in 0..59)
    }

    companion object {
        /**
         * Creates an invalid WatchTime instance to represent no detection.
         */
        fun noDetection(): WatchTime = WatchTime(0, 0, -1, 0f)
    }
}
