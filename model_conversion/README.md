# Model Conversion Scripts

This directory contains Python scripts for converting TensorFlow models from the [akucia/analog-watch-recognition](https://github.com/akucia/analog-watch-recognition) repository to TensorFlow Lite format for use in the Android application.

## Overview

The akucia/analog-watch-recognition project uses multiple models in a pipeline:
- **Bounding Box Detector**: Locates the watch face in the image
- **Orientation Classifier**: Determines watch orientation
- **Keypoint Detector**: Identifies center and top reference points
- **Hand Segmentation**: Segments hour and minute hands
- **Post-processing**: KDE and line fitting to extract hand angles

For the Android app, we need these models converted to TensorFlow Lite (.tflite) format with optimizations for mobile deployment.

## Scripts

### 1. `export_savedmodel.py`

Exports trained TensorFlow models from the analog-watch-recognition repository as SavedModel format (prerequisite for TFLite conversion).

**Usage:**
```bash
# Export segmentation model
python export_savedmodel.py \
    --model-type segmentation \
    --checkpoint-path /path/to/checkpoints/segmentation \
    --output-dir saved_models/

# Export keypoint model
python export_savedmodel.py \
    --model-type keypoint \
    --checkpoint-path /path/to/checkpoints/keypoint \
    --output-dir saved_models/

# Export detector model
python export_savedmodel.py \
    --model-type detector \
    --checkpoint-path /path/to/checkpoints/detector \
    --output-dir saved_models/

# Create unified model (combines segmentation + keypoint)
python export_savedmodel.py \
    --model-type unified \
    --segmentation-model saved_models/segmentation_model \
    --keypoint-model saved_models/keypoint_model \
    --output-dir saved_models/
```

**Note**: The unified model combines segmentation and keypoint detection to directly output hand angles in a format compatible with the Android app.

### 2. `convert_to_tflite.py`

Converts SavedModel to TensorFlow Lite format with various optimization options.

**Usage:**
```bash
# Convert with dynamic range quantization (recommended)
python convert_to_tflite.py \
    --model-path saved_models/unified_model \
    --output watch_detector.tflite \
    --quantize dynamic

# Convert with float16 quantization (good for GPU)
python convert_to_tflite.py \
    --model-path saved_models/unified_model \
    --output watch_detector.tflite \
    --quantize float16

# Convert with full int8 quantization (smallest size)
python convert_to_tflite.py \
    --model-path saved_models/unified_model \
    --output watch_detector.tflite \
    --quantize int8

# Convert without quantization
python convert_to_tflite.py \
    --model-path saved_models/unified_model \
    --output watch_detector.tflite \
    --quantize none
```

**Quantization Options:**
- **`dynamic`** (recommended): Quantizes weights to int8, keeps activations as float32. ~4x size reduction, minimal accuracy loss.
- **`float16`**: Reduces precision to 16-bit floats. ~2x size reduction, good GPU performance.
- **`int8`**: Full integer quantization. ~4x size reduction, fastest on CPU, requires representative dataset.
- **`none`**: No quantization, keeps float32. Largest size but highest accuracy.

### 3. `create_demo_model.py`

Creates a simple demo/mock TensorFlow Lite model for testing the Android integration without needing the full analog-watch-recognition training pipeline.

**Usage:**
```bash
# Create demo model directly in Android assets
python create_demo_model.py --output ../app/src/main/assets/watch_detector.tflite

# Create demo model in current directory
python create_demo_model.py --output watch_detector.tflite

# Create without quantization (larger but faster conversion)
python create_demo_model.py --output watch_detector.tflite --no-quantize
```

**⚠️ Important**: The demo model is **only for testing the Android infrastructure**. It will NOT produce accurate time readings from actual watch images. For production use, you must train and convert real models from analog-watch-recognition.

## Requirements

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install tensorflow>=2.10.0 numpy
```

For working with the full analog-watch-recognition repository:
```bash
pip install watch_recognition
```

## Complete Workflow

### Option A: Using Pre-trained Models from analog-watch-recognition

1. **Clone and setup analog-watch-recognition**:
   ```bash
   git clone https://github.com/akucia/analog-watch-recognition.git
   cd analog-watch-recognition
   pip install watch_recognition/
   ```

2. **Download pre-trained checkpoints** (if available via DVC):
   ```bash
   dvc pull checkpoints/segmentation.dvc
   dvc pull checkpoints/keypoint.dvc
   dvc pull checkpoints/detector.dvc
   ```

3. **Export to SavedModel**:
   ```bash
   cd ../time-reading/model_conversion
   
   # Export individual models
   python export_savedmodel.py --model-type segmentation \
       --checkpoint-path ../../analog-watch-recognition/checkpoints/segmentation \
       --output-dir saved_models/
   
   python export_savedmodel.py --model-type keypoint \
       --checkpoint-path ../../analog-watch-recognition/checkpoints/keypoint \
       --output-dir saved_models/
   ```

4. **Create unified model**:
   ```bash
   python export_savedmodel.py --model-type unified \
       --segmentation-model saved_models/segmentation_model \
       --keypoint-model saved_models/keypoint_model \
       --output-dir saved_models/
   ```

5. **Convert to TensorFlow Lite**:
   ```bash
   python convert_to_tflite.py \
       --model-path saved_models/unified_model \
       --output watch_detector.tflite \
       --quantize dynamic
   ```

6. **Copy to Android assets**:
   ```bash
   cp watch_detector.tflite ../app/src/main/assets/
   ```

### Option B: Using Demo Model (for testing only)

1. **Create demo model**:
   ```bash
   cd model_conversion
   python create_demo_model.py --output ../app/src/main/assets/watch_detector.tflite
   ```

2. **Build Android app**:
   ```bash
   cd ..
   ./gradlew assembleDebug
   ```

## Model Specifications

The Android app expects a TensorFlow Lite model with the following signature:

**Input:**
- Shape: `[1, 224, 224, 3]`
- Type: `float32`
- Format: RGB image normalized to [0, 1]

**Output:**
- Shape: `[1, 4]`
- Type: `float32`
- Format: `[hourAngle, minuteAngle, secondAngle, confidence]`
  - `hourAngle`: Angle of hour hand in degrees (0-360), where 0° = 12 o'clock
  - `minuteAngle`: Angle of minute hand in degrees (0-360)
  - `secondAngle`: Angle of second hand in degrees (0-360), or -1 if not detected
  - `confidence`: Detection confidence score (0.0-1.0)

## Troubleshooting

### Model loading fails in Android

1. **Verify model is in assets**: Check `app/src/main/assets/watch_detector.tflite` exists
2. **Check APK contents**: 
   ```bash
   ./gradlew assembleDebug
   unzip -l app/build/outputs/apk/debug/app-debug.apk | grep tflite
   ```
3. **Verify `aaptOptions`** in `app/build.gradle`:
   ```gradle
   aaptOptions {
       noCompress "tflite"
   }
   ```

### Conversion errors

- **Out of memory**: Try using quantization or reduce batch size in representative dataset
- **Incompatible ops**: Check that all model operations are supported by TFLite
- **Shape issues**: Ensure model has fixed input shape or use dynamic shapes correctly

### Model produces incorrect results

- **Check input preprocessing**: Verify images are normalized to [0, 1]
- **Verify quantization**: Try without quantization first to isolate issues
- **Check output scaling**: Ensure angles are in correct range (0-360)

## Performance Optimization

### Size vs Accuracy Trade-offs

| Quantization | Model Size | CPU Latency | GPU Latency | Accuracy Loss |
|-------------|-----------|-------------|-------------|---------------|
| None (FP32) | ~20 MB | 100ms | 50ms | 0% |
| Float16 | ~10 MB | 95ms | 25ms | <0.1% |
| Dynamic | ~5 MB | 60ms | N/A | <1% |
| Int8 | ~5 MB | 40ms | N/A | ~2% |

*Note: Actual numbers depend on model architecture and hardware*

### Android Optimization Tips

1. **Use GPU delegate** for float16 models:
   ```kotlin
   val options = Interpreter.Options().apply {
       addDelegate(GpuDelegate())
   }
   ```

2. **Use NNAPI** for int8 models:
   ```kotlin
   val options = Interpreter.Options().apply {
       setUseNNAPI(true)
   }
   ```

3. **Increase threads** for CPU inference:
   ```kotlin
   val options = Interpreter.Options().apply {
       setNumThreads(4)
   }
   ```

## References

- [TensorFlow Lite Converter](https://www.tensorflow.org/lite/convert)
- [TensorFlow Lite Optimization](https://www.tensorflow.org/lite/performance/model_optimization)
- [akucia/analog-watch-recognition](https://github.com/akucia/analog-watch-recognition)
- [TensorFlow Lite Android Guide](https://www.tensorflow.org/lite/guide/android)
