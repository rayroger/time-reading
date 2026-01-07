# Build Quick Reference

Quick reference for building and verifying the Time Reading Android app.

## Essential Commands

### Build Commands
```bash
./build.sh debug              # Build debug APK
./build.sh release            # Build release APK
./build.sh clean              # Clean build artifacts
./build.sh all                # Clean, build, and test
```

### Verification
```bash
./verify-build.sh             # Verify debug build
./verify-build.sh --all       # Verify both debug and release
./verify-build.sh --strict    # Strict mode (warnings = failures)
```

### Testing
```bash
./build.sh test               # Run unit tests
./build.sh lint               # Run lint checks
```

### Installation
```bash
./build.sh install            # Install debug APK on device
./build.sh installRelease     # Install release APK on device
```

## Direct Gradle Commands

```bash
./gradlew tasks               # List all available tasks
./gradlew assembleDebug       # Build debug APK
./gradlew assembleRelease     # Build release APK
./gradlew test                # Run unit tests
./gradlew lint                # Run lint checks
./gradlew clean               # Clean project
./gradlew build               # Full build with tests
```

## Build Outputs

| Type | Location |
|------|----------|
| Debug APK | `app/build/outputs/apk/debug/app-debug.apk` |
| Release APK | `app/build/outputs/apk/release/app-release.apk` |
| Test Reports | `app/build/reports/tests/` |
| Lint Reports | `app/build/reports/lint/` |

## Common Workflows

### First Time Build
```bash
./build.sh debug
./verify-build.sh
```

### Development Cycle
```bash
./build.sh clean debug
./verify-build.sh
./build.sh install
```

### Full Validation
```bash
./build.sh all
./verify-build.sh --all --strict
```

### Release Build
```bash
./build.sh clean release
./verify-build.sh --release
```

## Troubleshooting Quick Fixes

```bash
# Clear Gradle cache
./gradlew clean --refresh-dependencies

# Make scripts executable
chmod +x build.sh verify-build.sh

# Check environment
java -version
echo $ANDROID_HOME
```

For detailed documentation, see [BUILD.md](BUILD.md).
