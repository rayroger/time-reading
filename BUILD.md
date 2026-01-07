# Build Guide - Time Reading Android App

This document provides comprehensive instructions for building, testing, and verifying the Time Reading Android application.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Build Scripts](#build-scripts)
- [Build Commands](#build-commands)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

1. **Java Development Kit (JDK)**
   - Version: JDK 11 or later
   - Download: [Oracle JDK](https://www.oracle.com/java/technologies/downloads/) or [OpenJDK](https://openjdk.org/)
   - Verify installation: `java -version`

2. **Android SDK**
   - Install via [Android Studio](https://developer.android.com/studio) (recommended)
   - Or install command-line tools from [Android Developer website](https://developer.android.com/studio#command-tools)
   - Set `ANDROID_HOME` or `ANDROID_SDK_ROOT` environment variable

3. **Gradle**
   - Included as Gradle Wrapper (`gradlew`)
   - No separate installation needed

4. **Git** (for cloning the repository)
   - Download: [Git Downloads](https://git-scm.com/downloads)

### Optional Tools

- **Android Debug Bridge (adb)** - For installing APKs on devices
- **aapt** (Android Asset Packaging Tool) - For APK analysis
- **Android Emulator** - For testing without physical device

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/rayroger/time-reading.git
cd time-reading
```

### 2. Build Debug APK

```bash
./build.sh debug
```

The debug APK will be generated at: `app/build/outputs/apk/debug/app-debug.apk`

### 3. Verify the Build

```bash
./verify-build.sh
```

### 4. Install on Device (Optional)

```bash
# Connect Android device or start emulator
./build.sh install
```

## Build Scripts

### build.sh

The main build script provides convenient commands for common build tasks.

**Usage:**
```bash
./build.sh [COMMAND] [OPTIONS]
```

**Available Commands:**
- `clean` - Clean build artifacts
- `debug` - Build debug APK
- `release` - Build release APK
- `assemble` - Assemble all variants
- `test` - Run unit tests
- `install` - Install debug APK on connected device
- `installRelease` - Install release APK on connected device
- `lint` - Run lint checks
- `all` - Clean, build, and test
- `help` - Show help message

**Examples:**
```bash
# Build debug APK
./build.sh debug

# Clean and build
./build.sh clean debug

# Run tests
./build.sh test

# Complete build cycle
./build.sh all

# Install on device
./build.sh install
```

### verify-build.sh

The verification script validates build outputs and project configuration.

**Usage:**
```bash
./verify-build.sh [OPTIONS]
```

**Available Options:**
- `--debug` - Verify debug build only (default)
- `--release` - Verify release build only
- `--all` - Verify both debug and release builds
- `--strict` - Enable strict mode (warnings as failures)
- `--help` - Show help message

**Examples:**
```bash
# Verify debug build
./verify-build.sh

# Verify both builds
./verify-build.sh --all

# Strict verification
./verify-build.sh --all --strict
```

## Build Commands

### Using Gradle Wrapper Directly

If you prefer to use Gradle commands directly:

#### Build Commands

```bash
# Clean project
./gradlew clean

# Build debug APK
./gradlew assembleDebug

# Build release APK
./gradlew assembleRelease

# Build all variants
./gradlew assemble

# Build and run unit tests
./gradlew build
```

#### Test Commands

```bash
# Run unit tests
./gradlew test

# Run unit tests for debug variant
./gradlew testDebug

# Run instrumented tests (requires device/emulator)
./gradlew connectedAndroidTest

# Generate test report
./gradlew test --info
```

#### Code Quality Commands

```bash
# Run lint checks
./gradlew lint

# Generate lint report
./gradlew lintDebug

# Run lint and fail on errors
./gradlew lintDebug --warning-mode all
```

#### Installation Commands

```bash
# Install debug APK
./gradlew installDebug

# Install release APK
./gradlew installRelease

# Uninstall app
./gradlew uninstallAll
```

#### Other Useful Commands

```bash
# List all available tasks
./gradlew tasks

# List all available tasks (including detailed info)
./gradlew tasks --all

# Show project dependencies
./gradlew app:dependencies

# Clean and rebuild
./gradlew clean build

# Build with stack trace (for debugging)
./gradlew assembleDebug --stacktrace

# Build with detailed logging
./gradlew assembleDebug --info
```

## Verification

### What Gets Verified

The verification script checks:

1. **Prerequisites**
   - Java installation and version
   - Gradle wrapper presence
   - Android SDK configuration
   - ADB availability

2. **Project Structure**
   - Build files (build.gradle, settings.gradle)
   - Source code presence
   - Resource files
   - Android manifest

3. **Gradle Configuration**
   - Android plugin configuration
   - Kotlin/Java configuration
   - Application ID and namespace
   - SDK versions (compileSdk, minSdk, targetSdk)
   - Dependencies

4. **Build Outputs**
   - APK existence and validity
   - APK size analysis
   - Package name extraction
   - Version information
   - DEX files presence
   - Resource compilation
   - Permissions declaration

5. **Test Configuration**
   - Unit test files
   - Instrumented test files
   - Test dependencies
   - Test reports

6. **Code Quality**
   - Lint configuration
   - Lint results (errors and warnings)

7. **Assets & Resources**
   - Asset files (including ML models)
   - Drawable resources
   - String resources
   - Theme/style resources

### Verification Output

The script provides colored output:
- ✓ (Green) - Test passed
- ✗ (Red) - Test failed
- ⚠ (Yellow) - Warning
- ℹ (Blue) - Information

Example output:
```
========================================
Time Reading - Build Verification
========================================

--- Verifying Prerequisites ---
✓ Java is installed: 11.0.12
✓ Gradle wrapper is present and executable
✓ Android SDK environment variable is set

--- Verifying Debug Build ---
✓ Debug APK exists
✓ Debug APK size: 12.34 MB
✓ Debug APK is a valid archive
✓ Package name: com.timereading.app
✓ Version: 1.0

========================================
Build Verification Summary
========================================
Total Tests: 45
Passed:      42
Failed:      0
Warnings:    3
Pass Rate:   93.3%

╔════════════════════════════════════════╗
║  ✓ BUILD VERIFICATION PASSED          ║
╚════════════════════════════════════════╝
```

## Troubleshooting

### Common Issues

#### 1. "Java not found"

**Solution:** Install Java JDK 11 or later and ensure it's in your PATH.

```bash
# Check Java installation
java -version

# Set JAVA_HOME (Linux/Mac)
export JAVA_HOME=/path/to/jdk
export PATH=$JAVA_HOME/bin:$PATH

# Set JAVA_HOME (Windows)
set JAVA_HOME=C:\Path\To\JDK
set PATH=%JAVA_HOME%\bin;%PATH%
```

#### 2. "Android SDK not found"

**Solution:** Install Android SDK and set environment variable.

```bash
# Set ANDROID_HOME (Linux/Mac)
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools:$PATH

# Set ANDROID_HOME (Windows)
set ANDROID_HOME=C:\Users\YourUser\AppData\Local\Android\Sdk
set PATH=%ANDROID_HOME%\tools;%ANDROID_HOME%\platform-tools;%PATH%
```

#### 3. "Permission denied" when running scripts

**Solution:** Make scripts executable.

```bash
chmod +x build.sh verify-build.sh
```

#### 4. "Could not resolve dependencies"

**Solution:** Check internet connection and Gradle cache.

```bash
# Clear Gradle cache
./gradlew clean --refresh-dependencies

# Or delete .gradle directory
rm -rf .gradle
./gradlew clean build
```

#### 5. "No connected devices"

**Solution:** Connect device or start emulator.

```bash
# Check connected devices
adb devices

# Start an emulator
emulator -avd Your_AVD_Name
```

#### 6. Build fails with "Unsupported Java version"

**Solution:** Ensure you're using JDK 11 or later.

```bash
# Check Java version
java -version

# Update JAVA_HOME to point to correct JDK
export JAVA_HOME=/path/to/jdk11
```

#### 7. "Execution failed for task ':app:lint'"

**Solution:** Fix lint errors or disable lint temporarily.

```bash
# Run with lint warnings as info
./gradlew assembleDebug -x lint

# Or fix issues shown in lint report
cat app/build/reports/lint/lint-results.txt
```

### Build Output Locations

| Build Type | Output Location |
|------------|----------------|
| Debug APK | `app/build/outputs/apk/debug/app-debug.apk` |
| Release APK | `app/build/outputs/apk/release/app-release.apk` |
| Test Reports | `app/build/reports/tests/` |
| Lint Reports | `app/build/reports/lint/` |
| Build Logs | `app/build/outputs/logs/` |

### Getting More Information

#### Verbose Build Output

```bash
# Run with info logging
./gradlew assembleDebug --info

# Run with debug logging
./gradlew assembleDebug --debug

# Run with stack trace
./gradlew assembleDebug --stacktrace
```

#### Check Build Configuration

```bash
# Show project properties
./gradlew properties

# Show dependencies
./gradlew app:dependencies

# Show dependency insights
./gradlew app:dependencyInsight --dependency <dependency-name>
```

## Release Builds

### Signing Configuration

For production release builds, you need to configure signing:

1. **Create a keystore:**

```bash
keytool -genkey -v -keystore time-reading.keystore -alias time-reading -keyalg RSA -keysize 2048 -validity 10000
```

2. **Configure signing in `app/build.gradle`:**

```gradle
android {
    signingConfigs {
        release {
            storeFile file("../time-reading.keystore")
            storePassword "your-store-password"
            keyAlias "time-reading"
            keyPassword "your-key-password"
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

3. **Build signed release:**

```bash
./build.sh release
```

**Security Note:** Never commit keystores or passwords to version control. Use environment variables or gradle.properties (excluded from git).

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/build.yml`:

```yaml
name: Android Build

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 11
      uses: actions/setup-java@v3
      with:
        java-version: '11'
        distribution: 'adopt'
    
    - name: Grant execute permission
      run: chmod +x gradlew build.sh verify-build.sh
    
    - name: Build with Gradle
      run: ./build.sh debug
    
    - name: Verify Build
      run: ./verify-build.sh
    
    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: app-debug
        path: app/build/outputs/apk/debug/app-debug.apk
```

## Additional Resources

- [Android Developer Guide](https://developer.android.com/guide)
- [Gradle User Manual](https://docs.gradle.org/current/userguide/userguide.html)
- [CameraX Documentation](https://developer.android.com/training/camerax)
- [TensorFlow Lite for Android](https://www.tensorflow.org/lite/android)

## Support

For issues or questions:
1. Check this build guide
2. Review the troubleshooting section
3. Check project README.md and ARCHITECTURE.md
4. Create an issue on GitHub

---

**Last Updated:** January 2026
