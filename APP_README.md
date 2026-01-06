# Time Reading - Android Camera App

An Android application that captures photos and videos using the device camera, built with Kotlin and CameraX.

## Features

- **Photo Capture**: Take photos using the device camera
- **Video Recording**: Record videos with audio
- **Camera Preview**: Live camera preview in the app
- **Modern Architecture**: Built with AndroidX CameraX library
- **Material Design**: Uses Material Design 3 components

## Requirements

- Android SDK 24 (Android 7.0) or higher
- Android Studio Arctic Fox or later
- Kotlin 1.9.0
- Gradle 8.0

## Permissions

The app requires the following permissions:
- `CAMERA` - To access device camera
- `RECORD_AUDIO` - To record audio in videos
- `WRITE_EXTERNAL_STORAGE` - For devices running Android 9 and below

## Project Structure

```
app/
├── src/main/
│   ├── java/com/timereading/app/
│   │   └── MainActivity.kt          # Main activity with camera logic
│   ├── res/
│   │   ├── layout/
│   │   │   └── activity_main.xml    # UI layout
│   │   ├── values/
│   │   │   ├── strings.xml          # String resources
│   │   │   ├── colors.xml           # Color resources
│   │   │   └── themes.xml           # App theme
│   │   └── xml/
│   │       ├── backup_rules.xml     # Backup configuration
│   │       └── data_extraction_rules.xml
│   └── AndroidManifest.xml          # App manifest with permissions
└── build.gradle                     # App-level build configuration
```

## Building the App

1. Clone the repository:
   ```bash
   git clone https://github.com/rayroger/time-reading.git
   cd time-reading
   ```

2. Open the project in Android Studio

3. Build the project:
   ```bash
   ./gradlew build
   ```

4. Run on an emulator or physical device:
   ```bash
   ./gradlew installDebug
   ```

## How to Use

1. Launch the app
2. Grant camera and audio permissions when prompted
3. Use the **Take Photo** button to capture a still image
4. Use the **Start Recording** button to begin video recording
5. Press **Stop Recording** to end the video recording

Photos and videos are saved to:
- Photos: `Pictures/TimeReading/`
- Videos: `Movies/TimeReading/`

## Technical Details

### Dependencies

- **AndroidX Core**: Core Android libraries
- **AppCompat**: Backward compatibility
- **Material Components**: Material Design UI components
- **ConstraintLayout**: Flexible layout system
- **CameraX**: Modern camera API
  - camera-core: Core CameraX functionality
  - camera-camera2: Camera2 implementation
  - camera-lifecycle: Lifecycle integration
  - camera-video: Video recording capabilities
  - camera-view: Preview view widget

### Key Components

- **MainActivity**: Manages camera lifecycle and capture operations
- **ViewBinding**: Type-safe view access
- **CameraX Preview**: Displays live camera feed
- **ImageCapture**: Handles photo capture
- **VideoCapture**: Handles video recording with audio

## License

This project is part of the time-reading repository.

## Contributing

Feel free to submit issues and pull requests.
