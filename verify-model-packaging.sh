#!/bin/bash
# Script to verify that TFLite models are properly packaged in the APK

set -e

echo "=========================================="
echo "Model Packaging Verification Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# 1. Check if model exists in assets
echo "1. Checking model in assets directory..."
if [ -f "app/src/main/assets/watch_detector.tflite" ]; then
    SIZE=$(stat -f%z "app/src/main/assets/watch_detector.tflite" 2>/dev/null || stat -c%s "app/src/main/assets/watch_detector.tflite" 2>/dev/null)
    print_status 0 "Model file exists (${SIZE} bytes)"
else
    print_status 1 "Model file NOT found in app/src/main/assets/"
    exit 1
fi

# 2. Check build.gradle configuration
echo ""
echo "2. Checking build.gradle configuration..."
if grep -q 'noCompress "tflite"' app/build.gradle; then
    print_status 0 "aaptOptions configured correctly"
else
    print_status 1 "aaptOptions 'noCompress \"tflite\"' not found in build.gradle"
fi

# 3. Check TensorFlow Lite dependencies
echo ""
echo "3. Checking TensorFlow Lite dependencies..."
if grep -q "tensorflow-lite:" app/build.gradle; then
    print_status 0 "TensorFlow Lite dependency found"
else
    print_status 1 "TensorFlow Lite dependency NOT found"
fi

if grep -q "tensorflow-lite-gpu:" app/build.gradle; then
    print_status 0 "TensorFlow Lite GPU dependency found"
else
    print_status 1 "TensorFlow Lite GPU dependency NOT found"
fi

# 4. Build the APK if requested
if [ "$1" = "--build" ]; then
    echo ""
    echo "4. Building debug APK..."
    ./gradlew assembleDebug
    APK_BUILT=$?
    print_status $APK_BUILT "APK build"
    
    if [ $APK_BUILT -eq 0 ]; then
        # 5. Verify model in APK
        echo ""
        echo "5. Verifying model in APK..."
        APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
        
        if [ -f "$APK_PATH" ]; then
            if unzip -l "$APK_PATH" | grep -q "watch_detector.tflite"; then
                # Get the size from the APK
                SIZE_IN_APK=$(unzip -l "$APK_PATH" | grep "watch_detector.tflite" | awk '{print $1}')
                print_status 0 "Model found in APK (${SIZE_IN_APK} bytes)"
                
                # Compare sizes
                if [ "$SIZE" = "$SIZE_IN_APK" ]; then
                    print_status 0 "Model size matches (no compression)"
                else
                    print_status 1 "Model size mismatch - may be compressed"
                fi
            else
                print_status 1 "Model NOT found in APK"
            fi
        else
            print_status 1 "APK file not found at $APK_PATH"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "Verification Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  - Run with --build flag to build and verify APK:"
echo "    ./verify-model-packaging.sh --build"
echo "  - Install on device: adb install app/build/outputs/apk/debug/app-debug.apk"
echo "  - Check logs: adb logcat | grep WatchDialAnalyzer"
