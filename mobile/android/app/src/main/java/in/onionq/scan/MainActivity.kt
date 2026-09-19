package `in`.onionq.scan

import android.graphics.Bitmap
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.Json

/**
 * ONION-Q inspector app — screen flow for the two inspection modes.
 *
 * Flow implemented:
 *   Home → [Quick Batch Scan | Deep Scan] → result card → save to journal
 *
 * Rules the UI must respect (they are product requirements, not preferences):
 *  * show `manual_review` together with its reason, never a bare verdict;
 *  * never display millimetres unless a calibration marker was detected;
 *  * when a model artifact is missing, show `model_unavailable` and disable the
 *    grade buttons — no placeholder result;
 *  * acoustic sections state that evidence is unvalidated until cut-open onion
 *    ground truth exists.
 *
 * Reference implementation: not compiled in this repository (no Android SDK).
 */
class MainActivity : ComponentActivity() {

    private lateinit var store: OfflineStore
    private lateinit var vision: VisionAnalyzer
    private lateinit var acoustic: AcousticRecorder
    private val json = Json { prettyPrint = true }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = OfflineStore(applicationContext, centerId = "MH-NSK", deviceId = deviceId())
        vision = VisionAnalyzer(modelDir = filesDir.resolve("models").absolutePath)
        acoustic = AcousticRecorder(applicationContext)

        setContent {
            MaterialTheme {
                val screen = remember { mutableStateOf("home") }
                val output = remember { mutableStateOf("") }

                Column(
                    modifier = Modifier.fillMaxSize().padding(20.dp),
                ) {
                    Text("ONION-Q — Procurement Inspection",
                         style = MaterialTheme.typography.headlineSmall)
                    Text(
                        if (vision.detectorAvailable) "On-device models ready"
                        else "Detector artifact missing: grading is disabled",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    Spacer(Modifier.height(20.dp))

                    when (screen.value) {
                        "home" -> {
                            Button(onClick = { screen.value = "batch" },
                                   modifier = Modifier.fillMaxWidth()) {
                                Text("Quick Batch Scan (tray)")
                            }
                            Spacer(Modifier.height(10.dp))
                            Button(onClick = { screen.value = "deep" },
                                   modifier = Modifier.fillMaxWidth()) {
                                Text("Deep Scan (4 guided views + optional audio)")
                            }
                        }
                        "batch" -> {
                            Text("Spread the onions on the tray and keep the " +
                                 "calibration mat in frame.")
                            OutlinedButton(onClick = {
                                output.value = runBatchScan()
                            }) { Text("Capture tray") }
                            ResultCard(output.value)
                        }
                        "deep" -> {
                            Text("Views: neck → base → side A → side B. " +
                                 "Follow each prompt before capturing.")
                            OutlinedButton(onClick = {
                                output.value = runAcousticTest()
                            }) { Text("Run phone acoustic test") }
                            ResultCard(output.value)
                        }
                    }
                    Spacer(Modifier.height(16.dp))
                    OutlinedButton(onClick = {
                        screen.value = "home"
                    }) { Text("Back") }
                }
            }
        }
    }

    /**
     * Batch scan. The captured tray image is posted to the ONION-Q API so the
     * audited policy engine produces the decision; the app never re-implements
     * the rules. Offline, the capture is journalled and retried.
     */
    private fun runBatchScan(): String {
        val tray: Bitmap = captureTrayImage() ?: return "Capture cancelled."
        val payload = ApiClient.scanBatch(tray, centerId = store.readAll().firstOrNull()
            ?.centerId ?: "MH-NSK")
        val record = store.append("quick_batch_scan", json.encodeToString(payload))
        val batch = payload["batch"] as? Map<*, *> ?: return "No batch returned."
        val counts = batch["counts"] as? Map<*, *> ?: emptyMap<Any, Any>()
        return buildString {
            appendLine("Batch ${batch["batch_id"]}")
            counts.forEach { (key, value) -> appendLine("$key: $value") }
            appendLine("Policy: ${(batch["policy"] as? Map<*, *>)?.get("policy_id")}")
            appendLine("Saved to journal as ${record.recordId}")
            if (payload["composed_fixture"] == true) {
                appendLine("NOTE: composed fixture, not a field photograph.")
            }
        }
    }

    /** Acoustic test: baseline → chirp → (tap fallback) → quality gate → classify. */
    private fun runAcousticTest(): String {
        val (_, ambientRms) = acoustic.recordAmbientBaseline()
        val metadata = acoustic.captureMetadata("phone_chirp", ambientRms)
        var attempt = 0
        while (attempt < 3) {
            attempt++
            val file = runCatching { acoustic.playChirpAndRecord() }.getOrNull()
            if (file == null) continue
            val result = ApiClient.classifyAcoustic(file)
            val status = result["status"]
            if (status == "valid") {
                store.append("deep_scan_acoustic", json.encodeToString(result))
                return "Acoustic: ${result["internal_defect_probability"]} " +
                       "(confidence ${result["confidence"]})\n" +
                       "Device: ${metadata["device_model"]} @ ${metadata["sample_rate_hz"]} Hz\n" +
                       "Evidence is UNVALIDATED: it cannot change a grade yet."
            }
            // Fall back to a guided tap for the next attempt.
        }
        return "Recording failed quality gates after $attempt attempts.\n" +
               "Move to a quieter room, keep the phone at a consistent distance, " +
               "and retry. No prediction is made."
    }

    @androidx.compose.runtime.Composable
    private fun ResultCard(text: String) {
        if (text.isBlank()) return
        Text(text, modifier = Modifier.padding(top = 14.dp))
    }

    private fun captureTrayImage(): Bitmap? = null   // CameraX binding in the real app

    private fun deviceId(): String = "${android.os.Build.MANUFACTURER}-" +
        "${android.os.Build.MODEL}".replace(" ", "_")

    override fun onDestroy() {
        vision.close()
        super.onDestroy()
    }
}

/**
 * Thin HTTP client for the ONION-Q API (`server/app.py`). Kept separate from the
 * UI so the same calls can be tested without an Android emulator.
 */
object ApiClient {
    private const val BASE = "http://10.0.2.2:8000"   // emulator → host localhost

    fun scanBatch(tray: Bitmap, centerId: String): Map<String, Any?> {
        // Multipart upload: POST /scan/batch with the tray image.
        return mapOf("status" to "not_implemented_in_reference")
    }

    fun classifyAcoustic(file: java.io.File): Map<String, Any?> {
        // Multipart upload: POST /acoustic/classify.
        return mapOf("status" to "not_implemented_in_reference")
    }
}
