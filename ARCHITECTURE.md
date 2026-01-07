# Application Architecture Overview

## Time Reading Camera App

### High-Level Architecture

```
┌─────────────────────────────────────────────┐
│           MainActivity                      │
│  ┌───────────────────────────────────────┐ │
│  │  Camera Preview (PreviewView)         │ │
│  │  - Live camera feed                   │ │
│  │  - Full screen display                │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Take Photo  │  │  Start/Stop Video   │ │
│  │   Button    │  │      Button         │ │
│  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Component Flow

```
MainActivity
    │
    ├── onCreate()
    │   ├── Check Permissions
    │   │   ├── If granted → startCamera()
    │   │   └── If not → requestPermissions()
    │   └── Setup Button Listeners
    │
    ├── startCamera()
    │   ├── Initialize CameraProvider
    │   ├── Setup Preview UseCase
    │   ├── Setup ImageCapture UseCase
    │   ├── Setup VideoCapture UseCase
    │   └── Bind all to Lifecycle
    │
    ├── takePhoto()
    │   ├── Create OutputFileOptions
    │   ├── Capture Image
    │   └── Save to MediaStore
    │       └── Pictures/TimeReading/
    │
    └── captureVideo()
        ├── If recording → Stop Recording
        └── If not recording → Start Recording
            ├── Create MediaStoreOutputOptions
            ├── Enable Audio (if permitted)
            └── Save to MediaStore
                └── Movies/TimeReading/
```

### Permissions Flow

```
App Launch
    │
    ├── Check Permissions
    │   ├── CAMERA
    │   ├── RECORD_AUDIO
    │   └── WRITE_EXTERNAL_STORAGE (API ≤ 28)
    │
    ├── All Granted?
    │   ├── YES → Initialize Camera
    │   └── NO → Request Permissions
    │           │
    │           ├── User Grants → Initialize Camera
    │           └── User Denies → Show Toast & Exit
```

### CameraX Use Cases

```
CameraProvider
    │
    ├── Preview
    │   └── Displays live camera feed
    │
    ├── ImageCapture
    │   └── Captures still photos
    │
    └── VideoCapture<Recorder>
        └── Records video with audio
```

### File Storage

```
MediaStore
    │
    ├── Images
    │   └── Pictures/TimeReading/
    │       └── yyyy-MM-dd-HH-mm-ss-SSS.jpg
    │
    └── Video
        └── Movies/TimeReading/
            └── yyyy-MM-dd-HH-mm-ss-SSS.mp4
```

## Key Technologies

- **Language**: Kotlin
- **Min SDK**: API 24 (Android 7.0)
- **Target SDK**: API 34 (Android 14)
- **Camera API**: CameraX 1.3.0
- **UI**: Material Design 3
- **View Binding**: Enabled for type-safe view access

## Features Implemented

1. ✅ Camera Preview
2. ✅ Photo Capture
3. ✅ Video Recording with Audio
4. ✅ Runtime Permission Handling
5. ✅ MediaStore Integration
6. ✅ Lifecycle-aware Camera Management
7. ✅ Material Design UI

## Build Configuration

- **Gradle Version**: 8.0
- **Android Gradle Plugin**: 8.1.0
- **Kotlin Version**: 1.9.0
- **Compile SDK**: 34
- **View Binding**: Enabled

## ML-Based Analog Watch Dial Recognition

### Overview

The application includes ML-based capabilities to recognize analog watch dials and extract time information from watch hands. This feature uses computer vision and machine learning to detect watch faces in camera frames and interpret the positions of hour, minute, and second hands.

### ML Architecture

```
Camera Frame
    │
    ├── Image Preprocessing
    │   ├── Resize to model input size (224x224 or 320x320)
    │   ├── Normalize pixel values (0-1 or -1 to 1)
    │   └── Convert to RGB/Grayscale
    │
    ├── Watch Face Detection
    │   ├── Object Detection Model (TensorFlow Lite)
    │   │   └── Detects watch dial bounding box
    │   └── Circle Detection (Hough Transform)
    │       └── Identifies circular watch face
    │
    ├── Watch Dial Extraction
    │   ├── Crop to detected region
    │   ├── Perspective correction
    │   └── Center alignment
    │
    ├── Hand Detection & Recognition
    │   ├── CNN-based Hand Segmentation
    │   │   ├── Hour hand (short, thick)
    │   │   ├── Minute hand (long, medium)
    │   │   └── Second hand (long, thin)
    │   │
    │   ├── Line Detection (Hough Lines)
    │   │   └── Detect hand orientations
    │   │
    │   └── Angle Calculation
    │       ├── Calculate angle from 12 o'clock
    │       ├── Hour angle → hours (0-11)
    │       ├── Minute angle → minutes (0-59)
    │       └── Second angle → seconds (0-59)
    │
    └── Time Extraction
        ├── Convert angles to time
        ├── Validate time reading
        └── Display recognized time
```

### ML Pipeline Components

#### 1. Watch Face Detection

```
Input: Camera Frame (1920x1080 or similar)
    │
    ├── TensorFlow Lite Object Detection Model
    │   ├── Model: MobileNet SSD or EfficientDet-Lite
    │   ├── Input Size: 320x320 or 300x300
    │   ├── Output: Bounding boxes with confidence scores
    │   └── Classes: ["analog_watch", "clock"]
    │
    └── Alternative: Classical CV Approach
        ├── Convert to Grayscale
        ├── Edge Detection (Canny)
        ├── Circle Detection (Hough Circle Transform)
        └── Filter by size and circularity
```

#### 2. Hand Recognition Model

```
Watch Face Image (Cropped)
    │
    ├── CNN Segmentation Network
    │   ├── Architecture: U-Net or MobileNetV3
    │   ├── Input: 224x224 RGB image
    │   ├── Output: 3-channel mask (hour/minute/second)
    │   └── Training: Synthetic watch images + real data
    │
    ├── Post-Processing
    │   ├── Morphological operations (erosion/dilation)
    │   ├── Skeleton extraction
    │   └── Line fitting
    │
    └── Angle Extraction
        ├── Find center of watch
        ├── Calculate hand vectors from center
        ├── Compute angles relative to 12 o'clock
        └── Handle overlapping hands
```

#### 3. Time Calculation

```
Hand Angles
    │
    ├── Hour Hand Processing
    │   ├── Angle range: 0-360°
    │   ├── Hour = (angle / 30) % 12
    │   └── Consider minute hand for precision
    │
    ├── Minute Hand Processing
    │   ├── Angle range: 0-360°
    │   └── Minute = (angle / 6) % 60
    │
    ├── Second Hand Processing (Optional)
    │   ├── Angle range: 0-360°
    │   └── Second = (angle / 6) % 60
    │
    └── Time Validation
        ├── Check consistency between hands
        ├── Validate against physical constraints
        └── Apply temporal smoothing for video
```

### Integration with CameraX

```
CameraProvider
    │
    ├── Preview UseCase
    │   └── Display to user
    │
    ├── ImageAnalysis UseCase (NEW)
    │   ├── Target Resolution: 640x480 or higher
    │   ├── Output Format: YUV_420_888
    │   ├── Executor: Dedicated ML executor thread
    │   │
    │   └── Analyzer Implementation
    │       ├── Convert YUV to RGB
    │       ├── Run ML inference
    │       ├── Extract time from hands
    │       └── Update UI with results
    │
    ├── ImageCapture UseCase
    │   └── Existing photo capture
    │
    └── VideoCapture UseCase
        └── Existing video recording
```

### ML Model Options

#### Option 1: TensorFlow Lite Models

**Watch Detection:**
- **Model**: MobileNet SSD v2 or EfficientDet-Lite0
- **Size**: 3-10 MB
- **Inference Time**: 50-150ms on mobile GPU
- **Accuracy**: 90-95% mAP

**Hand Segmentation:**
- **Model**: Custom U-Net with MobileNetV3 backbone
- **Size**: 5-15 MB
- **Inference Time**: 100-200ms
- **Accuracy**: 85-92% IoU

#### Option 2: ML Kit (Google)

**Text Recognition + Custom:**
- Use ML Kit for watch number detection
- Custom model for hand detection
- Hybrid approach for better accuracy

#### Option 3: Custom Lightweight CNN

**End-to-End Time Reading:**
- **Model**: Custom CNN (ResNet-18 or EfficientNet-B0 backbone)
- **Input**: 224x224 watch face image
- **Output**: Direct time prediction (hours, minutes, seconds)
- **Size**: 8-20 MB
- **Inference Time**: 80-150ms

### Technical Implementation Details

#### Model Integration

```kotlin
class WatchDialAnalyzer(
    private val context: Context
) : ImageAnalysis.Analyzer {
    
    private val interpreter: Interpreter
    private val inputImageBuffer: TensorImage
    private val outputBuffer: TensorBuffer
    
    init {
        // Load TFLite model from assets
        val model = FileUtil.loadMappedFile(context, "watch_detector.tflite")
        interpreter = Interpreter(model)
        
        // Initialize input/output tensors
        inputImageBuffer = TensorImage(DataType.FLOAT32)
        outputBuffer = TensorBuffer.createFixedSize(
            intArrayOf(1, 4), DataType.FLOAT32
        )
    }
    
    override fun analyze(imageProxy: ImageProxy) {
        // Convert ImageProxy to Bitmap
        val bitmap = imageProxy.toBitmap()
        
        // Preprocess image
        inputImageBuffer.load(bitmap)
        val processedImage = preprocessImage(inputImageBuffer)
        
        // Run inference
        interpreter.run(processedImage.buffer, outputBuffer.buffer)
        
        // Post-process results
        val time = extractTimeFromOutput(outputBuffer)
        
        // Update UI
        onTimeDetected(time)
        
        imageProxy.close()
    }
}
```

#### Image Preprocessing

```kotlin
private fun preprocessImage(image: TensorImage): TensorImage {
    // Resize to model input size
    val imageProcessor = ImageProcessor.Builder()
        .add(ResizeOp(224, 224, ResizeMethod.BILINEAR))
        .add(NormalizeOp(0f, 255f))  // Normalize to [0,1]
        .add(Rot90Op(getRotationDegrees()))
        .build()
    
    return imageProcessor.process(image)
}
```

#### Angle Calculation

```kotlin
private fun calculateHandAngles(
    centerX: Float, 
    centerY: Float,
    handPoints: List<Point>
): HandAngles {
    val hourAngle = calculateAngle(centerX, centerY, hourHand)
    val minuteAngle = calculateAngle(centerX, centerY, minuteHand)
    val secondAngle = calculateAngle(centerX, centerY, secondHand)
    
    return HandAngles(hourAngle, minuteAngle, secondAngle)
}

private fun calculateAngle(cx: Float, cy: Float, point: Point): Float {
    val dx = point.x - cx
    val dy = cy - point.y  // Inverted Y-axis
    var angle = Math.toDegrees(atan2(dy.toDouble(), dx.toDouble())).toFloat()
    
    // Adjust to 12 o'clock reference (90° offset)
    angle = (angle - 90 + 360) % 360
    
    return angle
}
```

#### Time Extraction

```kotlin
data class WatchTime(
    val hours: Int,
    val minutes: Int,
    val seconds: Int,
    val confidence: Float
)

private fun extractTime(angles: HandAngles): WatchTime {
    // Convert angles to time components
    val hours = ((angles.hourAngle / 30f) % 12).toInt()
    val minutes = ((angles.minuteAngle / 6f) % 60).toInt()
    val seconds = ((angles.secondAngle / 6f) % 60).toInt()
    
    // Calculate confidence based on hand consistency
    val confidence = calculateConfidence(angles)
    
    return WatchTime(hours, minutes, seconds, confidence)
}
```

### Training Data Requirements

#### Dataset Composition

- **Real Watch Images**: 10,000+ labeled images
  - Various watch styles (digital, analog, mixed)
  - Different lighting conditions
  - Multiple angles and perspectives
  - Varied backgrounds
  
- **Synthetic Data**: 50,000+ generated images
  - Programmatically generated watch faces
  - Random hand positions
  - Augmented with noise, blur, rotation
  - Helps with rare time combinations

#### Annotation Format

```json
{
  "image_id": "watch_001.jpg",
  "watch_bbox": [x, y, width, height],
  "hands": {
    "hour": {
      "angle": 90.0,
      "start": [cx, cy],
      "end": [x1, y1]
    },
    "minute": {
      "angle": 180.0,
      "start": [cx, cy],
      "end": [x2, y2]
    },
    "second": {
      "angle": 270.0,
      "start": [cx, cy],
      "end": [x3, y3]
    }
  },
  "time": "03:30:45",
  "watch_type": "analog"
}
```

### Performance Optimization

#### Model Optimization Techniques

```
TensorFlow Lite Optimizations
    │
    ├── Quantization
    │   ├── Post-training quantization (INT8)
    │   ├── Reduces model size by 4x
    │   └── Minimal accuracy loss (~1-2%)
    │
    ├── GPU Delegation
    │   ├── Use GPU delegate on supported devices
    │   ├── 2-5x faster inference
    │   └── Lower power consumption
    │
    ├── NNAPI Delegation
    │   ├── Use Android Neural Networks API
    │   ├── Hardware acceleration
    │   └── Device-specific optimization
    │
    └── Model Pruning
        ├── Remove redundant connections
        ├── Reduce model size by 30-50%
        └── Maintain accuracy
```

#### Runtime Optimization

```kotlin
// Use dedicated thread pool for ML operations
private val mlExecutor = Executors.newSingleThreadExecutor()

// Configure interpreter options
private fun createInterpreter(model: ByteBuffer): Interpreter {
    val options = Interpreter.Options().apply {
        setNumThreads(4)  // Use 4 CPU threads
        
        // Try to use GPU delegate
        if (isGpuSupported()) {
            addDelegate(GpuDelegate())
        }
        
        // Fallback to NNAPI
        if (isNnapiSupported()) {
            setUseNNAPI(true)
        }
    }
    
    return Interpreter(model, options)
}
```

### Error Handling & Edge Cases

```
ML Inference Pipeline
    │
    ├── No Watch Detected
    │   ├── Show "Point camera at watch" message
    │   └── Continue analyzing frames
    │
    ├── Multiple Watches Detected
    │   ├── Select largest/closest watch
    │   └── Focus on primary detection
    │
    ├── Low Confidence Detection
    │   ├── Threshold: confidence < 0.7
    │   └── Show "Unclear reading" warning
    │
    ├── Overlapping Hands
    │   ├── Use temporal information
    │   └── Apply physics-based constraints
    │
    └── Invalid Time Reading
        ├── Check consistency (hour vs minute)
        ├── Apply smoothing over frames
        └── Flag suspicious readings
```

### UI Integration

```
┌─────────────────────────────────────────────┐
│           MainActivity                      │
│  ┌───────────────────────────────────────┐ │
│  │  Camera Preview                       │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │  ╔═══════════════════════════╗  │ │ │
│  │  │  ║  Detected Watch           ║  │ │ │
│  │  │  ║  Time: 03:45:12          ║  │ │ │
│  │  │  ║  Confidence: 94%         ║  │ │ │
│  │  │  ╚═══════════════════════════╝  │ │ │
│  │  └─────────────────────────────────┘ │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Analyze   │  │  Take Photo         │ │
│  │   Watch     │  │                     │ │
│  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Dependencies for ML

```gradle
dependencies {
    // Existing dependencies...
    
    // TensorFlow Lite
    implementation 'org.tensorflow:tensorflow-lite:2.14.0'
    implementation 'org.tensorflow:tensorflow-lite-gpu:2.14.0'
    implementation 'org.tensorflow:tensorflow-lite-support:0.4.4'
    
    // ML Kit (Optional - for hybrid approach)
    implementation 'com.google.mlkit:object-detection:17.0.1'
    implementation 'com.google.mlkit:image-labeling:17.0.8'
    
    // Image processing
    implementation 'org.opencv:opencv-android:4.8.0'  // Optional
}
```

### Future Enhancements

1. **Multi-Watch Support**: Detect and read multiple watches simultaneously
2. **Digital Watch Recognition**: OCR-based reading for digital displays
3. **Smart Watch Detection**: Special handling for smart watches
4. **World Clock Mode**: Recognize watches from different time zones
5. **Historical Tracking**: Log time readings over time
6. **AR Overlay**: Draw detected hands and recognized time on preview
7. **Voice Announcement**: Speak detected time aloud
8. **Accuracy Metrics**: Display detection quality indicators
9. **Offline Training**: On-device model fine-tuning
10. **Cloud Sync**: Share detected times across devices
