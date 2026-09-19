package `in`.onionq.scan

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.graphics.Bitmap
import java.nio.FloatBuffer

/**
 * On-device vision inference (ONNX Runtime Mobile).
 *
 * Two models, both exported from the tracked PyTorch artifacts with a script
 * (see `mobile/android/README.md`):
 *
 *   detector_v0.1.onnx        single-class onion detector (boxes)
 *   attributes_v0.1.onnx      MobileNetV3-Small: 4-class grade + rotten/sprout
 *
 * Honesty rules implemented here:
 *  * if a model file is missing, [available] is false and the caller must show
 *    `model_unavailable` — never a guessed grade;
 *  * only the `rotten` and `sprout` heads feed a decision (the 4-class grade
 *    head measured macro-F1 0.312 on a leak-free split and is reported only);
 *  * the detector returns boxes, not masks, so no defect *area* is produced.
 *
 * Reference implementation: not compiled in this repository (no Android SDK,
 * and `onnx` is not installed to export the artifacts).
 */
class VisionAnalyzer(private val modelDir: String,
                     private val scoreThreshold: Float = 0.5f) {

    private val env: OrtEnvironment = OrtEnvironment.getEnvironment()
    private var detector: OrtSession? = null
    private var attributes: OrtSession? = null

    /** Attribute heads, in the order the Python model defines them. */
    val binaryHeads = listOf("rotten", "sprout")
    val qualityClasses = listOf("extra_class", "class_1", "class_2", "reject")

    var isOnionConfident = false
        private set

    init {
        runCatching {
            detector = env.createSession("$modelDir/detector_v0.1.onnx",
                                         OrtSession.SessionOptions())
        }
        runCatching {
            attributes = env.createSession("$modelDir/attributes_v0.1.onnx",
                                           OrtSession.SessionOptions())
        }
    }

    val available: Boolean get() = attributes != null
    val detectorAvailable: Boolean get() = detector != null

    fun close() {
        detector?.close()
        attributes?.close()
    }

    /** Pre-process: 128x128 RGB, ImageNet normalisation (matches the training code). */
    private fun toInput(bitmap: Bitmap, size: Int): OnnxTensor {
        val scaled = Bitmap.createScaledBitmap(bitmap, size, size, true)
        val mean = floatArrayOf(0.485f, 0.456f, 0.406f)
        val std = floatArrayOf(0.229f, 0.224f, 0.225f)
        val buffer = FloatBuffer.allocate(1 * 3 * size * size)
        val pixels = IntArray(size * size)
        scaled.getPixels(pixels, 0, size, 0, 0, size, size)
        for (channel in 0 until 3) {
            for (pixel in pixels) {
                val value = when (channel) {
                    0 -> ((pixel shr 16) and 0xff) / 255f
                    1 -> ((pixel shr 8) and 0xff) / 255f
                    else -> (pixel and 0xff) / 255f
                }
                buffer.put((value - mean[channel]) / std[channel])
            }
        }
        buffer.rewind()
        return OnnxTensor.createTensor(env, buffer, longArrayOf(1, 3, size.toLong(), size.toLong()))
    }

    private fun softmax(logits: FloatArray): FloatArray {
        val max = logits.maxOrNull() ?: 0f
        val exps = logits.map { kotlin.math.exp((it - max).toDouble()).toFloat() }
        val sum = exps.sum().coerceAtLeast(1e-9f)
        return exps.map { it / sum }.toFloatArray()
    }

    private fun sigmoid(x: Float): Float =
        (1.0 / (1.0 + kotlin.math.exp(-x.toDouble()))).toFloat()

    /**
     * Classify one onion crop. Returns the same contract as the Python side so
     * reports are identical whichever runtime produced them.
     */
    fun classify(crop: Bitmap): Map<String, Any> {
        val session = attributes ?: return mapOf(
            "status" to "model_unavailable",
            "warnings" to listOf("attributes_v0.1.onnx not present in $modelDir"))

        val input = toInput(crop, 128)
        input.use {
            val outputs = session.run(mapOf(session.inputNames.first() to it))
            val values = outputs.use { result ->
                result.map { entry ->
                    val tensor = entry.value as OnnxTensor
                    val buffer = FloatBuffer.allocate(tensor.info.shape.fold(1L) { a, b -> a * b }.toInt())
                    tensor.floatBuffer.forEach { v -> buffer.put(v) }
                    buffer.array()
                }
            }
            val qualityLogits = values.firstOrNull() ?: FloatArray(4)
            val defectLogits = values.getOrNull(1) ?: FloatArray(2)

            val qualityProbs = softmax(qualityLogits)
            val qualityIndex = qualityProbs.indices.maxByOrNull { qualityProbs[it] } ?: 0
            val defects = binaryHeads.mapIndexed { index, name ->
                name to mapOf(
                    "detected" to (defectLogits.getOrNull(index)?.let { sigmoid(it) } ?: 0f) >= 0.5f,
                    "confidence" to (defectLogits.getOrNull(index)?.let { sigmoid(it) } ?: 0f),
                )
            }.toMap()

            val rotten = (defects["rotten"] as Map<*, *>)["detected"] == true
            val sprout = (defects["sprout"] as Map<*, *>)["detected"] == true
            val confidence = maxOf(qualityProbs.maxOrNull() ?: 0f,
                                   (defects.values.maxOfOrNull {
                                       (it as Map<*, *>)["confidence"] as Float
                                   } ?: 0f))
            val label = when {
                rotten -> "visibly_rotten"
                sprout -> "sprouted"
                confidence < 0.55f -> "uncertain"
                else -> "sound"
            }
            return mapOf(
                "status" to "success",
                "is_onion" to isOnionConfident,
                "vision" to mapOf(
                    "label" to label,
                    "confidence" to confidence,
                    "quality_class" to qualityClasses.getOrElse(qualityIndex) { "unknown" },
                    "quality_confidence" to qualityProbs.getOrElse(qualityIndex) { 0f },
                    "defects" to defects,
                    "freshness_score" to null,   // no shelf-life model exists
                    "model_version" to "vision-attributes-v0.1 (onnx)",
                ),
                "warnings" to listOf(
                    "On-device inference. The 4-class grade head is reported but not used " +
                    "for procurement decisions (macro-F1 0.312 on a leak-free split)."),
            )
        }
    }
}
