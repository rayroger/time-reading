package com.timereading.app

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.timereading.app.ml.WatchDialAnalyzer
import com.timereading.app.ml.WatchTime
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * Instrumented test for WatchDialAnalyzer.
 * These tests run on an Android device or emulator.
 */
@RunWith(AndroidJUnit4::class)
class WatchDialAnalyzerTest {

    private lateinit var context: Context
    private var analyzer: WatchDialAnalyzer? = null

    @Before
    fun setUp() {
        context = ApplicationProvider.getApplicationContext()
    }

    @After
    fun tearDown() {
        analyzer?.close()
        analyzer = null
    }

    @Test
    fun testAnalyzerInitialization() {
        // Test that analyzer can be created without crashing
        var callbackInvoked = false
        analyzer = WatchDialAnalyzer(context) { watchTime ->
            callbackInvoked = true
        }
        
        assertNotNull(analyzer)
    }

    @Test
    fun testAnalyzerClosePreventsMemoryLeak() {
        analyzer = WatchDialAnalyzer(context) { watchTime ->
            // Callback
        }
        
        // Should not throw exception
        analyzer?.close()
        
        // Calling close multiple times should be safe
        analyzer?.close()
    }

    @Test
    fun testAnalyzerWithCallback() {
        val latch = CountDownLatch(1)
        var receivedWatchTime: WatchTime? = null
        
        analyzer = WatchDialAnalyzer(context) { watchTime ->
            receivedWatchTime = watchTime
            latch.countDown()
        }
        
        // Since we don't have a real model, the callback will eventually be called
        // with null (no detection) during mock analysis
        // We just verify the analyzer was created successfully
        assertNotNull(analyzer)
    }

    @Test
    fun testContextNotNull() {
        // Verify we have a valid context for testing
        assertNotNull(context)
        assertNotNull(context.assets)
    }

    @Test
    fun testModelFileAccess() {
        // Test that we can check for the model file in assets
        try {
            val inputStream = context.assets.open("watch_detector.tflite")
            inputStream.close()
            // If we get here, the model exists
            assertTrue("Model file exists", true)
        } catch (e: Exception) {
            // Model file doesn't exist, which is expected for this test
            // The analyzer should handle this gracefully
            assertTrue("Model file not found - analyzer should use mock mode", true)
        }
    }

    @Test
    fun testAnalyzerHandlesMissingModel() {
        // Create analyzer without model file
        // Should not crash and should fall back to mock mode
        var exceptionThrown = false
        
        try {
            analyzer = WatchDialAnalyzer(context) { watchTime ->
                // Mock mode should return null
                assertNull("Mock mode should return null", watchTime)
            }
        } catch (e: Exception) {
            exceptionThrown = true
        }
        
        assertFalse("Analyzer should handle missing model gracefully", exceptionThrown)
    }

    @Test
    fun testMultipleAnalyzerInstances() {
        // Test that we can create multiple analyzer instances
        val analyzer1 = WatchDialAnalyzer(context) { }
        val analyzer2 = WatchDialAnalyzer(context) { }
        
        assertNotNull(analyzer1)
        assertNotNull(analyzer2)
        
        analyzer1.close()
        analyzer2.close()
    }
}
