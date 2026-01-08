#!/usr/bin/env python3
"""
Create a simple demo TensorFlow Lite model for testing the Android integration.

This script creates a minimal model that outputs mock hand angles for testing
the Android inference pipeline without requiring the full analog-watch-recognition
training pipeline.

Requirements:
    pip install tensorflow>=2.10.0 numpy

Usage:
    python create_demo_model.py --output ../app/src/main/assets/watch_detector.tflite
"""

import argparse
import os
import sys

try:
    import tensorflow as tf
    import numpy as np
except ImportError:
    print("Error: TensorFlow not installed. Please run: pip install tensorflow>=2.10.0 numpy")
    sys.exit(1)


def create_simple_demo_model():
    """
    Create a simple CNN model that takes an image and outputs hand angles.
    
    This is a mock model for testing purposes. It will output plausible
    but not accurate hand angles based on simple image features.
    
    Returns:
        A compiled Keras model
    """
    print("Creating demo watch detector model...")
    
    # Input: 224x224 RGB image
    inputs = tf.keras.Input(shape=(224, 224, 3), name='input_image')
    
    # Simple CNN feature extractor
    # Using MobileNetV2-inspired architecture for efficiency
    x = tf.keras.layers.Conv2D(32, 3, strides=2, padding='same', activation='relu')(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    
    x = tf.keras.layers.Conv2D(64, 3, strides=2, padding='same', activation='relu')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    
    x = tf.keras.layers.Conv2D(128, 3, strides=2, padding='same', activation='relu')(x)
    x = tf.keras.layers.BatchNormalization()(x)
    
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    
    # Regression head for hand angles
    x = tf.keras.layers.Dense(256, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    x = tf.keras.layers.Dense(128, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    
    # Output layer: [hourAngle, minuteAngle, secondAngle, confidence]
    # Angles are in range [0, 360] degrees
    # Confidence is in range [0, 1]
    outputs = tf.keras.layers.Dense(4, activation='linear', name='output')(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=outputs, name='watch_detector')
    
    # Compile the model (needed for saving)
    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['mae']
    )
    
    print(f"Model created with {model.count_params():,} parameters")
    return model


def initialize_with_mock_weights(model):
    """
    Initialize model with mock weights that produce reasonable outputs.
    
    This helps the demo model produce plausible angle values even without training.
    """
    print("Initializing with mock weights...")
    
    # Create some dummy training data to give the model a starting point
    # This is just for demonstration - in reality you'd train on real data
    num_samples = 100
    
    # Generate random images
    X = np.random.rand(num_samples, 224, 224, 3).astype(np.float32)
    
    # Generate plausible angle outputs
    # Hour angle: 0-360 degrees (uniform distribution)
    hour_angles = np.random.uniform(0, 360, num_samples)
    # Minute angle: 0-360 degrees
    minute_angles = np.random.uniform(0, 360, num_samples)
    # Second angle: 0-360 degrees (or -1 for no second hand)
    second_angles = np.random.uniform(0, 360, num_samples)
    # Confidence: 0.7-0.95 for demo
    confidence = np.random.uniform(0.7, 0.95, num_samples)
    
    y = np.stack([hour_angles, minute_angles, second_angles, confidence], axis=1).astype(np.float32)
    
    # Quick training to initialize weights
    print("Quick initialization training...")
    model.fit(X, y, epochs=5, batch_size=16, verbose=0)
    
    print("Model initialized")


def convert_to_tflite(model, output_path, quantize=True):
    """
    Convert the Keras model to TensorFlow Lite format.
    
    Args:
        model: Keras model to convert
        output_path: Path to save the .tflite file
        quantize: Whether to apply dynamic range quantization
    """
    print(f"Converting to TensorFlow Lite (quantize={quantize})...")
    
    # Create converter
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Apply optimizations
    if quantize:
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        print("Applying dynamic range quantization...")
    
    # Convert
    tflite_model = converter.convert()
    
    # Save
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✓ TFLite model saved to {output_path} ({file_size_mb:.2f} MB)")


def validate_tflite_model(tflite_path):
    """
    Validate the TFLite model by running test inference.
    """
    print(f"\nValidating model: {tflite_path}")
    
    # Load the model
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    
    # Get input and output details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print("\n=== Model Details ===")
    print(f"Input shape: {input_details[0]['shape']}")
    print(f"Input type: {input_details[0]['dtype'].__name__}")
    print(f"Output shape: {output_details[0]['shape']}")
    print(f"Output type: {output_details[0]['dtype'].__name__}")
    
    # Run test inference
    print("\n=== Test Inference ===")
    test_image = np.random.rand(1, 224, 224, 3).astype(np.float32)
    
    interpreter.set_tensor(input_details[0]['index'], test_image)
    interpreter.invoke()
    
    output = interpreter.get_tensor(output_details[0]['index'])
    
    print(f"Output: {output[0]}")
    print(f"  Hour angle: {output[0][0]:.2f}°")
    print(f"  Minute angle: {output[0][1]:.2f}°")
    print(f"  Second angle: {output[0][2]:.2f}°")
    print(f"  Confidence: {output[0][3]:.3f}")
    
    # Validate output ranges
    hour_angle, minute_angle, second_angle, confidence = output[0]
    
    print("\n=== Validation ===")
    valid = True
    
    # Note: We're allowing wider ranges since the demo model is untrained
    # Real model should have better constraints
    if not (-360 <= hour_angle <= 720):
        print(f"⚠ Hour angle out of expected range: {hour_angle}")
        valid = False
    
    if not (-360 <= minute_angle <= 720):
        print(f"⚠ Minute angle out of expected range: {minute_angle}")
        valid = False
    
    if not (-360 <= second_angle <= 720):
        print(f"⚠ Second angle out of expected range: {second_angle}")
        valid = False
    
    # Confidence can be any value for untrained model
    print(f"Confidence value: {confidence}")
    
    if valid:
        print("✓ Model validation passed (ranges are acceptable for demo)")
    else:
        print("⚠ Model has some values outside expected ranges (OK for demo)")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Create a demo TFLite model for testing Android integration"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="watch_detector.tflite",
        help="Output path for .tflite file"
    )
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Disable quantization"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip model validation"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Creating Demo Watch Detector Model")
    print("=" * 60)
    print("\nWARNING: This is a DEMO model for testing infrastructure only.")
    print("It will NOT produce accurate time readings from watch images.")
    print("For production use, train models using analog-watch-recognition.\n")
    
    # Create the model
    model = create_simple_demo_model()
    
    # Initialize with mock weights
    initialize_with_mock_weights(model)
    
    # Print model summary
    print("\n=== Model Summary ===")
    model.summary()
    
    # Convert to TFLite
    convert_to_tflite(model, args.output, quantize=not args.no_quantize)
    
    # Validate
    if not args.skip_validation:
        validate_tflite_model(args.output)
    
    print("\n" + "=" * 60)
    print("✓ Demo model created successfully!")
    print("=" * 60)
    print(f"\nModel saved to: {args.output}")
    print("\nNext steps:")
    print(f"  1. Copy to Android assets (if not already there):")
    print(f"     cp {args.output} ../app/src/main/assets/")
    print(f"  2. Build the Android app:")
    print(f"     cd .. && ./gradlew assembleDebug")
    print(f"  3. Install and test on device")
    print("\nNote: This demo model will output random-ish angles.")
    print("For real time detection, train models using analog-watch-recognition.")


if __name__ == "__main__":
    main()
