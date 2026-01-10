package com.timereading.app.ml

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Matrix
import android.graphics.Rect
import android.graphics.YuvImage
import android.util.Log
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import org.tensorflow.lite.DataType
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.gpu.CompatibilityList
import org.tensorflow.lite.gpu.GpuDelegate
import org.tensorflow.lite.nnapi.NnApiDelegate
import org.tensorflow.lite.support.common.ops.NormalizeOp
import org.tensorflow.lite.support.image.ImageProcessor
import org.tensorflow.lite.support.image.TensorImage
import org.tensorflow.lite.support.image.ops.ResizeOp
import org.tensorflow.lite.support.tensorbuffer.TensorBuffer
import java.io.ByteArrayOutputStream
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel

/**
 * Analyzer for detecting and reading analog watch dials from camera frames.
 * 
 * This analyzer uses TensorFlow Lite models to:
 * 1. Detect watch faces in the camera frame
 * 2. Identify watch hand positions
 * 3. Extract time from hand angles
 *
 * @param context Application context for loading model assets
 * @param onTimeDetected Callback invoked when time is detected (called on analyzer thread)
 */
class WatchDialAnalyzer(
    private val context: Context,
    private val onTimeDetected: (WatchTime?) -> Unit
) : ImageAnalysis.Analyzer {

    private var interpreter: Interpreter? = null
    private var gpuDelegate: GpuDelegate? = null
    private var nnapiDelegate: NnApiDelegate? = null
    private var isInitialized = false
    private var lastAnalysisTime = 0L
    
    // Model input/output configuration
    private val inputImageWidth = 224
    private val inputImageHeight = 224
    private val outputSize = 4 // [hourAngle, minuteAngle, secondAngle, confidence]

    companion object {
        private const val TAG = "WatchDialAnalyzer"
        private const val MODEL_FILE = "watch_detector.tflite"
        private const val ANALYSIS_INTERVAL_MS = 500L // Analyze every 500ms for performance
    }

    init {
        initializeInterpreter()
    }

    /**
     * Initializes the TensorFlow Lite interpreter with the watch detection model.
     * Attempts to use GPU acceleration if available, with fallback to NNAPI and CPU.
     */
    private fun initializeInterpreter() {
        try {
            val model = loadModelFile()
            if (model != null) {
                // Try GPU acceleration first
                var useGpu = false
                var useNnapi = false
                
                val options = Interpreter.Options().apply {
                    setNumThreads(4)
                    
                    // Try GPU delegate if compatible
                    if (CompatibilityList().isDelegateSupportedOnThisDevice) {
                        try {
                            // Use GpuDelegate constructor without options to avoid NoClassDefFoundError
                            val gpuDelegateOptions = GpuDelegate.Options().apply {
                                setPrecisionLossAllowed(true)
                                setInferencePreference(GpuDelegate.Options.INFERENCE_PREFERENCE_FAST_SINGLE_ANSWER)
                            }
                            gpuDelegate = GpuDelegate(gpuDelegateOptions)
                            addDelegate(gpuDelegate!!)
                            useGpu = true
                            Log.d(TAG, "GPU delegate enabled")
                        } catch (e: Exception) {
                            Log.w(TAG, "GPU delegate not available: ${e.message}")
                            gpuDelegate?.close()
                            gpuDelegate = null
                        }
                    }
                    
                    // Try NNAPI if GPU not available
                    if (!useGpu) {
                        try {
                            nnapiDelegate = NnApiDelegate()
                            addDelegate(nnapiDelegate!!)
                            useNnapi = true
                            Log.d(TAG, "NNAPI delegate enabled")
                        } catch (e: Exception) {
                            Log.w(TAG, "NNAPI not available: ${e.message}")
                            nnapiDelegate?.close()
                            nnapiDelegate = null
                        }
                    }
                }
                
                interpreter = Interpreter(model, options)
                isInitialized = true
                
                val accelType = when {
                    useGpu -> "GPU"
                    useNnapi -> "NNAPI"
                    else -> "CPU"
                }
                Log.d(TAG, "TFLite interpreter initialized successfully (using $accelType)")
            } else {
                Log.w(TAG, "Model file not found, analyzer will use mock detection")
                isInitialized = false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize TFLite interpreter", e)
            gpuDelegate?.close()
            gpuDelegate = null
            nnapiDelegate?.close()
            nnapiDelegate = null
            isInitialized = false
        }
    }

    /**
     * Loads the TFLite model from assets.
     *
     * @return MappedByteBuffer containing the model, or null if not found
     */
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

    override fun analyze(imageProxy: ImageProxy) {
        val currentTime = System.currentTimeMillis()
        
        // Throttle analysis to improve performance
        if (currentTime - lastAnalysisTime < ANALYSIS_INTERVAL_MS) {
            imageProxy.close()
            return
        }
        lastAnalysisTime = currentTime

        try {
            val bitmap = imageProxyToBitmap(imageProxy)
            if (bitmap != null) {
                val watchTime = if (isInitialized && interpreter != null) {
                    analyzeWithModel(bitmap)
                } else {
                    // Use mock detection for demonstration when model is not available
                    analyzeMock()
                }
                onTimeDetected(watchTime)
            } else {
                onTimeDetected(null)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error analyzing image", e)
            onTimeDetected(null)
        } finally {
            imageProxy.close()
        }
    }

    /**
     * Analyzes the image using the TensorFlow Lite model.
     */
    private fun analyzeWithModel(bitmap: Bitmap): WatchTime? {
        val interpreter = this.interpreter ?: return null
        
        try {
            // Preprocess image
            val tensorImage = preprocessImage(bitmap)
            
            // Create output buffer
            val outputBuffer = TensorBuffer.createFixedSize(
                intArrayOf(1, outputSize),
                DataType.FLOAT32
            )
            
            // Run inference
            interpreter.run(tensorImage.buffer, outputBuffer.buffer.rewind())
            
            // Extract results
            val output = outputBuffer.floatArray
            if (output.size >= 4) {
                val angles = HandAngles(
                    hourAngle = output[0],
                    minuteAngle = output[1],
                    secondAngle = output[2]
                )
                val confidence = output[3]
                
                if (confidence > 0.5f) {
                    val time = TimeExtractionHelper.extractTime(angles)
                    return time.copy(confidence = confidence)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error during model inference", e)
        }
        
        return null
    }

    /**
     * Mock analysis for demonstration when no ML model is available.
     * This simulates watch detection by returning a placeholder time.
     */
    private fun analyzeMock(): WatchTime? {
        // In a real implementation, this would not exist
        // For demo purposes, we return null to indicate no watch detected
        // The UI will show appropriate message
        Log.d(TAG, "Mock analysis - no model available")
        return null
    }

    /**
     * Preprocesses the bitmap for model input.
     */
    private fun preprocessImage(bitmap: Bitmap): TensorImage {
        val tensorImage = TensorImage(DataType.FLOAT32)
        tensorImage.load(bitmap)
        
        val imageProcessor = ImageProcessor.Builder()
            .add(ResizeOp(inputImageHeight, inputImageWidth, ResizeOp.ResizeMethod.BILINEAR))
            .add(NormalizeOp(0f, 255f)) // Normalize to [0, 1]
            .build()
        
        return imageProcessor.process(tensorImage)
    }

    /**
     * Converts ImageProxy to Bitmap.
     */
    private fun imageProxyToBitmap(imageProxy: ImageProxy): Bitmap? {
        val planes = imageProxy.planes
        if (planes.isEmpty()) return null

        return try {
            when (imageProxy.format) {
                ImageFormat.YUV_420_888 -> yuvToRgbBitmap(imageProxy)
                else -> {
                    Log.w(TAG, "Unsupported image format: ${imageProxy.format}")
                    null
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error converting ImageProxy to Bitmap", e)
            null
        }
    }

    /**
     * Converts YUV_420_888 format to RGB Bitmap.
     */
    private fun yuvToRgbBitmap(imageProxy: ImageProxy): Bitmap? {
        val yBuffer = imageProxy.planes[0].buffer
        val uBuffer = imageProxy.planes[1].buffer
        val vBuffer = imageProxy.planes[2].buffer

        val ySize = yBuffer.remaining()
        val uSize = uBuffer.remaining()
        val vSize = vBuffer.remaining()

        val nv21 = ByteArray(ySize + uSize + vSize)
        yBuffer.get(nv21, 0, ySize)
        vBuffer.get(nv21, ySize, vSize)
        uBuffer.get(nv21, ySize + vSize, uSize)

        val yuvImage = YuvImage(
            nv21,
            ImageFormat.NV21,
            imageProxy.width,
            imageProxy.height,
            null
        )

        val out = ByteArrayOutputStream()
        yuvImage.compressToJpeg(Rect(0, 0, imageProxy.width, imageProxy.height), 80, out)
        val imageBytes = out.toByteArray()
        val bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)

        // Rotate bitmap based on image rotation
        return rotateBitmap(bitmap, imageProxy.imageInfo.rotationDegrees)
    }

    /**
     * Rotates bitmap by the specified degrees.
     */
    private fun rotateBitmap(bitmap: Bitmap, rotationDegrees: Int): Bitmap {
        if (rotationDegrees == 0) return bitmap

        val matrix = Matrix().apply {
            postRotate(rotationDegrees.toFloat())
        }

        return Bitmap.createBitmap(
            bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true
        )
    }

    /**
     * Releases resources held by this analyzer.
     */
    fun close() {
        interpreter?.close()
        interpreter = null
        gpuDelegate?.close()
        gpuDelegate = null
        nnapiDelegate?.close()
        nnapiDelegate = null
        isInitialized = false
    }
}
