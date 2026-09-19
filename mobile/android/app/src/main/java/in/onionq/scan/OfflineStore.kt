package `in`.onionq.scan

import android.content.Context
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.util.UUID

/**
 * Offline-first scan journal — the Kotlin mirror of
 * `src/mobile/offline_store.py`.
 *
 * Guarantees that matter in the field:
 *  * append-only: one JSON object per line, flushed to disk immediately;
 *  * nothing is ever deleted — a synced record is *marked*, not removed;
 *  * every record has a client-generated UUID so a retried upload is
 *    idempotent server-side (see `POST /sync/scans`);
 *  * a truncated final line cannot hide earlier records (skipped on read).
 *
 * Reference implementation: not compiled in this repository.
 */
@Serializable
data class ScanRecord(
    val recordId: String = UUID.randomUUID().toString(),
    val kind: String,                      // quick_batch_scan | deep_scan | report
    val centerId: String,
    val deviceId: String,
    val createdAt: String = java.time.Instant.now().toString(),
    var syncState: String = "pending",     // pending | sent | failed
    var attempts: Int = 0,
    var lastError: String? = null,
    var serverHash: String? = null,
    val payloadJson: String,
)

class OfflineStore(context: Context, private val centerId: String,
                   private val deviceId: String) {

    private val json = Json { encodeDefaults = true; prettyPrint = false }
    private val journal = File(context.filesDir, "scans/$centerId/scans.jsonl")
        .apply { parentFile?.mkdirs() }

    fun append(kind: String, payloadJson: String): ScanRecord {
        val record = ScanRecord(kind = kind, centerId = centerId,
                                deviceId = deviceId, payloadJson = payloadJson)
        journal.appendText(json.encodeToString(record) + "\n")
        return record
    }

    fun readAll(): List<ScanRecord> =
        journal.takeIf { it.exists() }
            ?.readLines()
            ?.mapNotNull { line ->
                line.trim().takeIf { it.isNotEmpty() }?.let {
                    runCatching { json.decodeFromString<ScanRecord>(it) }.getOrNull()
                }
            } ?: emptyList()

    fun pending(): List<ScanRecord> = readAll().filter { it.syncState != "sent" }

    /** Marking rewrites the journal atomically; records are never dropped. */
    fun mark(recordId: String, state: String, error: String? = null,
             serverHash: String? = null) {
        val records = readAll().map { record ->
            if (record.recordId == recordId) {
                record.syncState = state
                record.attempts += 1
                record.lastError = error
                if (serverHash != null) record.serverHash = serverHash
            }
            record
        }
        val tmp = File(journal.parentFile, "scans.jsonl.tmp")
        tmp.writeText(records.joinToString("") { json.encodeToString(it) + "\n" })
        tmp.renameTo(journal)
    }

    /**
     * Push pending records. `send` returns the server hash on success and throws
     * on failure; one failure never blocks the rest of the queue.
     */
    fun sync(send: (ScanRecord) -> String): Map<String, Int> {
        var sent = 0
        var failed = 0
        for (record in pending()) {
            try {
                mark(record.recordId, "sent", serverHash = send(record))
                sent++
            } catch (error: Exception) {
                mark(record.recordId, "failed", error = error.message)
                failed++
            }
        }
        return mapOf("sent" to sent, "failed" to failed,
                     "remaining" to pending().size)
    }
}
