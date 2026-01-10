#!/usr/bin/env python3
"""
Create a minimal mock .tflite file for testing without TensorFlow dependency.

This creates a placeholder file that the Android build system can package,
allowing us to test the build and integration without a real model.
"""

import struct
import sys

def create_mock_tflite(output_path):
    """Create a minimal mock TFLite file."""
    
    # TFLite files use FlatBuffers format with a specific header
    # This creates a minimal valid structure
    
    # FlatBuffers file identifier for TFLite: "TFL3"
    file_identifier = b'TFL3'
    
    # Create a minimal FlatBuffers structure
    # This won't actually work for inference, but it's a valid file format
    
    with open(output_path, 'wb') as f:
        # Write minimal FlatBuffers header
        # Offset to root table (8 bytes from start)
        f.write(struct.pack('<I', 0))
        # File identifier
        f.write(file_identifier)
        
        # Write some padding to make it look like a real file
        # Real TFLite models are typically several MB
        f.write(b'\x00' * 1024)
    
    print(f"✓ Mock TFLite file created: {output_path}")
    print(f"  Size: {1028} bytes")
    print()
    print("⚠ WARNING: This is a MOCK file for build testing only!")
    print("  It cannot be used for actual inference.")
    print("  To create a real model, run:")
    print("    pip install tensorflow>=2.10.0 numpy")
    print("    python create_demo_model.py --output <path>")

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "watch_detector.tflite"
    create_mock_tflite(output)
