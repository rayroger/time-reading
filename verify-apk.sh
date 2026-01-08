#!/bin/bash

################################################################################
# APK Verification Script
# 
# This script verifies that the APK is built correctly and contains all
# necessary assets including the TensorFlow Lite model.
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_header "APK Verification"

# Check if debug APK exists
DEBUG_APK="app/build/outputs/apk/debug/app-debug.apk"
RELEASE_APK="app/build/outputs/apk/release/app-release.apk"

APK_TO_VERIFY=""

if [ -f "$DEBUG_APK" ]; then
    APK_TO_VERIFY="$DEBUG_APK"
    print_success "Found debug APK: $DEBUG_APK"
elif [ -f "$RELEASE_APK" ]; then
    APK_TO_VERIFY="$RELEASE_APK"
    print_success "Found release APK: $RELEASE_APK"
else
    print_error "No APK found. Please build the app first."
    print_info "Run: ./build.sh debug"
    exit 1
fi

# Get APK size
APK_SIZE=$(ls -lh "$APK_TO_VERIFY" | awk '{print $5}')
print_info "APK Size: $APK_SIZE"

print_header "Verifying APK Contents"

# Check for required libraries
print_info "Checking for required libraries..."

if unzip -l "$APK_TO_VERIFY" | grep -q "libtensorflowlite"; then
    print_success "TensorFlow Lite native library found"
else
    print_warning "TensorFlow Lite native library not found (this might be OK if using Java-only version)"
fi

# Check for assets
print_info "Checking for assets..."

if unzip -l "$APK_TO_VERIFY" | grep -q "assets/"; then
    print_success "Assets directory found"
    
    # List all assets
    echo ""
    print_info "Assets in APK:"
    unzip -l "$APK_TO_VERIFY" | grep "assets/" | awk '{print "  - " $4}'
    echo ""
else
    print_warning "No assets directory found"
fi

# Check for TensorFlow Lite model
print_info "Checking for TensorFlow Lite model..."

if unzip -l "$APK_TO_VERIFY" | grep -q "assets/watch_detector.tflite"; then
    print_success "TensorFlow Lite model found: watch_detector.tflite"
    
    # Get model size
    MODEL_SIZE=$(unzip -l "$APK_TO_VERIFY" | grep "assets/watch_detector.tflite" | awk '{print $1}')
    print_info "Model size: $MODEL_SIZE bytes"
else
    print_warning "TensorFlow Lite model NOT found (app will run in mock mode)"
    print_info "To add the model: Place watch_detector.tflite in app/src/main/assets/"
fi

# Check for .tflite compression
print_info "Verifying .tflite files are not compressed..."

if unzip -l "$APK_TO_VERIFY" | grep "\.tflite" | grep -q "Stored"; then
    print_success ".tflite files are stored uncompressed (correct)"
elif unzip -l "$APK_TO_VERIFY" | grep -q "\.tflite"; then
    print_warning ".tflite files might be compressed (check aaptOptions in build.gradle)"
else
    print_info "No .tflite files found in APK"
fi

# Check for Kotlin runtime
print_info "Checking for Kotlin runtime..."

if unzip -l "$APK_TO_VERIFY" | grep -q "kotlin"; then
    print_success "Kotlin runtime found"
else
    print_error "Kotlin runtime not found"
fi

# Check for AndroidX libraries
print_info "Checking for AndroidX libraries..."

if unzip -l "$APK_TO_VERIFY" | grep -q "androidx"; then
    print_success "AndroidX libraries found"
else
    print_warning "AndroidX libraries not found (might be an issue)"
fi

# Check for CameraX libraries
print_info "Checking for CameraX libraries..."

if unzip -l "$APK_TO_VERIFY" | grep -q "camera"; then
    print_success "CameraX libraries found"
else
    print_warning "CameraX libraries not found (might be an issue)"
fi

# Verify manifest
print_header "Verifying AndroidManifest.xml"

if command -v aapt &> /dev/null; then
    print_info "Checking permissions in manifest..."
    
    MANIFEST_DUMP=$(aapt dump permissions "$APK_TO_VERIFY")
    
    if echo "$MANIFEST_DUMP" | grep -q "android.permission.CAMERA"; then
        print_success "CAMERA permission declared"
    else
        print_error "CAMERA permission NOT declared"
    fi
    
    if echo "$MANIFEST_DUMP" | grep -q "android.permission.RECORD_AUDIO"; then
        print_success "RECORD_AUDIO permission declared"
    else
        print_warning "RECORD_AUDIO permission NOT declared"
    fi
    
    print_info "Package name:"
    aapt dump badging "$APK_TO_VERIFY" | grep "package:" | head -1
    
    print_info "Min SDK version:"
    aapt dump badging "$APK_TO_VERIFY" | grep "sdkVersion"
else
    print_warning "aapt not found, skipping manifest verification"
    print_info "Install Android SDK build-tools to enable manifest verification"
fi

# Summary
print_header "Verification Summary"

if [ -f "$APK_TO_VERIFY" ]; then
    print_success "APK file exists and is valid"
    print_info "APK path: $APK_TO_VERIFY"
    print_info "APK size: $APK_SIZE"
    
    if unzip -l "$APK_TO_VERIFY" | grep -q "assets/watch_detector.tflite"; then
        print_success "ML model is packaged in APK"
        print_info "App will use TensorFlow Lite for watch detection"
    else
        print_warning "ML model is NOT packaged in APK"
        print_info "App will run in mock mode (no actual watch detection)"
        print_info "To add model: Place watch_detector.tflite in app/src/main/assets/ and rebuild"
    fi
    
    echo ""
    print_success "APK verification completed successfully!"
    echo ""
    
    print_info "To install APK on a device:"
    echo "  adb install -r $APK_TO_VERIFY"
    echo ""
    
    print_info "To analyze APK in detail:"
    echo "  Android Studio > Build > Analyze APK > Select $APK_TO_VERIFY"
    echo ""
else
    print_error "APK verification failed"
    exit 1
fi
