package com.timereading.app.ml

import kotlin.math.atan2

/**
 * Data class representing angles of watch hands relative to 12 o'clock position.
 * Angles are in degrees (0-360), where 0/360 is 12 o'clock, 90 is 3 o'clock, etc.
 */
data class HandAngles(
    val hourAngle: Float,
    val minuteAngle: Float,
    val secondAngle: Float = -1f
)

/**
 * Utility class for extracting time from watch hand angles.
 */
object TimeExtractionHelper {

    /**
     * Calculates the angle of a point from the center, relative to 12 o'clock position.
     *
     * @param centerX X coordinate of the watch center
     * @param centerY Y coordinate of the watch center
     * @param pointX X coordinate of the hand tip
     * @param pointY Y coordinate of the hand tip
     * @return Angle in degrees (0-360), where 0 is 12 o'clock
     */
    fun calculateAngle(centerX: Float, centerY: Float, pointX: Float, pointY: Float): Float {
        val dx = pointX - centerX
        val dy = centerY - pointY // Inverted Y-axis (screen coordinates)
        
        // atan2 returns angle in radians with 3 o'clock as 0
        var angle = Math.toDegrees(atan2(dx.toDouble(), dy.toDouble())).toFloat()
        
        // Normalize to 0-360 range
        if (angle < 0) {
            angle += 360f
        }
        
        return angle
    }

    /**
     * Extracts time from watch hand angles.
     *
     * @param angles HandAngles containing angles of hour, minute, and optionally second hands
     * @return WatchTime with extracted time components and confidence
     */
    fun extractTime(angles: HandAngles): WatchTime {
        // Convert hour angle to hours (0-11)
        // Hour hand moves 30 degrees per hour (360/12 = 30)
        val hours = ((angles.hourAngle / 30f) % 12).toInt()
        
        // Convert minute angle to minutes (0-59)
        // Minute hand moves 6 degrees per minute (360/60 = 6)
        val minutes = ((angles.minuteAngle / 6f) % 60).toInt()
        
        // Convert second angle to seconds (0-59) if available
        val seconds = if (angles.secondAngle >= 0) {
            ((angles.secondAngle / 6f) % 60).toInt()
        } else {
            -1
        }
        
        // Calculate confidence based on hour-minute consistency
        val confidence = calculateConfidence(angles)
        
        return WatchTime(hours, minutes, seconds, confidence)
    }

    /**
     * Calculates confidence based on physical constraints of watch hands.
     * The hour hand position should be consistent with the minute hand position.
     *
     * For example, at 3:30, the hour hand should be at 105 degrees (halfway between 3 and 4).
     */
    private fun calculateConfidence(angles: HandAngles): Float {
        // Expected hour angle based on minute position
        // Each minute adds 0.5 degrees to hour hand (30 degrees / 60 minutes)
        val expectedMinuteContribution = (angles.minuteAngle / 360f) * 30f
        
        // Get base hour from hour angle
        val baseHourAngle = (angles.hourAngle / 30f).toInt() * 30f
        val expectedHourAngle = (baseHourAngle + expectedMinuteContribution) % 360f
        
        // Calculate angular difference
        var diff = kotlin.math.abs(angles.hourAngle - expectedHourAngle)
        if (diff > 180f) {
            diff = 360f - diff
        }
        
        // Convert to confidence (0-1), allowing 15 degrees tolerance
        val maxError = 15f
        val confidence = 1f - (diff / maxError).coerceIn(0f, 1f)
        
        return confidence
    }

    /**
     * Validates if the detected time is physically possible based on hand positions.
     *
     * @param time WatchTime to validate
     * @return true if the time reading is valid
     */
    fun validateTime(time: WatchTime): Boolean {
        if (!time.isValid()) {
            return false
        }
        
        // Check confidence threshold
        return time.confidence >= 0.5f
    }
}
