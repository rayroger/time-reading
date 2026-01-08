# Watch Detector Model

## Model Information

This directory should contain the TensorFlow Lite model file `watch_detector.tflite`.

### Model Specifications

- **Input**: 224x224 RGB image (normalized to [0, 1])
- **Output**: 4 float values
  - `hourAngle`: Angle of hour hand (0-360 degrees from 12 o'clock)
  - `minuteAngle`: Angle of minute hand (0-360 degrees from 12 o'clock)
  - `secondAngle`: Angle of second hand (0-360 degrees from 12 o'clock)
  - `confidence`: Detection confidence (0-1)

### Training Requirements

To train this model, you would need:

1. **Dataset**: 
   - 10,000+ labeled images of analog watches
   - 50,000+ synthetic watch images with various hand positions
   
2. **Labels**:
   - Watch bounding box
   - Hand angles (hour, minute, second)
   - Time values

3. **Model Architecture**:
   - Backbone: MobileNetV3 or EfficientNet-B0
   - Output head: Regression for angles + classification for confidence

### Verifying Model Packaging in APK

To verify that the model file is properly packaged in the APK:

1. **Build the APK**:
   ```bash
   ./gradlew assembleDebug
   ```

2. **Inspect APK contents**:
   ```bash
   # Using Android Studio's APK Analyzer:
   # Build > Analyze APK > Select app-debug.apk
   
   # Or using command line:
   unzip -l app/build/outputs/apk/debug/app-debug.apk | grep watch_detector.tflite
   
   # Or using aapt:
   aapt list app/build/outputs/apk/debug/app-debug.apk | grep watch_detector.tflite
   ```

3. **Expected output**:
   ```
   assets/watch_detector.tflite
   ```

### Model Loading in Code

The `WatchDialAnalyzer.kt` class handles model loading:

```kotlin
private fun loadModelFile(): MappedByteBuffer? {
    return try {
        val fileDescriptor = context.assets.openFd(MODEL_FILE)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        val startOffset = fileDescriptor.startOffset
        val declaredLength = fileDescriptor.declaredLength
        fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
    } catch (e: Exception) {
        Log.w(TAG, "Model file not found: $MODEL_FILE")
        null
    }
}
```

The `aaptOptions { noCompress "tflite" }` setting in `app/build.gradle` ensures that 
.tflite files are not compressed in the APK, allowing them to be memory-mapped directly.

### Current Status

**Mock Mode**: Until a trained model is available, the `WatchDialAnalyzer` will operate 
in mock mode, indicating that no watch was detected. The infrastructure is in place for 
seamless integration once a trained model is available.

To add the model:
1. Place `watch_detector.tflite` in the `app/src/main/assets/` directory
2. Rebuild the app
3. The analyzer will automatically detect and use the model

