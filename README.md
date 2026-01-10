# time-reading

Android application for reading time from analog watches using machine learning and camera vision.

## Overview

This application uses TensorFlow Lite models to detect analog watch faces in camera feed and extract the time by analyzing clock hand positions. The app leverages CameraX for real-time camera preview and ML inference to provide instant time recognition.

## Features

- 📷 **Live Camera Preview**: Real-time camera feed with CameraX
- 🤖 **ML-Based Time Recognition**: TensorFlow Lite models for watch detection and hand angle extraction
- ⚡ **Hardware Acceleration**: GPU and NNAPI delegates for optimal performance
- 📸 **Photo Capture**: Save images with detected time
- 🎥 **Video Recording**: Record video with audio
- 🎯 **High Accuracy**: Confidence scoring for reliable time readings
- 📱 **Material Design**: Modern, intuitive user interface

## Architecture

The application uses a multi-stage ML pipeline:

1. **Watch Face Detection**: Locate the watch in the camera frame
2. **Keypoint Detection**: Identify center and reference points
3. **Hand Segmentation**: Detect hour, minute, and second hands
4. **Angle Extraction**: Calculate hand angles relative to 12 o'clock
5. **Time Conversion**: Convert angles to time (HH:MM:SS)

### TensorFlow Lite Integration

Models are integrated from the [akucia/analog-watch-recognition](https://github.com/akucia/analog-watch-recognition) repository:

- **Input**: 224x224 RGB images (normalized to [0, 1])
- **Output**: Hand angles (hour, minute, second) and confidence score
- **Optimization**: Dynamic quantization for 4x size reduction
- **Acceleration**: GPU delegate (primary), NNAPI (fallback), CPU (default)

See [model_conversion/README.md](model_conversion/README.md) for details on model conversion and optimization.

## Requirements

- **Android SDK**: API 24 (Android 7.0) or higher
- **Target SDK**: API 34 (Android 14)
- **Kotlin**: 1.9.0
- **Gradle**: 8.0
- **Device**: Camera-enabled Android device

## Building the App

### 1. Clone the Repository

```bash
git clone https://github.com/rayroger/time-reading.git
cd time-reading
```

### 2. Prepare TensorFlow Lite Models

**Option A: Using Demo Model (for testing)**

A mock model is already included in `app/src/main/assets/watch_detector.tflite` for build testing.

**Option B: Creating a Real Demo Model**

```bash
cd model_conversion
pip install -r requirements.txt
python create_demo_model.py --output ../app/src/main/assets/watch_detector.tflite
cd ..
```

**Option C: Converting Trained Models**

See [model_conversion/README.md](model_conversion/README.md) for complete instructions on converting models from analog-watch-recognition.

### 3. Build the APK

```bash
# Debug build
./gradlew assembleDebug

# Release build
./gradlew assembleRelease
```

### 4. Install on Device

```bash
# Install debug APK
./gradlew installDebug

# Or manually install
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Usage

1. **Launch the app** and grant camera permissions
2. **Point camera** at an analog watch face
3. **Tap "Analyze Watch"** to enable ML analysis
4. **View detected time** displayed on screen with confidence score
5. **Take photos** or **record videos** of the detection

### UI Controls

- **Analyze Watch**: Toggle ML analysis on/off
- **Take Photo**: Capture still image
- **Start/Stop Recording**: Record video with audio

## Model Integration Details

### Model Specifications

The app expects a TensorFlow Lite model with:

**Input Tensor:**
- Name: `input_image`
- Shape: `[1, 224, 224, 3]`
- Type: `float32`
- Format: RGB image normalized to [0, 1]

**Output Tensor:**
- Name: `output`
- Shape: `[1, 4]`
- Type: `float32`
- Format: `[hourAngle, minuteAngle, secondAngle, confidence]`
  - Angles in degrees (0-360), 0° = 12 o'clock position
  - Confidence score (0.0-1.0)

### Performance Optimization

The app automatically selects the best inference backend:

1. **GPU Delegate** (fastest for float models)
   - Used if device supports GPU acceleration
   - ~2-5x faster than CPU
   - Better for float16 quantized models

2. **NNAPI** (hardware acceleration)
   - Used if GPU not available
   - Leverages device-specific accelerators
   - Good for int8 quantized models

3. **CPU** (fallback)
   - 4 threads for parallel processing
   - Works on all devices

### Inference Pipeline

```
Camera Frame (YUV_420_888)
    ↓
Convert to RGB Bitmap
    ↓
Resize to 224x224
    ↓
Normalize to [0, 1]
    ↓
TFLite Model Inference
    ↓
Extract Hand Angles
    ↓
Convert to Time (HH:MM:SS)
    ↓
Validate & Display
```

## Project Structure

```
time-reading/
├── app/
│   ├── src/main/
│   │   ├── assets/
│   │   │   ├── watch_detector.tflite    # TFLite model
│   │   │   └── MODEL_README.md          # Model documentation
│   │   ├── java/com/timereading/app/
│   │   │   ├── MainActivity.kt          # Main activity
│   │   │   └── ml/
│   │   │       ├── WatchDialAnalyzer.kt # ML inference
│   │   │       ├── WatchTime.kt         # Data model
│   │   │       └── TimeExtractionHelper.kt # Angle→time conversion
│   │   └── res/                         # UI resources
│   └── build.gradle                     # App dependencies
├── model_conversion/
│   ├── README.md                        # Model conversion guide
│   ├── requirements.txt                 # Python dependencies
│   ├── export_savedmodel.py            # Export from akucia repo
│   ├── convert_to_tflite.py            # Convert to TFLite
│   └── create_demo_model.py            # Create demo model
├── build.gradle                         # Project configuration
└── README.md                            # This file
```

## Development

### Key Dependencies

```gradle
// CameraX for camera functionality
implementation "androidx.camera:camera-core:1.3.0"
implementation "androidx.camera:camera-camera2:1.3.0"
implementation "androidx.camera:camera-lifecycle:1.3.0"

// TensorFlow Lite for ML inference
implementation 'org.tensorflow:tensorflow-lite:2.13.0'
implementation 'org.tensorflow:tensorflow-lite-gpu:2.13.0'
implementation 'org.tensorflow:tensorflow-lite-support:0.4.4'
```

### Testing

```bash
# Run unit tests
./gradlew test

# Run instrumented tests
./gradlew connectedAndroidTest
```

### Code Style

- **Language**: Kotlin
- **Min SDK**: 24 (Android 7.0)
- **Target SDK**: 34 (Android 14)
- **Java Version**: 1.8

## Model Training

To train your own models for better accuracy:

1. Clone [akucia/analog-watch-recognition](https://github.com/akucia/analog-watch-recognition)
2. Follow their training instructions
3. Use the conversion scripts in `model_conversion/` to export to TFLite
4. Replace `app/src/main/assets/watch_detector.tflite`

## Performance Benchmarks

Expected inference times (224x224 input):

| Device | GPU | NNAPI | CPU |
|--------|-----|-------|-----|
| High-end (2023) | ~20ms | ~40ms | ~80ms |
| Mid-range (2021) | ~40ms | ~60ms | ~120ms |
| Budget (2019) | N/A | ~100ms | ~200ms |

*Actual performance varies by device and quantization method*

## Troubleshooting

### Model not loading

1. Verify `watch_detector.tflite` exists in `app/src/main/assets/`
2. Check build logs for asset packaging
3. Verify `aaptOptions { noCompress "tflite" }` in build.gradle

### Poor detection accuracy

1. Ensure good lighting conditions
2. Hold camera steady
3. Frame the watch face clearly
4. Check confidence score (should be >0.5)
5. Consider training with more diverse dataset

### Slow inference

1. Check which delegate is active in logs
2. Try different quantization methods
3. Reduce analysis frequency (increase ANALYSIS_INTERVAL_MS)
4. Use smaller input resolution

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [akucia/analog-watch-recognition](https://github.com/akucia/analog-watch-recognition) for ML models
- [TensorFlow Lite](https://www.tensorflow.org/lite) for mobile ML framework
- [CameraX](https://developer.android.com/training/camerax) for camera APIs

## References

- [Model Conversion Guide](model_conversion/README.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Model Specifications](app/src/main/assets/MODEL_README.md)
- [TensorFlow Lite Android Guide](https://www.tensorflow.org/lite/guide/android)

## Contact

For questions or issues, please open an issue on GitHub.

