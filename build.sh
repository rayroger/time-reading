#!/bin/bash

################################################################################
# Time Reading Android App - Build Script
# 
# This script provides a convenient way to build the Time Reading Android
# application with various options and configurations.
#
# Usage:
#   ./build.sh [COMMAND] [OPTIONS]
#
# Commands:
#   clean          - Clean build artifacts
#   debug          - Build debug APK
#   release        - Build release APK (requires signing configuration)
#   assemble       - Assemble all variants
#   test           - Run unit tests
#   install        - Install debug APK on connected device
#   installRelease - Install release APK on connected device
#   lint           - Run lint checks
#   all            - Clean, build, and test
#   help           - Show this help message
#
# Examples:
#   ./build.sh debug
#   ./build.sh clean debug
#   ./build.sh test
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

################################################################################
# Check Prerequisites
################################################################################

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check for Java
    if ! command -v java &> /dev/null; then
        print_error "Java is not installed or not in PATH"
        print_info "Please install Java JDK 17 or later"
        exit 1
    else
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
        print_success "Java found: $JAVA_VERSION"
    fi
    
    # Check for Gradle wrapper
    if [ ! -f "./gradlew" ]; then
        print_error "Gradle wrapper (gradlew) not found"
        exit 1
    else
        print_success "Gradle wrapper found"
        chmod +x ./gradlew
    fi
    
    # Check for Android SDK (optional check)
    if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
        print_warning "ANDROID_HOME or ANDROID_SDK_ROOT not set"
        print_info "The build may fail if Android SDK is not properly configured"
    else
        print_success "Android SDK configured"
    fi
}

################################################################################
# Build Commands
################################################################################

cmd_clean() {
    print_header "Cleaning Build Artifacts"
    ./gradlew clean
    print_success "Clean completed"
}

cmd_debug() {
    print_header "Building Debug APK"
    ./gradlew assembleDebug
    
    if [ -f "app/build/outputs/apk/debug/app-debug.apk" ]; then
        print_success "Debug APK built successfully"
        print_info "Location: app/build/outputs/apk/debug/app-debug.apk"
        ls -lh app/build/outputs/apk/debug/app-debug.apk
    else
        print_error "Debug APK not found"
        exit 1
    fi
}

cmd_release() {
    print_header "Building Release APK"
    
    print_warning "Note: Release builds require proper signing configuration"
    print_info "Ensure you have configured signing in app/build.gradle or via gradle.properties"
    
    ./gradlew assembleRelease
    
    if [ -f "app/build/outputs/apk/release/app-release.apk" ] || \
       [ -f "app/build/outputs/apk/release/app-release-unsigned.apk" ]; then
        print_success "Release APK built successfully"
        print_info "Location: app/build/outputs/apk/release/"
        ls -lh app/build/outputs/apk/release/*.apk 2>/dev/null || true
    else
        print_error "Release APK not found"
        exit 1
    fi
}

cmd_assemble() {
    print_header "Assembling All Variants"
    ./gradlew assemble
    print_success "All variants assembled"
}

cmd_test() {
    print_header "Running Unit Tests"
    ./gradlew test
    
    print_success "Unit tests completed"
    print_info "Test reports: app/build/reports/tests/"
}

cmd_lint() {
    print_header "Running Lint Checks"
    ./gradlew lint
    
    print_success "Lint checks completed"
    print_info "Lint reports: app/build/reports/lint/"
}

cmd_install() {
    print_header "Installing Debug APK"
    
    # Check if device is connected
    if ! command -v adb &> /dev/null; then
        print_error "adb not found. Please ensure Android SDK platform-tools are in PATH"
        exit 1
    fi
    
    DEVICES=$(adb devices | grep -v "List" | grep "device$" | wc -l)
    if [ "$DEVICES" -eq 0 ]; then
        print_error "No Android device connected"
        print_info "Please connect a device or start an emulator"
        exit 1
    fi
    
    print_info "Installing to connected device(s)..."
    ./gradlew installDebug
    print_success "Debug APK installed"
}

cmd_install_release() {
    print_header "Installing Release APK"
    
    # Check if device is connected
    if ! command -v adb &> /dev/null; then
        print_error "adb not found. Please ensure Android SDK platform-tools are in PATH"
        exit 1
    fi
    
    DEVICES=$(adb devices | grep -v "List" | grep "device$" | wc -l)
    if [ "$DEVICES" -eq 0 ]; then
        print_error "No Android device connected"
        print_info "Please connect a device or start an emulator"
        exit 1
    fi
    
    print_info "Installing to connected device(s)..."
    ./gradlew installRelease
    print_success "Release APK installed"
}

cmd_all() {
    print_header "Complete Build and Test"
    cmd_clean
    cmd_debug
    cmd_test
    print_success "All build steps completed successfully!"
}

cmd_help() {
    cat << EOF

${BLUE}Time Reading Android App - Build Script${NC}

${YELLOW}Usage:${NC}
  ./build.sh [COMMAND] [OPTIONS]

${YELLOW}Commands:${NC}
  clean          - Clean build artifacts
  debug          - Build debug APK
  release        - Build release APK (requires signing configuration)
  assemble       - Assemble all variants
  test           - Run unit tests
  install        - Install debug APK on connected device
  installRelease - Install release APK on connected device
  lint           - Run lint checks
  all            - Clean, build, and test
  help           - Show this help message

${YELLOW}Examples:${NC}
  ./build.sh debug              # Build debug APK
  ./build.sh clean debug        # Clean then build debug
  ./build.sh test               # Run unit tests
  ./build.sh all                # Full build and test cycle
  ./build.sh install            # Install debug APK on device

${YELLOW}Requirements:${NC}
  - Java JDK 17 or later
  - Android SDK (ANDROID_HOME or ANDROID_SDK_ROOT set)
  - For installation: Connected Android device or emulator

${YELLOW}Build Outputs:${NC}
  - Debug APK:   app/build/outputs/apk/debug/app-debug.apk
  - Release APK: app/build/outputs/apk/release/app-release.apk
  - Test reports: app/build/reports/tests/
  - Lint reports: app/build/reports/lint/

EOF
}

################################################################################
# Main Script Logic
################################################################################

main() {
    # Show help if no arguments
    if [ "$#" -eq 0 ]; then
        cmd_help
        exit 0
    fi
    
    # Check prerequisites once
    check_prerequisites
    
    # Process commands
    for cmd in "$@"; do
        case "$cmd" in
            clean)
                cmd_clean
                ;;
            debug)
                cmd_debug
                ;;
            release)
                cmd_release
                ;;
            assemble)
                cmd_assemble
                ;;
            test)
                cmd_test
                ;;
            lint)
                cmd_lint
                ;;
            install)
                cmd_install
                ;;
            installRelease)
                cmd_install_release
                ;;
            all)
                cmd_all
                ;;
            help|--help|-h)
                cmd_help
                ;;
            *)
                print_error "Unknown command: $cmd"
                print_info "Run './build.sh help' for usage information"
                exit 1
                ;;
        esac
    done
    
    echo ""
    print_success "Build script completed successfully!"
}

# Run main function
main "$@"
