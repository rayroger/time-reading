#!/bin/bash

################################################################################
# Time Reading Android App - Build Verification Script
# 
# This script verifies that the build was successful and validates the
# application structure, configuration, and outputs.
#
# Usage:
#   ./verify-build.sh [OPTIONS]
#
# Options:
#   --debug        - Verify debug build only (default)
#   --release      - Verify release build only
#   --all          - Verify both debug and release builds
#   --strict       - Enable strict mode (fail on warnings)
#   --help         - Show this help message
#
# Examples:
#   ./verify-build.sh
#   ./verify-build.sh --all
#   ./verify-build.sh --release --strict
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Counters for test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNING=0
TESTS_TOTAL=0

# Configuration
STRICT_MODE=false
VERIFY_DEBUG=true
VERIFY_RELEASE=false

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_section() {
    echo -e "\n${CYAN}--- $1 ---${NC}"
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

get_file_size_mb() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo "N/A"
        return
    fi
    
    # Try to get file size in bytes using portable method
    local size=$(wc -c < "$file" 2>/dev/null | tr -d ' ')
    
    if [ -n "$size" ] && [ "$size" -gt 0 ]; then
        # Use shell arithmetic for division (result in MB with 2 decimal places)
        # Convert to MB: bytes / 1048576
        local mb=$((size / 1048576))
        local remainder=$((size % 1048576))
        local decimal=$((remainder * 100 / 1048576))
        printf "%d.%02d" "$mb" "$decimal"
    else
        echo "N/A"
    fi
}

test_passed() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    print_success "$1"
}

test_failed() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    print_error "$1"
}

test_warning() {
    TESTS_WARNING=$((TESTS_WARNING + 1))
    print_warning "$1"
    if [ "$STRICT_MODE" = true ]; then
        TESTS_FAILED=$((TESTS_FAILED + 1))
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
    else
        TESTS_TOTAL=$((TESTS_TOTAL + 1))
    fi
}

################################################################################
# Verification Tests
################################################################################

verify_prerequisites() {
    print_section "Verifying Prerequisites"
    
    # Check for Java
    if command -v java &> /dev/null; then
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
        test_passed "Java is installed: $JAVA_VERSION"
    else
        test_failed "Java is not installed or not in PATH"
    fi
    
    # Check for Gradle wrapper
    if [ -f "./gradlew" ] && [ -x "./gradlew" ]; then
        test_passed "Gradle wrapper is present and executable"
    else
        test_failed "Gradle wrapper is missing or not executable"
    fi
    
    # Check for Android SDK
    if [ -n "$ANDROID_HOME" ] || [ -n "$ANDROID_SDK_ROOT" ]; then
        test_passed "Android SDK environment variable is set"
    else
        test_warning "ANDROID_HOME/ANDROID_SDK_ROOT not set (may cause build issues)"
    fi
    
    # Check for adb
    if command -v adb &> /dev/null; then
        ADB_VERSION=$(adb version | head -n 1)
        test_passed "adb is available: $ADB_VERSION"
    else
        test_warning "adb not found (device installation will not be available)"
    fi
}

verify_project_structure() {
    print_section "Verifying Project Structure"
    
    # Check root build.gradle
    if [ -f "build.gradle" ]; then
        test_passed "Root build.gradle exists"
    else
        test_failed "Root build.gradle is missing"
    fi
    
    # Check settings.gradle
    if [ -f "settings.gradle" ]; then
        test_passed "settings.gradle exists"
    else
        test_failed "settings.gradle is missing"
    fi
    
    # Check app module
    if [ -d "app" ]; then
        test_passed "app module directory exists"
    else
        test_failed "app module directory is missing"
    fi
    
    # Check app build.gradle
    if [ -f "app/build.gradle" ]; then
        test_passed "app/build.gradle exists"
    else
        test_failed "app/build.gradle is missing"
    fi
    
    # Check AndroidManifest.xml
    if [ -f "app/src/main/AndroidManifest.xml" ]; then
        test_passed "AndroidManifest.xml exists"
    else
        test_failed "AndroidManifest.xml is missing"
    fi
    
    # Check for source files
    if [ -d "app/src/main/java" ] || [ -d "app/src/main/kotlin" ]; then
        SOURCE_COUNT=$(find app/src/main -name "*.kt" -o -name "*.java" 2>/dev/null | wc -l)
        if [ "$SOURCE_COUNT" -gt 0 ]; then
            test_passed "Source files found: $SOURCE_COUNT files"
        else
            test_warning "No Kotlin/Java source files found"
        fi
    else
        test_failed "Source directory is missing"
    fi
    
    # Check for resources
    if [ -d "app/src/main/res" ]; then
        test_passed "Resources directory exists"
        
        # Check for layouts
        if [ -d "app/src/main/res/layout" ]; then
            LAYOUT_COUNT=$(find app/src/main/res/layout -name "*.xml" 2>/dev/null | wc -l)
            test_passed "Layout files found: $LAYOUT_COUNT files"
        else
            test_warning "No layout directory found"
        fi
    else
        test_failed "Resources directory is missing"
    fi
}

verify_gradle_configuration() {
    print_section "Verifying Gradle Configuration"
    
    # Check build.gradle content
    if grep -q "com.android.application" app/build.gradle; then
        test_passed "Android application plugin configured"
    else
        test_failed "Android application plugin not found in app/build.gradle"
    fi
    
    # Check for Kotlin plugin
    if grep -q "kotlin" app/build.gradle; then
        test_passed "Kotlin plugin configured"
    else
        test_warning "Kotlin plugin not found (may be Java-only project)"
    fi
    
    # Check namespace/applicationId
    if grep -q "namespace\|applicationId" app/build.gradle; then
        test_passed "Application ID/namespace configured"
    else
        test_failed "Application ID/namespace not found"
    fi
    
    # Check compileSdk
    if grep -q "compileSdk" app/build.gradle; then
        COMPILE_SDK=$(grep "compileSdk" app/build.gradle | head -n 1 | grep -oP '\d+' | head -n 1)
        if [ -n "$COMPILE_SDK" ] && [ "$COMPILE_SDK" -ge 24 ]; then
            test_passed "compileSdk configured: API $COMPILE_SDK"
        else
            test_warning "compileSdk may be too low: API $COMPILE_SDK"
        fi
    else
        test_failed "compileSdk not specified"
    fi
    
    # Check minSdk
    if grep -q "minSdk" app/build.gradle; then
        MIN_SDK=$(grep "minSdk" app/build.gradle | head -n 1 | grep -oP '\d+' | head -n 1)
        test_passed "minSdk configured: API $MIN_SDK"
    else
        test_warning "minSdk not specified"
    fi
    
    # Check for dependencies
    if grep -q "dependencies {" app/build.gradle; then
        DEP_COUNT=$(grep -c "implementation\|api\|compileOnly" app/build.gradle 2>/dev/null || echo "0")
        test_passed "Dependencies configured: ~$DEP_COUNT dependencies"
    else
        test_warning "No dependencies section found"
    fi
}

verify_debug_build() {
    print_section "Verifying Debug Build"
    
    DEBUG_APK="app/build/outputs/apk/debug/app-debug.apk"
    
    if [ -f "$DEBUG_APK" ]; then
        test_passed "Debug APK exists"
        
        # Check file size
        APK_SIZE_MB=$(get_file_size_mb "$DEBUG_APK")
        test_passed "Debug APK size: ${APK_SIZE_MB} MB"
        
        # Check if APK is valid (basic check)
        if file "$DEBUG_APK" | grep -qE "Zip archive|Java archive|Android"; then
            test_passed "Debug APK is a valid archive"
        elif unzip -t "$DEBUG_APK" >/dev/null 2>&1; then
            test_passed "Debug APK is a valid archive"
        else
            test_failed "Debug APK may be corrupted"
        fi
        
        # Try to extract APK information using aapt if available
        if command -v aapt &> /dev/null; then
            print_info "Analyzing APK with aapt..."
            
            # Get package name
            PACKAGE=$(aapt dump badging "$DEBUG_APK" 2>/dev/null | grep "package:" | sed "s/.*name='\([^']*\)'.*/\1/")
            if [ -n "$PACKAGE" ]; then
                test_passed "Package name: $PACKAGE"
            else
                test_warning "Could not extract package name"
            fi
            
            # Get version
            VERSION=$(aapt dump badging "$DEBUG_APK" 2>/dev/null | grep "versionName" | sed "s/.*versionName='\([^']*\)'.*/\1/")
            if [ -n "$VERSION" ]; then
                test_passed "Version: $VERSION"
            else
                test_warning "Could not extract version"
            fi
            
            # Check for required permissions
            PERMS=$(aapt dump badging "$DEBUG_APK" 2>/dev/null | grep "uses-permission" | wc -l)
            test_passed "Permissions declared: $PERMS"
            
        else
            test_warning "aapt not available - skipping APK analysis"
        fi
        
        # Check AndroidManifest.xml exists in APK
        if unzip -l "$DEBUG_APK" 2>/dev/null | grep -q "AndroidManifest.xml"; then
            test_passed "AndroidManifest.xml found in APK"
        else
            test_failed "AndroidManifest.xml not found in APK"
        fi
        
        # Check for DEX files
        DEX_COUNT=$(unzip -l "$DEBUG_APK" 2>/dev/null | grep -c "\.dex$" || echo "0")
        if [ "$DEX_COUNT" -gt 0 ]; then
            test_passed "DEX files found in APK: $DEX_COUNT files"
        else
            test_failed "No DEX files found in APK"
        fi
        
        # Check for resources
        if unzip -l "$DEBUG_APK" 2>/dev/null | grep -q "resources.arsc"; then
            test_passed "Resources compiled into APK"
        else
            test_warning "No compiled resources found"
        fi
        
    else
        test_failed "Debug APK not found at $DEBUG_APK"
        print_info "Run './build.sh debug' to build the debug APK"
    fi
}

verify_release_build() {
    print_section "Verifying Release Build"
    
    RELEASE_APK="app/build/outputs/apk/release/app-release.apk"
    RELEASE_UNSIGNED="app/build/outputs/apk/release/app-release-unsigned.apk"
    
    if [ -f "$RELEASE_APK" ]; then
        test_passed "Release APK exists (signed)"
        
        # Check file size
        APK_SIZE_MB=$(get_file_size_mb "$RELEASE_APK")
        test_passed "Release APK size: ${APK_SIZE_MB} MB"
        
        # Check if APK is valid
        if file "$RELEASE_APK" | grep -q "Zip archive"; then
            test_passed "Release APK is a valid archive"
        else
            test_failed "Release APK may be corrupted"
        fi
        
    elif [ -f "$RELEASE_UNSIGNED" ]; then
        test_warning "Release APK exists but is unsigned"
        print_info "Configure signing in app/build.gradle for production release"
    else
        test_warning "Release APK not found (this is normal if not built)"
        print_info "Run './build.sh release' to build the release APK"
    fi
}

verify_tests() {
    print_section "Verifying Test Configuration"
    
    # Check for test directories
    if [ -d "app/src/test" ]; then
        TEST_COUNT=$(find app/src/test -name "*.kt" -o -name "*.java" 2>/dev/null | wc -l)
        if [ "$TEST_COUNT" -gt 0 ]; then
            test_passed "Unit tests found: $TEST_COUNT test files"
        else
            test_warning "Test directory exists but no test files found"
        fi
    else
        test_warning "No unit test directory (app/src/test)"
    fi
    
    # Check for instrumented tests
    if [ -d "app/src/androidTest" ]; then
        ANDROID_TEST_COUNT=$(find app/src/androidTest -name "*.kt" -o -name "*.java" 2>/dev/null | wc -l)
        if [ "$ANDROID_TEST_COUNT" -gt 0 ]; then
            test_passed "Instrumented tests found: $ANDROID_TEST_COUNT test files"
        else
            test_warning "androidTest directory exists but no test files found"
        fi
    else
        test_warning "No instrumented test directory (app/src/androidTest)"
    fi
    
    # Check test dependencies
    if grep -q "testImplementation\|androidTestImplementation" app/build.gradle; then
        test_passed "Test dependencies configured in build.gradle"
    else
        test_warning "No test dependencies found in build.gradle"
    fi
    
    # Check for test reports
    if [ -d "app/build/reports/tests" ]; then
        test_passed "Test reports directory exists"
    else
        print_info "Test reports not found (tests may not have been run)"
    fi
}

verify_lint_results() {
    print_section "Verifying Lint Configuration"
    
    # Check for lint reports
    if [ -d "app/build/reports/lint" ]; then
        test_passed "Lint reports directory exists"
        
        # Check for lint results file
        if [ -f "app/build/reports/lint/lint-results.xml" ] || \
           [ -f "app/build/reports/lint-results.xml" ]; then
            test_passed "Lint results file found"
            
            # Parse lint results if available
            LINT_FILE=$(find app/build/reports -name "lint-results.xml" 2>/dev/null | head -n 1)
            if [ -f "$LINT_FILE" ]; then
                ERRORS=$(grep -o '<issue[^>]*severity="Error"' "$LINT_FILE" 2>/dev/null | wc -l || echo "0")
                WARNINGS=$(grep -o '<issue[^>]*severity="Warning"' "$LINT_FILE" 2>/dev/null | wc -l || echo "0")
                
                if [ "$ERRORS" -eq 0 ]; then
                    test_passed "Lint errors: 0"
                else
                    test_warning "Lint errors found: $ERRORS"
                fi
                
                if [ "$WARNINGS" -eq 0 ]; then
                    test_passed "Lint warnings: 0"
                else
                    print_info "Lint warnings found: $WARNINGS"
                fi
            fi
        else
            print_info "Lint results not found (lint may not have been run)"
        fi
    else
        print_info "Lint reports directory not found (lint may not have been run)"
        print_info "Run './build.sh lint' to generate lint reports"
    fi
}

verify_build_cache() {
    print_section "Verifying Build Cache"
    
    # Check .gradle directory
    if [ -d ".gradle" ]; then
        test_passed "Gradle cache directory exists"
    else
        print_info "Gradle cache not found (first build)"
    fi
    
    # Check build directory
    if [ -d "app/build" ]; then
        test_passed "Build output directory exists"
        
        # Check intermediates
        if [ -d "app/build/intermediates" ]; then
            test_passed "Build intermediates directory exists"
        fi
        
        # Check generated sources
        if [ -d "app/build/generated" ]; then
            test_passed "Generated sources directory exists"
        fi
    else
        test_warning "Build directory not found (project may not have been built)"
    fi
}

verify_assets_resources() {
    print_section "Verifying Assets and Resources"
    
    # Check for assets
    if [ -d "app/src/main/assets" ]; then
        ASSET_COUNT=$(find app/src/main/assets -type f 2>/dev/null | wc -l)
        if [ "$ASSET_COUNT" -gt 0 ]; then
            test_passed "Assets found: $ASSET_COUNT files"
            
            # Check for ML models specifically mentioned in architecture
            if [ -f "app/src/main/assets/watch_detector.tflite" ]; then
                MODEL_SIZE_MB=$(get_file_size_mb "app/src/main/assets/watch_detector.tflite")
                test_passed "TensorFlow Lite model found: ${MODEL_SIZE_MB} MB"
            else
                print_info "TensorFlow Lite model not found (see MODEL_README.md for details)"
            fi
        else
            print_info "Assets directory exists but is empty"
        fi
    else
        print_info "No assets directory (this may be normal)"
    fi
    
    # Check for drawable resources
    if [ -d "app/src/main/res/drawable" ] || \
       [ -d "app/src/main/res/drawable-v24" ] || \
       [ -d "app/src/main/res/mipmap-hdpi" ]; then
        test_passed "Drawable resources found"
    else
        test_warning "No drawable resources found"
    fi
    
    # Check for string resources
    if [ -f "app/src/main/res/values/strings.xml" ]; then
        test_passed "String resources found"
    else
        test_warning "strings.xml not found"
    fi
    
    # Check for theme resources
    if [ -f "app/src/main/res/values/themes.xml" ] || \
       [ -f "app/src/main/res/values/styles.xml" ]; then
        test_passed "Theme/style resources found"
    else
        test_warning "No theme/style resources found"
    fi
}

################################################################################
# Summary and Reporting
################################################################################

print_summary() {
    print_header "Build Verification Summary"
    
    echo -e "${CYAN}Total Tests:${NC} $TESTS_TOTAL"
    echo -e "${GREEN}Passed:${NC}      $TESTS_PASSED"
    echo -e "${RED}Failed:${NC}      $TESTS_FAILED"
    echo -e "${YELLOW}Warnings:${NC}    $TESTS_WARNING"
    echo ""
    
    PASS_RATE=0
    if [ "$TESTS_TOTAL" -gt 0 ]; then
        PASS_RATE=$(( TESTS_PASSED * 100 / TESTS_TOTAL ))
    fi
    
    echo -e "${CYAN}Pass Rate:${NC}   ${PASS_RATE}%"
    echo ""
    
    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✓ BUILD VERIFICATION PASSED          ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        echo ""
        
        if [ "$TESTS_WARNING" -gt 0 ]; then
            print_warning "$TESTS_WARNING warning(s) found - review recommended"
        fi
        
        return 0
    else
        echo -e "${RED}╔════════════════════════════════════════╗${NC}"
        echo -e "${RED}║  ✗ BUILD VERIFICATION FAILED           ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════╝${NC}"
        echo ""
        print_error "$TESTS_FAILED test(s) failed"
        
        return 1
    fi
}

################################################################################
# Main Script Logic
################################################################################

show_help() {
    cat << EOF

${BLUE}Time Reading Android App - Build Verification Script${NC}

${YELLOW}Usage:${NC}
  ./verify-build.sh [OPTIONS]

${YELLOW}Options:${NC}
  --debug        - Verify debug build only (default)
  --release      - Verify release build only
  --all          - Verify both debug and release builds
  --strict       - Enable strict mode (warnings count as failures)
  --help         - Show this help message

${YELLOW}Examples:${NC}
  ./verify-build.sh              # Verify debug build
  ./verify-build.sh --all        # Verify both builds
  ./verify-build.sh --release    # Verify release build only
  ./verify-build.sh --all --strict  # Strict verification of both builds

${YELLOW}Verification Steps:${NC}
  1. Prerequisites (Java, Gradle, Android SDK)
  2. Project structure validation
  3. Gradle configuration checks
  4. Build output verification (APK analysis)
  5. Test configuration validation
  6. Lint results review
  7. Build cache verification
  8. Assets and resources validation

${YELLOW}Exit Codes:${NC}
  0 - All verifications passed
  1 - One or more verifications failed

EOF
}

main() {
    print_header "Time Reading - Build Verification"
    
    # Parse command line arguments
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --debug)
                VERIFY_DEBUG=true
                VERIFY_RELEASE=false
                shift
                ;;
            --release)
                VERIFY_DEBUG=false
                VERIFY_RELEASE=true
                shift
                ;;
            --all)
                VERIFY_DEBUG=true
                VERIFY_RELEASE=true
                shift
                ;;
            --strict)
                STRICT_MODE=true
                print_warning "Strict mode enabled - warnings will be treated as failures"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Run verification tests
    verify_prerequisites
    verify_project_structure
    verify_gradle_configuration
    
    if [ "$VERIFY_DEBUG" = true ]; then
        verify_debug_build
    fi
    
    if [ "$VERIFY_RELEASE" = true ]; then
        verify_release_build
    fi
    
    verify_tests
    verify_lint_results
    verify_build_cache
    verify_assets_resources
    
    # Print summary and exit with appropriate code
    if print_summary; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
