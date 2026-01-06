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
