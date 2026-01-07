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

### Placeholder

Until a trained model is available, the `WatchDialAnalyzer` will operate in mock mode,
indicating that no watch was detected. The infrastructure is in place for seamless
integration once a trained model is available.
