# TensorFlow Lite Model Integration Guide

This document provides a comprehensive guide for integrating TensorFlow Lite models from the akucia/analog-watch-recognition repository into the time-reading Android application.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Integration Steps](#integration-steps)
4. [Model Conversion Workflow](#model-conversion-workflow)
5. [Android Integration](#android-integration)
6. [Performance Optimization](#performance-optimization)
7. [Testing and Validation](#testing-and-validation)
8. [Troubleshooting](#troubleshooting)

## Overview

The time-reading app uses TensorFlow Lite for on-device machine learning to detect analog watch faces and extract time information. The integration leverages models from the akucia/analog-watch-recognition repository, which provides a complete pipeline for analog clock recognition.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Android Application                       │
├─────────────────────────────────────────────────────────────┤
│  CameraX (Live Feed) → ImageAnalysis → WatchDialAnalyzer   │
│                              ↓                               │
│                    TensorFlow Lite Model                     │
│                              ↓                               │
│           Hand Angles → Time Extraction → UI Display        │
└─────────────────────────────────────────────────────────────┘
```

### Model Pipeline (from akucia/analog-watch-recognition)

```
Input Image
    ↓
Bounding Box Detector ────→ Watch Location
    ↓
Orientation Classifier ───→ Watch Rotation
    ↓
Keypoint Detector ────────→ Center & Top Points
    ↓
Hand Segmentation ────────→ Hand Pixels
    ↓
KDE & Line Fitting ───────→ Hand Angles
    ↓
Output: [hourAngle, minuteAngle, secondAngle, confidence]
```

## Prerequisites

### Software Requirements

- **Python 3.7-3.12** for model conversion
- **TensorFlow 2.10+** for model export and conversion
- **Android Studio** Arctic Fox or later
- **Android SDK** API 24 (Android 7.0) minimum
- **Git** for repository access

### Hardware Requirements

- Development machine with 8GB+ RAM (for TensorFlow)
- Android device with:
  - API 24+ (Android 7.0+)
  - Camera
  - 2GB+ RAM (recommended)
  - GPU acceleration (optional but recommended)

## Integration Steps

### Step 1: Prepare the Environment

```bash
# Clone the time-reading repository
git clone https://github.com/rayroger/time-reading.git
cd time-reading

# Set up Python environment (recommended: use virtualenv)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd model_conversion
pip install -r requirements.txt
```

### Step 2: Obtain Models from analog-watch-recognition

**Option A: Use Pre-trained Models (Recommended)**

```bash
# Clone the analog-watch-recognition repository
cd ../..
git clone https://github.com/akucia/analog-watch-recognition.git
cd analog-watch-recognition

# Install the package
pip install watch_recognition/

# Download pre-trained checkpoints (requires DVC)
pip install dvc
dvc pull checkpoints/segmentation.dvc
dvc pull checkpoints/keypoint.dvc
dvc pull checkpoints/detector.dvc
```

**Option B: Train Your Own Models**

Follow the training instructions in the analog-watch-recognition repository:
1. Prepare dataset (or use synthetic data generation)
2. Train individual models (detector, keypoint, segmentation)
3. Evaluate model performance
4. Export checkpoints

### Step 3: Convert Models to TensorFlow Lite

```bash
cd ../time-reading/model_conversion

# Step 3a: Export to SavedModel format
python export_savedmodel.py \
    --model-type segmentation \
    --checkpoint-path ../../analog-watch-recognition/checkpoints/segmentation \
    --output-dir saved_models/

python export_savedmodel.py \
    --model-type keypoint \
    --checkpoint-path ../../analog-watch-recognition/checkpoints/keypoint \
    --output-dir saved_models/

# Step 3b: Create unified model (combines models for single-pass inference)
python export_savedmodel.py \
    --model-type unified \
    --segmentation-model saved_models/segmentation_model \
    --keypoint-model saved_models/keypoint_model \
    --output-dir saved_models/

# Step 3c: Convert to TensorFlow Lite with quantization
python convert_to_tflite.py \
    --model-path saved_models/unified_model \
    --output watch_detector.tflite \
    --quantize dynamic \
    --validate
```

### Step 4: Deploy Model to Android

```bash
# Copy the TFLite model to Android assets
cp watch_detector.tflite ../app/src/main/assets/

# Verify the file is in place
ls -lh ../app/src/main/assets/watch_detector.tflite
```

### Step 5: Build and Test

```bash
# Build the Android app
cd ..
./gradlew assembleDebug

# Verify model is packaged in APK
unzip -l app/build/outputs/apk/debug/app-debug.apk | grep watch_detector.tflite

# Install on device
adb install app/build/outputs/apk/debug/app-debug.apk

# Check logs for model loading
adb logcat | grep WatchDialAnalyzer
```

## Model Conversion Workflow

### Detailed Conversion Process

#### 1. SavedModel Export

The `export_savedmodel.py` script handles different model types:

```python
# For segmentation model
python export_savedmodel.py \
    --model-type segmentation \
    --checkpoint-path <path-to-checkpoint> \
    --output-dir saved_models/

# Creates: saved_models/segmentation_model/
#   ├── saved_model.pb
#   ├── variables/
#   └── assets/
```

#### 2. TensorFlow Lite Conversion

The `convert_to_tflite.py` script provides multiple optimization options:

**Dynamic Range Quantization (Recommended)**
```bash
python convert_to_tflite.py \
    --model-path saved_models/unified_model \
    --output watch_detector.tflite \
    --quantize dynamic
```
- Weights: int8 (8-bit integers)
- Activations: float32
- Size reduction: ~75%
- Accuracy loss: <1%
- Best for: General mobile deployment

**Float16 Quantization**
```bash
python convert_to_tflite.py \
    --model-path saved_models/unified_model \
    --output watch_detector.tflite \
    --quantize float16
```
- Weights & Activations: float16 (16-bit floats)
- Size reduction: ~50%
- Accuracy loss: <0.1%
- Best for: GPU acceleration

**Full Integer Quantization**
```bash
python convert_to_tflite.py \
    --model-path saved_models/unified_model \
    --output watch_detector.tflite \
    --quantize int8
```
- Weights & Activations: int8
- Size reduction: ~75%
- Accuracy loss: ~2%
- Best for: Edge devices, smallest size

#### 3. Model Validation

The conversion script automatically validates:
- Model structure integrity
- Input/output tensor shapes
- Inference capability with test data
- Output value ranges

Example validation output:
```
=== Model Information ===
Input shape: [1, 224, 224, 3]
Input type: <class 'numpy.float32'>
Output shape: [1, 4]
Output type: <class 'numpy.float32'>

=== Testing Inference ===
Output: [[128.5, 312.7, 45.2, 0.87]]
Output shape: (1, 4)

✓ Validation successful!
```

## Android Integration

### WatchDialAnalyzer Implementation

The `WatchDialAnalyzer` class handles:

1. **Model Loading**: Memory-maps the .tflite file from assets
2. **Initialization**: Sets up interpreter with hardware acceleration
3. **Image Processing**: Converts camera frames to model input format
4. **Inference**: Runs model prediction
5. **Post-processing**: Extracts time from hand angles

### Hardware Acceleration Setup

```kotlin
// GPU Delegate (Primary)
if (CompatibilityList().isDelegateSupportedOnThisDevice) {
    gpuDelegate = GpuDelegate()
    options.addDelegate(gpuDelegate!!)
    Log.d(TAG, "GPU delegate enabled")
}

// NNAPI (Fallback)
if (!useGpu) {
    options.setUseNNAPI(true)
    Log.d(TAG, "NNAPI delegate enabled")
}

// CPU (Default)
options.setNumThreads(4)
```

### Inference Flow

```kotlin
override fun analyze(imageProxy: ImageProxy) {
    // 1. Convert camera frame to bitmap
    val bitmap = imageProxyToBitmap(imageProxy)
    
    // 2. Preprocess (resize, normalize)
    val tensorImage = preprocessImage(bitmap)
    
    // 3. Run inference
    interpreter.run(tensorImage.buffer, outputBuffer.buffer)
    
    // 4. Extract results
    val output = outputBuffer.floatArray
    val angles = HandAngles(
        hourAngle = output[0],
        minuteAngle = output[1],
        secondAngle = output[2]
    )
    val confidence = output[3]
    
    // 5. Convert to time
    val time = TimeExtractionHelper.extractTime(angles)
    
    // 6. Update UI
    onTimeDetected(time)
}
```

## Performance Optimization

### Model Size Optimization

| Quantization | Model Size | Accuracy | Best For |
|-------------|-----------|----------|----------|
| None (FP32) | ~20 MB | 100% | Development |
| Float16 | ~10 MB | 99.9% | GPU devices |
| Dynamic | ~5 MB | 99% | General use |
| Int8 | ~5 MB | 98% | CPU/Edge |

### Inference Speed Optimization

**1. Hardware Acceleration**
- GPU: 2-5x faster than CPU
- NNAPI: Device-specific acceleration
- CPU: Multi-threading (4 threads)

**2. Input Resolution**
- Default: 224x224 (good balance)
- Higher: 320x320 (more accurate, slower)
- Lower: 128x128 (faster, less accurate)

**3. Analysis Frequency**
- Current: 500ms interval (2 FPS)
- Real-time: 100ms interval (10 FPS)
- Power-saving: 1000ms interval (1 FPS)

### Expected Performance

| Device Type | GPU | NNAPI | CPU |
|------------|-----|-------|-----|
| Flagship (2023) | 15-25ms | 30-50ms | 60-100ms |
| Mid-range (2021) | 30-50ms | 50-80ms | 100-150ms |
| Budget (2019) | N/A | 80-120ms | 150-250ms |

## Testing and Validation

### Build Verification

```bash
# Build debug APK
./gradlew assembleDebug

# Verify model is packaged
unzip -l app/build/outputs/apk/debug/app-debug.apk | grep tflite

# Expected output:
#   assets/watch_detector.tflite
```

### Runtime Testing

```bash
# Install on device
adb install app/build/outputs/apk/debug/app-debug.apk

# Monitor logs
adb logcat -s WatchDialAnalyzer:D TimeReading:D

# Expected logs:
#   D/WatchDialAnalyzer: GPU delegate enabled
#   D/WatchDialAnalyzer: TFLite interpreter initialized successfully (using GPU)
```

### Accuracy Validation

Test with various watch images:
1. Different watch styles (classic, minimalist, ornate)
2. Various lighting conditions
3. Different angles and perspectives
4. Multiple times of day

Expected confidence scores:
- Good detection: >0.7
- Acceptable: 0.5-0.7
- Poor: <0.5

### Performance Profiling

```kotlin
// Add timing in WatchDialAnalyzer
val startTime = System.currentTimeMillis()
interpreter.run(tensorImage.buffer, outputBuffer.buffer)
val inferenceTime = System.currentTimeMillis() - startTime
Log.d(TAG, "Inference time: ${inferenceTime}ms")
```

## Troubleshooting

### Model Loading Issues

**Problem**: Model file not found
```
Log: Model file not found: watch_detector.tflite
```

**Solution**:
1. Verify file exists: `ls app/src/main/assets/watch_detector.tflite`
2. Clean and rebuild: `./gradlew clean assembleDebug`
3. Check `aaptOptions` in build.gradle

**Problem**: Model loading crash
```
Error: Failed to initialize TFLite interpreter
```

**Solution**:
1. Validate model file: `python convert_to_tflite.py --validate`
2. Check model format compatibility
3. Verify TFLite version matches

### Inference Issues

**Problem**: Always returns null/no detection
```
Log: Mock analysis - no model available
```

**Solution**:
1. Check model initialization logs
2. Verify model is correctly loaded
3. Test with demo model first

**Problem**: Incorrect time readings
```
Detected: 03:45, Actual: 09:30
```

**Solution**:
1. Check input preprocessing (normalization)
2. Verify angle calculation (0° = 12 o'clock)
3. Test with trained model (not demo)
4. Improve lighting conditions

### Performance Issues

**Problem**: Slow inference (>500ms)
```
Log: Inference time: 623ms
```

**Solution**:
1. Enable GPU delegate
2. Use dynamic quantization
3. Reduce input resolution
4. Increase analysis interval

**Problem**: High memory usage
```
Warning: Memory pressure, app may be killed
```

**Solution**:
1. Use quantized model (int8 or dynamic)
2. Release unused resources
3. Reduce image processing frequency

### Build Issues

**Problem**: Gradle build fails
```
Error: Could not resolve org.tensorflow:tensorflow-lite:2.13.0
```

**Solution**:
1. Check network connectivity
2. Verify repository configuration in build.gradle
3. Try offline mode if dependencies cached

## Best Practices

### Model Development

1. **Start with Demo Model**: Test infrastructure before full integration
2. **Iterative Training**: Train on small dataset, validate, expand
3. **Data Augmentation**: Use synthetic data for rare cases
4. **Version Control**: Tag model versions for reproducibility

### Android Integration

1. **Async Processing**: Never run inference on main thread
2. **Resource Management**: Always close interpreter and delegates
3. **Error Handling**: Graceful fallback for model failures
4. **User Feedback**: Show confidence scores and warnings

### Deployment

1. **A/B Testing**: Compare model versions in production
2. **Monitoring**: Track inference times and accuracy
3. **Fallbacks**: Provide manual time input option
4. **Updates**: Plan for over-the-air model updates

## Next Steps

After successful integration:

1. **Collect Real-World Data**: Gather user feedback and edge cases
2. **Retrain Models**: Improve accuracy with production data
3. **Optimize Further**: Profile and tune for target devices
4. **Add Features**: Multi-watch detection, digital watch support
5. **Cloud Integration**: Optional server-side processing for complex cases

## Additional Resources

- [TensorFlow Lite Guide](https://www.tensorflow.org/lite/guide)
- [TensorFlow Lite Converter](https://www.tensorflow.org/lite/convert)
- [Model Optimization](https://www.tensorflow.org/lite/performance/model_optimization)
- [GPU Delegate](https://www.tensorflow.org/lite/performance/gpu)
- [NNAPI Delegate](https://www.tensorflow.org/lite/performance/nnapi)
- [akucia/analog-watch-recognition](https://github.com/akucia/analog-watch-recognition)

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing issues and discussions
- Refer to TensorFlow Lite documentation
- Review akucia/analog-watch-recognition documentation
