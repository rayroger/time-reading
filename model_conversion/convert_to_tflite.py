#!/usr/bin/env python3
"""
Convert TensorFlow SavedModel to TensorFlow Lite format with optimizations.

This script takes a SavedModel and converts it to TensorFlow Lite format,
applying various optimizations like quantization for mobile deployment.

Requirements:
    pip install tensorflow>=2.10.0

Usage:
    # Convert with dynamic range quantization (recommended)
    python convert_to_tflite.py --model-path saved_models/unified_model --output watch_detector.tflite --quantize dynamic

    # Convert with float16 quantization
    python convert_to_tflite.py --model-path saved_models/unified_model --output watch_detector.tflite --quantize float16

    # Convert without quantization
    python convert_to_tflite.py --model-path saved_models/unified_model --output watch_detector.tflite
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import tensorflow as tf
    import numpy as np
except ImportError:
    print("Error: TensorFlow not installed. Please run: pip install tensorflow>=2.10.0")
    sys.exit(1)


def representative_dataset_gen(image_dir):
    """
    Yield preprocessed watch images for full integer quantization calibration.
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
    image_paths = sorted(
        path for path in Path(image_dir).iterdir()
        if path.is_file() and path.suffix.lower() in image_extensions
    )
    if not image_paths:
        raise ValueError(f"No supported calibration images found in {image_dir}")

    for image_path in image_paths:
        image_data = tf.io.read_file(str(image_path))
        image = tf.io.decode_image(image_data, channels=3, expand_animations=False)
        image = tf.image.convert_image_dtype(image, tf.float32)
        image = tf.image.resize(image, [224, 224])
        yield [image[tf.newaxis, ...].numpy()]


def convert_to_tflite(
    model_path,
    output_path,
    quantization="none",
    optimize_for_size=True,
    representative_data_dir=None,
):
    """
    Convert SavedModel to TensorFlow Lite format.
    
    Args:
        model_path: Path to the SavedModel directory
        output_path: Output path for the .tflite file
        quantization: Type of quantization ("none", "dynamic", "float16", "int8")
        optimize_for_size: Whether to optimize for model size
    
    Returns:
        Path to the generated .tflite file or None on error
    """
    print(f"Converting model from {model_path} to TensorFlow Lite...")
    print(f"Quantization: {quantization}")
    
    try:
        if quantization == "int8":
            if not representative_data_dir or not os.path.isdir(representative_data_dir):
                raise ValueError(
                    "Int8 quantization requires --representative-data-dir "
                    "containing representative watch images"
                )

        # Create the converter
        converter = tf.lite.TFLiteConverter.from_saved_model(model_path)
        
        # Set default optimizations
        if optimize_for_size:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Configure quantization
        if quantization == "dynamic":
            # Dynamic range quantization (recommended for most cases)
            # Quantizes weights to int8, keeps activations as float
            # Reduces model size by ~4x with minimal accuracy loss
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            print("Using dynamic range quantization (weights -> int8)")
            
        elif quantization == "float16":
            # Float16 quantization
            # Reduces model size by ~2x, faster on GPU
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
            print("Using float16 quantization")
            
        elif quantization == "int8":
            # Full integer quantization
            # Quantizes model operations to int8 while keeping the external
            # interface float32, as required by WatchDialAnalyzer.
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.representative_dataset = lambda: representative_dataset_gen(
                representative_data_dir
            )
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type = tf.float32
            converter.inference_output_type = tf.float32
            print("Using int8 operation quantization with float32 input/output")
            
        else:  # quantization == "none"
            # No quantization, keep as float32
            print("No quantization (float32)")
        
        # Convert the model
        print("Converting...")
        tflite_model = converter.convert()
        
        # Save to file
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        # Get file size
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        print(f"\n✓ Conversion successful!")
        print(f"  Output: {output_path}")
        print(f"  Size: {file_size_mb:.2f} MB")
        
        return output_path
        
    except Exception as e:
        print(f"\n✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def validate_tflite_model(tflite_path):
    """
    Validate the converted TensorFlow Lite model.
    
    Args:
        tflite_path: Path to the .tflite file
    
    Returns:
        True if validation succeeds, False otherwise
    """
    print(f"\nValidating TFLite model: {tflite_path}")
    
    try:
        # Load the TFLite model
        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        interpreter.allocate_tensors()
        
        # Get input and output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print("\n=== Model Information ===")
        print(f"Input shape: {input_details[0]['shape']}")
        print(f"Input type: {input_details[0]['dtype']}")
        print(f"Output shape: {output_details[0]['shape']}")
        print(f"Output type: {output_details[0]['dtype']}")
        
        # Test inference with random data
        print("\n=== Testing Inference ===")
        input_shape = input_details[0]['shape']
        input_dtype = input_details[0]['dtype']
        
        # Create test input
        if input_dtype == np.uint8:
            test_input = np.random.randint(0, 256, size=input_shape, dtype=np.uint8)
        else:
            test_input = np.random.rand(*input_shape).astype(np.float32)
        
        # Run inference
        interpreter.set_tensor(input_details[0]['index'], test_input)
        interpreter.invoke()
        
        # Get output
        output_data = interpreter.get_tensor(output_details[0]['index'])
        print(f"Output: {output_data}")
        print(f"Output shape: {output_data.shape}")
        
        print("\n✓ Validation successful!")
        return True
        
    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert TensorFlow SavedModel to TensorFlow Lite"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to SavedModel directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path for .tflite file"
    )
    parser.add_argument(
        "--quantize",
        choices=["none", "dynamic", "float16", "int8"],
        default="dynamic",
        help="Quantization method (default: dynamic)"
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable size optimization"
    )
    parser.add_argument(
        "--representative-data-dir",
        type=str,
        help="Directory of representative watch images required for int8 quantization"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Validate the converted model (default: True)"
    )
    
    args = parser.parse_args()
    
    # Check if model path exists
    if not os.path.exists(args.model_path):
        print(f"Error: Model path not found: {args.model_path}")
        sys.exit(1)
    
    # Convert the model
    tflite_path = convert_to_tflite(
        args.model_path,
        args.output,
        args.quantize,
        not args.no_optimize,
        args.representative_data_dir
    )
    
    if tflite_path and args.validate:
        validate_tflite_model(tflite_path)
    
    if tflite_path:
        print(f"\n✓ All done! TFLite model ready at: {tflite_path}")
        print(f"\nNext steps:")
        print(f"  1. Copy the model to Android assets:")
        print(f"     cp {tflite_path} ../app/src/main/assets/")
        print(f"  2. Rebuild the Android app")
        print(f"  3. Test on device")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
