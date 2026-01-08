package com.timereading.app.ml

import org.junit.Assert.*
import org.junit.Test

/**
 * Unit tests for TimeExtractionHelper.
 */
class TimeExtractionHelperTest {

    @Test
    fun testExtractTimeFromAngles_12OClock() {
        val angles = HandAngles(
            hourAngle = 0f,    // 12 o'clock
            minuteAngle = 0f,  // 0 minutes
            secondAngle = 0f   // 0 seconds
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        
        assertEquals(0, time.hours)
        assertEquals(0, time.minutes)
        assertEquals(0, time.seconds)
        assertTrue(time.confidence > 0.5f) // Should have high confidence for aligned hands
    }

    @Test
    fun testExtractTimeFromAngles_3OClock() {
        val angles = HandAngles(
            hourAngle = 90f,   // 3 o'clock
            minuteAngle = 0f,  // 0 minutes
            secondAngle = 0f   // 0 seconds
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        
        assertEquals(3, time.hours)
        assertEquals(0, time.minutes)
        assertEquals(0, time.seconds)
    }

    @Test
    fun testExtractTimeFromAngles_6OClock() {
        val angles = HandAngles(
            hourAngle = 180f,  // 6 o'clock
            minuteAngle = 0f,  // 0 minutes
            secondAngle = 0f   // 0 seconds
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        
        assertEquals(6, time.hours)
        assertEquals(0, time.minutes)
        assertEquals(0, time.seconds)
    }

    @Test
    fun testExtractTimeFromAngles_9OClock() {
        val angles = HandAngles(
            hourAngle = 270f,  // 9 o'clock
            minuteAngle = 0f,  // 0 minutes
            secondAngle = 0f   // 0 seconds
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        
        assertEquals(9, time.hours)
        assertEquals(0, time.minutes)
        assertEquals(0, time.seconds)
    }

    @Test
    fun testExtractTimeFromAngles_330() {
        // 3:30 - hour hand halfway between 3 and 4
        val angles = HandAngles(
            hourAngle = 105f,  // 3.5 hours * 30 degrees = 105
            minuteAngle = 180f, // 30 minutes * 6 degrees = 180
            secondAngle = 0f
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        
        assertEquals(3, time.hours)
        assertEquals(30, time.minutes)
        assertEquals(0, time.seconds)
    }

    @Test
    fun testExtractTimeFromAngles_1215() {
        // 12:15
        val angles = HandAngles(
            hourAngle = 7.5f,  // 0.25 hours * 30 degrees = 7.5
            minuteAngle = 90f,  // 15 minutes * 6 degrees = 90
            secondAngle = 180f  // 30 seconds * 6 degrees = 180
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        
        assertEquals(0, time.hours)
        assertEquals(15, time.minutes)
        assertEquals(30, time.seconds)
    }

    @Test
    fun testExtractTimeFromAngles_WithoutSeconds() {
        val angles = HandAngles(
            hourAngle = 60f,   // 2 o'clock
            minuteAngle = 0f,  // 0 minutes
            secondAngle = -1f  // No second hand
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        
        assertEquals(2, time.hours)
        assertEquals(0, time.minutes)
        assertEquals(-1, time.seconds)
    }

    @Test
    fun testCalculateAngle_12OClock() {
        val angle = TimeExtractionHelper.calculateAngle(100f, 100f, 100f, 50f)
        assertEquals(0f, angle, 0.1f) // Pointing up (12 o'clock)
    }

    @Test
    fun testCalculateAngle_3OClock() {
        val angle = TimeExtractionHelper.calculateAngle(100f, 100f, 150f, 100f)
        assertEquals(90f, angle, 0.1f) // Pointing right (3 o'clock)
    }

    @Test
    fun testCalculateAngle_6OClock() {
        val angle = TimeExtractionHelper.calculateAngle(100f, 100f, 100f, 150f)
        assertEquals(180f, angle, 0.1f) // Pointing down (6 o'clock)
    }

    @Test
    fun testCalculateAngle_9OClock() {
        val angle = TimeExtractionHelper.calculateAngle(100f, 100f, 50f, 100f)
        assertEquals(270f, angle, 0.1f) // Pointing left (9 o'clock)
    }

    @Test
    fun testValidateTime_ValidTime() {
        val validTime = WatchTime(3, 30, 45, 0.9f)
        assertTrue(TimeExtractionHelper.validateTime(validTime))
    }

    @Test
    fun testValidateTime_LowConfidence() {
        val lowConfidenceTime = WatchTime(3, 30, 45, 0.3f)
        assertFalse(TimeExtractionHelper.validateTime(lowConfidenceTime))
    }

    @Test
    fun testValidateTime_InvalidHours() {
        val invalidTime = WatchTime(12, 30, 45, 0.9f)
        assertFalse(TimeExtractionHelper.validateTime(invalidTime))
    }

    @Test
    fun testValidateTime_ThresholdConfidence() {
        val thresholdTime = WatchTime(3, 30, 45, 0.5f)
        assertTrue(TimeExtractionHelper.validateTime(thresholdTime))
        
        val belowThreshold = WatchTime(3, 30, 45, 0.49f)
        assertFalse(TimeExtractionHelper.validateTime(belowThreshold))
    }

    @Test
    fun testHandAngles_DataClass() {
        val angles1 = HandAngles(90f, 180f, 270f)
        assertEquals(90f, angles1.hourAngle, 0.001f)
        assertEquals(180f, angles1.minuteAngle, 0.001f)
        assertEquals(270f, angles1.secondAngle, 0.001f)
        
        val angles2 = HandAngles(90f, 180f) // Without seconds
        assertEquals(90f, angles2.hourAngle, 0.001f)
        assertEquals(180f, angles2.minuteAngle, 0.001f)
        assertEquals(-1f, angles2.secondAngle, 0.001f)
    }

    @Test
    fun testConfidenceCalculation_AlignedHands() {
        // At exactly 3:00, hour hand at 90° and minute hand at 0°
        val angles = HandAngles(90f, 0f, 0f)
        val time = TimeExtractionHelper.extractTime(angles)
        
        // Confidence should be very high when hands are properly aligned
        assertTrue("Confidence should be high for aligned hands", time.confidence > 0.8f)
    }

    @Test
    fun testConfidenceCalculation_MisalignedHands() {
        // Hour hand says 3:00 (90°) but minute hand says 30 minutes (180°)
        // This is inconsistent - hour should be at 105° for 3:30
        val angles = HandAngles(90f, 180f, 0f)
        val time = TimeExtractionHelper.extractTime(angles)
        
        // Confidence should be lower for misaligned hands
        assertTrue("Confidence should be lower for misaligned hands", time.confidence < 1.0f)
    }

    @Test
    fun testMinuteHandBoundary() {
        // Test 59 minutes
        val angles = HandAngles(
            hourAngle = 29.5f,  // Almost at 1 o'clock
            minuteAngle = 354f,  // 59 minutes * 6 = 354 degrees
            secondAngle = 0f
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        assertEquals(0, time.hours) // Should be 0 (12 o'clock hour)
        assertEquals(59, time.minutes)
    }

    @Test
    fun testAngleNormalization() {
        // Test that angles beyond 360 are handled correctly
        val angles = HandAngles(
            hourAngle = 360f,  // Same as 0
            minuteAngle = 0f,
            secondAngle = 0f
        )
        
        val time = TimeExtractionHelper.extractTime(angles)
        // 360 / 30 = 12, 12 % 12 = 0
        assertEquals(0, time.hours)
        assertEquals(0, time.minutes)
    }
}
