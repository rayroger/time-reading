package com.timereading.app.ml

import org.junit.Assert.*
import org.junit.Test

/**
 * Unit tests for WatchTime data class.
 */
class WatchTimeTest {

    @Test
    fun testValidTimeCreation() {
        val watchTime = WatchTime(3, 30, 45, 0.9f)
        
        assertEquals(3, watchTime.hours)
        assertEquals(30, watchTime.minutes)
        assertEquals(45, watchTime.seconds)
        assertEquals(0.9f, watchTime.confidence, 0.001f)
        assertTrue(watchTime.isValid())
    }

    @Test
    fun testValidTimeWithoutSeconds() {
        val watchTime = WatchTime(10, 15, -1, 0.85f)
        
        assertEquals(10, watchTime.hours)
        assertEquals(15, watchTime.minutes)
        assertEquals(-1, watchTime.seconds)
        assertEquals(0.85f, watchTime.confidence, 0.001f)
        assertTrue(watchTime.isValid())
    }

    @Test
    fun testFormattedStringWithSeconds() {
        val watchTime = WatchTime(3, 30, 45, 0.9f)
        assertEquals("03:30:45", watchTime.toFormattedString())
    }

    @Test
    fun testFormattedStringWithoutSeconds() {
        val watchTime = WatchTime(10, 15, -1, 0.85f)
        assertEquals("10:15", watchTime.toFormattedString())
    }

    @Test
    fun testFormattedStringWithMidnight() {
        val watchTime = WatchTime(0, 0, 0, 0.9f)
        assertEquals("12:00:00", watchTime.toFormattedString())
    }

    @Test
    fun testFormattedStringPaddingZeros() {
        val watchTime = WatchTime(1, 5, 9, 0.9f)
        assertEquals("01:05:09", watchTime.toFormattedString())
    }

    @Test
    fun testIsValidWithValidTime() {
        val watchTime = WatchTime(11, 59, 59, 0.9f)
        assertTrue(watchTime.isValid())
    }

    @Test
    fun testIsValidWithInvalidHours() {
        val watchTime = WatchTime(12, 30, 45, 0.9f)
        assertFalse(watchTime.isValid())
        
        val watchTime2 = WatchTime(-1, 30, 45, 0.9f)
        assertFalse(watchTime2.isValid())
    }

    @Test
    fun testIsValidWithInvalidMinutes() {
        val watchTime = WatchTime(5, 60, 45, 0.9f)
        assertFalse(watchTime.isValid())
        
        val watchTime2 = WatchTime(5, -1, 45, 0.9f)
        assertFalse(watchTime2.isValid())
    }

    @Test
    fun testIsValidWithInvalidSeconds() {
        val watchTime = WatchTime(5, 30, 60, 0.9f)
        assertFalse(watchTime.isValid())
        
        // -1 is valid (indicates no second hand)
        val watchTime2 = WatchTime(5, 30, -1, 0.9f)
        assertTrue(watchTime2.isValid())
        
        // -2 is invalid
        val watchTime3 = WatchTime(5, 30, -2, 0.9f)
        assertFalse(watchTime3.isValid())
    }

    @Test
    fun testNoDetection() {
        val watchTime = WatchTime.noDetection()
        
        assertEquals(0, watchTime.hours)
        assertEquals(0, watchTime.minutes)
        assertEquals(-1, watchTime.seconds)
        assertEquals(0f, watchTime.confidence, 0.001f)
        assertTrue(watchTime.isValid())
    }

    @Test
    fun testBoundaryValues() {
        // Test hour boundaries
        val time1 = WatchTime(0, 0, 0, 1.0f)
        assertTrue(time1.isValid())
        assertEquals("12:00:00", time1.toFormattedString())
        
        val time2 = WatchTime(11, 59, 59, 1.0f)
        assertTrue(time2.isValid())
        assertEquals("11:59:59", time2.toFormattedString())
    }

    @Test
    fun testConfidenceValues() {
        val highConfidence = WatchTime(5, 30, 45, 1.0f)
        assertEquals(1.0f, highConfidence.confidence, 0.001f)
        
        val lowConfidence = WatchTime(5, 30, 45, 0.0f)
        assertEquals(0.0f, lowConfidence.confidence, 0.001f)
        
        val mediumConfidence = WatchTime(5, 30, 45, 0.5f)
        assertEquals(0.5f, mediumConfidence.confidence, 0.001f)
    }
}
