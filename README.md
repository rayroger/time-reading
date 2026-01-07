# time-reading

Android based clock reading using camera

## Quick Start

### Building the App

```bash
# Build debug APK
./build.sh debug

# Verify the build
./verify-build.sh

# Install on device
./build.sh install
```

For detailed build instructions, see [BUILD.md](BUILD.md).

### Documentation

- **[BUILD.md](BUILD.md)** - Comprehensive build guide with all commands and troubleshooting
- **[APP_README.md](APP_README.md)** - Application features and usage guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and ML integration details

## Build Scripts

This project includes automated build and verification scripts:

- `build.sh` - Build the app with various options (debug, release, test, install)
- `verify-build.sh` - Verify build outputs and validate project configuration

Run `./build.sh help` or `./verify-build.sh --help` for usage information.
