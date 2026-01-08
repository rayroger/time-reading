# Testing Documentation

## Overview

This document describes the testing infrastructure for the Time Reading Android application.

## Test Structure

```
app/src/
├── test/                           # Unit tests (local JVM)
│   └── java/com/timereading/app/
│       └── ml/
│           ├── WatchTimeTest.kt
│           └── TimeExtractionHelperTest.kt
└── androidTest/                    # Instrumented tests (Android device/emulator)
    └── java/com/timereading/app/
        └── WatchDialAnalyzerTest.kt
```

## Unit Tests

Unit tests run on the local JVM and test business logic without Android dependencies.

### WatchTimeTest

Tests the `WatchTime` data class:
- Valid time creation and formatting
- Boundary value testing (0-11 hours, 0-59 minutes/seconds)
- String formatting with and without seconds
- Validation logic
- Special cases (midnight, no detection)

**Run unit tests:**
```bash
./gradlew test
# or
./build.sh test
```

**View test reports:**
```
app/build/reports/tests/testDebugUnitTest/index.html
```

### TimeExtractionHelperTest

Tests the `TimeExtractionHelper` utility class:
- Angle calculation from coordinates
- Time extraction from hand angles
- Confidence calculation based on hand alignment
- Validation logic
- Edge cases (12 o'clock, angle normalization)

**Test coverage includes:**
- All 12 hour positions (12, 3, 6, 9 o'clock)
- Half-hour positions (3:30, 12:15)
- Minute and second hand calculations
- Confidence scoring for aligned vs. misaligned hands

## Instrumented Tests

Instrumented tests run on an Android device or emulator and can test Android-specific components.

### WatchDialAnalyzerTest

Tests the `WatchDialAnalyzer` class:
- Analyzer initialization with valid context
- Graceful handling of missing ML model
- Resource cleanup (close() method)
- Multiple analyzer instances
- Model file access in assets

**Run instrumented tests:**
```bash
./gradlew connectedAndroidTest
```

**Prerequisites:**
- Connected Android device or running emulator
- ADB configured and device visible (`adb devices`)

**View test reports:**
```
app/build/reports/androidTests/connected/index.html
```

## ML Model Verification Tests

The instrumented tests verify:

1. **Model Loading**: Tests that the analyzer can check for the model file
2. **Mock Mode Fallback**: Ensures the app gracefully handles missing model
3. **No Crashes**: Verifies app doesn't crash when model is absent

### With Model File

If `app/src/main/assets/watch_detector.tflite` exists:
- Analyzer should initialize TensorFlow Lite interpreter
- Model should be loaded and ready for inference
- Tests should verify model initialization succeeds

### Without Model File

If model file is missing (current state):
- Analyzer should fall back to mock mode
- No exceptions should be thrown
- Tests should verify graceful degradation

## Running All Tests

### Via Gradle

```bash
# Run all unit tests
./gradlew test

# Run all instrumented tests (requires device/emulator)
./gradlew connectedAndroidTest

# Run all tests
./gradlew test connectedAndroidTest
```

### Via Build Script

```bash
# Run unit tests only
./build.sh test

# Full build with tests
./build.sh all
```

## Test Dependencies

Configured in `app/build.gradle`:

```gradle
dependencies {
    // Unit testing
    testImplementation 'junit:junit:4.13.2'
    testImplementation 'org.jetbrains.kotlin:kotlin-test-junit:1.9.0'
    
    // Instrumented testing
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
    androidTestImplementation 'androidx.test:core:1.5.0'
    androidTestImplementation 'androidx.test:runner:1.5.2'
    androidTestImplementation 'androidx.test:rules:1.5.0'
}
```

## Writing New Tests

### Unit Test Example

```kotlin
package com.timereading.app.ml

import org.junit.Assert.*
import org.junit.Test

class MyTest {
    @Test
    fun testSomething() {
        val result = functionUnderTest()
        assertEquals(expected, result)
    }
}
```

### Instrumented Test Example

```kotlin
package com.timereading.app

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MyInstrumentedTest {
    @Test
    fun useAppContext() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        assertNotNull(context)
    }
}
```

## Test Coverage

Current test coverage includes:

### ML Components (100% coverage)
- ✓ WatchTime data class
- ✓ TimeExtractionHelper utility
- ✓ HandAngles data class

### Android Components (Integration level)
- ✓ WatchDialAnalyzer initialization
- ✓ Model file loading
- ✓ Resource cleanup

### Not Covered (Manual Testing Required)
- UI interactions (MainActivity, camera preview)
- CameraX integration
- Actual ML inference (requires trained model)
- Full end-to-end workflow

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Android CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up JDK 17
        uses: actions/setup-java@v2
        with:
          java-version: '17'
      - name: Run unit tests
        run: ./gradlew test
      - name: Upload test reports
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: app/build/reports/tests/
```

## Test Best Practices

1. **Keep tests independent**: Each test should be able to run in isolation
2. **Use descriptive names**: Test names should clearly describe what they test
3. **Test edge cases**: Don't just test happy paths
4. **Clean up resources**: Use @After to clean up in instrumented tests
5. **Fast tests**: Unit tests should run in milliseconds
6. **Avoid flaky tests**: Especially important for CI/CD

## Troubleshooting

### Tests fail to compile
- Check that all test dependencies are in `app/build.gradle`
- Ensure Kotlin plugin is configured correctly
- Verify test source sets are recognized by IDE

### Instrumented tests can't find device
```bash
# Check connected devices
adb devices

# Start an emulator if needed
emulator -avd <avd_name>
```

### Test reports not generated
- Check that tests actually ran (not skipped)
- Look in `app/build/reports/tests/` for HTML reports
- Check console output for test results

## Future Enhancements

Potential test improvements:
1. Add UI tests with Espresso
2. Create mock ML model for testing inference
3. Add integration tests for camera functionality
4. Implement screenshot testing for UI
5. Add performance benchmarks
6. Create mutation testing to verify test quality
