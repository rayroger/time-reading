#!/usr/bin/env python3
"""
Export TensorFlow models from akucia/analog-watch-recognition as SavedModel format.

This script loads trained models from the analog-watch-recognition repository
and exports them in TensorFlow SavedModel format, which is the first step
before converting to TensorFlow Lite.

Requirements:
    pip install tensorflow>=2.10.0 watch_recognition

Usage:
    python export_savedmodel.py --model-type segmentation --checkpoint-path path/to/checkpoint --output-dir saved_models/
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import tensorflow as tf
except ImportError:
    print("Error: TensorFlow not installed. Please run: pip install tensorflow>=2.10.0")
    sys.exit(1)


def export_segmentation_model(checkpoint_path, output_dir):
    """
    Export the hand segmentation model as SavedModel.
    
    Args:
        checkpoint_path: Path to the trained model checkpoint
        output_dir: Directory to save the exported model
    """
    print(f"Exporting segmentation model from {checkpoint_path}")
    
    try:
        # Load the model
        # Note: This is a placeholder - actual implementation would depend on
        # the model architecture from analog-watch-recognition
        model = tf.keras.models.load_model(checkpoint_path)
        
        # Define the serving signature
        @tf.function(input_signature=[tf.TensorSpec(shape=[None, 224, 224, 3], dtype=tf.float32)])
        def serving_fn(input_tensor):
            """Serving function for the segmentation model."""
            return model(input_tensor, training=False)
        
        # Export as SavedModel
        output_path = os.path.join(output_dir, "segmentation_model")
        tf.saved_model.save(
            model,
            output_path,
            signatures={'serving_default': serving_fn}
        )
        
        print(f"✓ Segmentation model exported to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error exporting segmentation model: {e}")
        return None


def export_detector_model(checkpoint_path, output_dir):
    """
    Export the bbox detector model as SavedModel.
    
    Args:
        checkpoint_path: Path to the trained model checkpoint
        output_dir: Directory to save the exported model
    """
    print(f"Exporting detector model from {checkpoint_path}")
    
    try:
        # Load the model
        model = tf.keras.models.load_model(checkpoint_path)
        
        # Define the serving signature
        @tf.function(input_signature=[tf.TensorSpec(shape=[None, None, None, 3], dtype=tf.float32)])
        def serving_fn(input_tensor):
            """Serving function for the detector model."""
            return model(input_tensor, training=False)
        
        # Export as SavedModel
        output_path = os.path.join(output_dir, "detector_model")
        tf.saved_model.save(
            model,
            output_path,
            signatures={'serving_default': serving_fn}
        )
        
        print(f"✓ Detector model exported to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error exporting detector model: {e}")
        return None


def export_keypoint_model(checkpoint_path, output_dir):
    """
    Export the keypoint detection model as SavedModel.
    
    Args:
        checkpoint_path: Path to the trained model checkpoint
        output_dir: Directory to save the exported model
    """
    print(f"Exporting keypoint model from {checkpoint_path}")
    
    try:
        # Load the model
        model = tf.keras.models.load_model(checkpoint_path)
        
        # Define the serving signature
        @tf.function(input_signature=[tf.TensorSpec(shape=[None, 224, 224, 3], dtype=tf.float32)])
        def serving_fn(input_tensor):
            """Serving function for the keypoint model."""
            return model(input_tensor, training=False)
        
        # Export as SavedModel
        output_path = os.path.join(output_dir, "keypoint_model")
        tf.saved_model.save(
            model,
            output_path,
            signatures={'serving_default': serving_fn}
        )
        
        print(f"✓ Keypoint model exported to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error exporting keypoint model: {e}")
        return None


def create_unified_model(segmentation_path, keypoint_path, output_dir):
    """
    Create a unified model that combines segmentation and keypoint detection
    to directly output hand angles.
    
    Args:
        segmentation_path: Path to segmentation SavedModel
        keypoint_path: Path to keypoint SavedModel
        output_dir: Directory to save the unified model
    """
    print("Creating unified watch detector model...")
    
    try:
        # Load the individual models
        segmentation_model = tf.saved_model.load(segmentation_path)
        keypoint_model = tf.saved_model.load(keypoint_path)
        
        # Define the unified inference function
        @tf.function(input_signature=[tf.TensorSpec(shape=[1, 224, 224, 3], dtype=tf.float32)])
        def unified_inference(input_image):
            """
            Unified inference that outputs hand angles directly.
            
            NOTE: This is a PLACEHOLDER implementation. The actual post-processing
            to extract angles from segmentation masks requires implementing:
            1. KDE (Kernel Density Estimation) to separate hour/minute hands
            2. Line fitting to extract hand orientations
            3. Angle calculation relative to keypoint top position
            
            For production use, you need to either:
            - Implement the full post-processing pipeline (see analog-watch-recognition)
            - Use the models separately in Android and do post-processing in Kotlin
            - Train an end-to-end model that directly outputs angles
            
            Returns:
                Tensor of shape [1, 4] containing:
                [hourAngle, minuteAngle, secondAngle, confidence]
            """
            # Get segmentation mask
            seg_output = segmentation_model.signatures['serving_default'](input_image)
            
            # Get keypoints (center and top)
            kp_output = keypoint_model.signatures['serving_default'](input_image)
            
            # TODO: Complete post-processing implementation
            # The following would be needed for a production-ready unified model:
            # 1. Extract hand pixels from segmentation mask (seg_output)
            # 2. Use KDE to separate pixels into hour/minute hand clusters
            # 3. Fit lines to each cluster to get hand directions
            # 4. Calculate angles from center to line endpoints, relative to top keypoint
            # 5. Determine confidence based on segmentation quality and consistency
            
            # PLACEHOLDER: Return zeros (this won't produce accurate results)
            # Replace this with actual angle extraction logic
            hour_angle = tf.constant([[0.0]], dtype=tf.float32)
            minute_angle = tf.constant([[0.0]], dtype=tf.float32)
            second_angle = tf.constant([[0.0]], dtype=tf.float32)
            confidence = tf.constant([[0.0]], dtype=tf.float32)
            
            output = tf.concat([hour_angle, minute_angle, second_angle, confidence], axis=1)
            return output
        
        # Create a module to save
        class UnifiedModel(tf.Module):
            def __init__(self):
                super().__init__()
                self.seg_model = segmentation_model
                self.kp_model = keypoint_model
            
            @tf.function(input_signature=[tf.TensorSpec(shape=[1, 224, 224, 3], dtype=tf.float32)])
            def __call__(self, x):
                return unified_inference(x)
        
        unified = UnifiedModel()
        
        # Export as SavedModel
        output_path = os.path.join(output_dir, "unified_model")
        tf.saved_model.save(unified, output_path)
        
        print(f"✓ Unified model created at {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error creating unified model: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Export models from analog-watch-recognition as SavedModel"
    )
    parser.add_argument(
        "--model-type",
        choices=["segmentation", "detector", "keypoint", "unified"],
        required=True,
        help="Type of model to export"
    )
    parser.add_argument(
        "--checkpoint-path",
        type=str,
        help="Path to model checkpoint (not needed for unified)"
    )
    parser.add_argument(
        "--segmentation-model",
        type=str,
        help="Path to segmentation SavedModel (for unified model)"
    )
    parser.add_argument(
        "--keypoint-model",
        type=str,
        help="Path to keypoint SavedModel (for unified model)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="saved_models",
        help="Output directory for SavedModel"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Export based on model type
    if args.model_type == "segmentation":
        if not args.checkpoint_path:
            print("Error: --checkpoint-path required for segmentation model")
            sys.exit(1)
        export_segmentation_model(args.checkpoint_path, args.output_dir)
        
    elif args.model_type == "detector":
        if not args.checkpoint_path:
            print("Error: --checkpoint-path required for detector model")
            sys.exit(1)
        export_detector_model(args.checkpoint_path, args.output_dir)
        
    elif args.model_type == "keypoint":
        if not args.checkpoint_path:
            print("Error: --checkpoint-path required for keypoint model")
            sys.exit(1)
        export_keypoint_model(args.checkpoint_path, args.output_dir)
        
    elif args.model_type == "unified":
        if not args.segmentation_model or not args.keypoint_model:
            print("Error: --segmentation-model and --keypoint-model required for unified model")
            sys.exit(1)
        create_unified_model(args.segmentation_model, args.keypoint_model, args.output_dir)
    
    print("\n✓ Export complete!")


if __name__ == "__main__":
    main()
