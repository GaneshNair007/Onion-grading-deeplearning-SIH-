package `in`.onionq.scan

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioRecord
import android.media.AudioTrack
import android.media.MediaRecorder
import android.os.Build
import java.io.File
import kotlin.math.PI
import kotlin.math.ln
import kotlin.math.sin

/**
 * Phone-only acoustic capture (no piezo, no USB ADC, no external hardware).
 *
 * Flow implemented here:
 *   1. [recordAmbientBaseline]  – ~1 s of room noise, used to refuse a noisy room
 *   2. [playChirpAndRecord]     – logarithmic chirp playback + simultaneous capture
 *   3. [recordGuidedTap]        – fallback when the chirp path fails quality gates
 *   4. [captureMetadata]        – device provenance required for every recording
 *
 * The Kotlin side only *captures*. Quality gates, features and the classifier
 * live in the shared Python pipeline (`src/acoustic/`), so the app and the
 * desktop demo cannot disagree about what a valid recording is.
 *
 * Reference implementation: not compiled in this repository (no Android SDK).
 */
class AcousticRecorder(private val context: Context) {

    companion object {
        const val SAMPLE_RATE = 48_000
        const val CHIRP_F0_HZ = 100.0
        const val CHIRP_F1_HZ = 8_000.0
        const val CHIRP_DURATION_S = 1.0
        const val RECORD_DURATION_S = 1.6
        const val MAX_ATTEMPTS = 3
        const val LABEL = "ONIONQ_ACOUSTIC"
    }

    /** Device provenance: phone speakers/mics are NOT consistent across devices. */
    fun captureMetadata(captureMethod: String, ambientRms: Double?): Map<String, Any> = mapOf(
        "device_model" to "${Build.MANUFACTURER} ${Build.MODEL}",
        "os_version" to "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})",
        "sample_rate_hz" to SAMPLE_RATE,
        "capture_method" to captureMethod,            // phone_chirp | phone_tap
        "recorded_volume_setting" to volumeSetting(),
        "ambient_noise_score" to (ambientRms ?: -1.0),
        "recorded_at" to java.time.Instant.now().toString(),
    )

    private fun volumeSetting(): String {
        val am = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC).coerceAtLeast(1)
        val now = am.getStreamVolume(AudioManager.STREAM_MUSIC)
        return "$now/$max"
    }

    /** Step 1 — room baseline. Return the RMS so the shared gate can judge it. */
    fun recordAmbientBaseline(seconds: Double = 1.0): Pair<File, Double> {
        val frames = (SAMPLE_RATE * seconds).toInt()
        val pcm = shortArrayOf().toMutableList()
        readInto(pcm, frames)
        val rms = kotlin.math.sqrt(pcm.sumOf { (it / 32768.0) * (it / 32768.0) } /
                                   pcm.size.coerceAtLeast(1))
        val file = writeWav(pcm.toShortArray(), "ambient_baseline.wav")
        return file to rms
    }

    /** Step 2 — chirp + capture in one pass (the app's primary measurement). */
    fun playChirpAndRecord(): File {
        val playback = Thread { playLogChirp() }
        playback.start()
        return record(RECORD_DURATION_S, "chirp_response.wav").also { playback.join() }
    }

    /** Step 3 — standardised tap fallback guided by the UI. */
    fun recordGuidedTap(seconds: Double = RECORD_DURATION_S): File =
        record(seconds, "tap_response.wav")

    private fun record(seconds: Double, name: String): File {
        val pcm = shortArrayOf().toMutableList()
        readInto(pcm, (SAMPLE_RATE * seconds).toInt())
        return writeWav(pcm.toShortArray(), name)
    }

    private fun readInto(sink: MutableList<Short>, frames: Int) {
        val minBuf = AudioRecord.getMinBufferSize(
            SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        val record = AudioRecord(
            MediaRecorder.AudioSource.UNPROCESSED,   // avoid vendor AGC/EQ where possible
            SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT, maxOf(minBuf, frames * 2))
        val buffer = ShortArray(frames)
        record.startRecording()
        var read = 0
        while (read < frames) {
            val n = record.read(buffer, read, frames - read)
            if (n <= 0) break
            read += n
        }
        record.stop()
        record.release()
        sink.addAll(buffer.take(read))
    }

    /** Logarithmic chirp: equal time per octave, matching the Python generator. */
    private fun playLogChirp() {
        val frames = (SAMPLE_RATE * CHIRP_DURATION_S).toInt()
        val pcm = ShortArray(frames)
        val k = ln(CHIRP_F1_HZ / CHIRP_F0_HZ) / CHIRP_DURATION_S
        for (i in 0 until frames) {
            val t = i.toDouble() / SAMPLE_RATE
            val phase = 2.0 * PI * CHIRP_F0_HZ * (kotlin.math.exp(k * t) - 1.0) / k
            val envelope = 0.6 * (1.0 - t / CHIRP_DURATION_S)   // taper to avoid a click
            pcm[i] = (envelope * sin(phase) * Short.MAX_VALUE).toInt().toShort()
        }
        val track = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build())
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setSampleRate(SAMPLE_RATE)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .build())
            .setTransferMode(AudioTrack.MODE_STATIC)
            .setBufferSizeInBytes(pcm.size * 2)
            .build()
        track.write(pcm, 0, pcm.size)
        track.play()
        Thread.sleep(((CHIRP_DURATION_S + 0.1) * 1000).toLong())
        track.stop()
        track.release()
    }

    private fun writeWav(pcm: ShortArray, name: String): File {
        val dir = File(context.filesDir, "acoustic").apply { mkdirs() }
        val file = File(dir, name)
        val pcmBytes = pcm.size * 2
        val header = ByteArray(44)
        fun putInt(offset: Int, value: Int) {
            header[offset] = (value and 0xff).toByte()
            header[offset + 1] = ((value shr 8) and 0xff).toByte()
            header[offset + 2] = ((value shr 16) and 0xff).toByte()
            header[offset + 3] = ((value shr 24) and 0xff).toByte()
        }
        fun putShort(offset: Int, value: Int) {
            header[offset] = (value and 0xff).toByte()
            header[offset + 1] = ((value shr 8) and 0xff).toByte()
        }
        "RIFF".forEachIndexed { i, c -> header[i] = c.code.toByte() }
        putInt(4, 36 + pcmBytes)
        "WAVE".forEachIndexed { i, c -> header[8 + i] = c.code.toByte() }
        "fmt ".forEachIndexed { i, c -> header[12 + i] = c.code.toByte() }
        putInt(16, 16); putShort(20, 1); putShort(22, 1)
        putInt(24, SAMPLE_RATE); putInt(28, SAMPLE_RATE * 2)
        putShort(32, 2); putShort(34, 16)
        "data".forEachIndexed { i, c -> header[36 + i] = c.code.toByte() }
        putInt(40, pcmBytes)

        file.outputStream().use { out ->
            out.write(header)
            val bytes = ByteArray(pcmBytes)
            for (i in pcm.indices) {
                bytes[i * 2] = (pcm[i].toInt() and 0xff).toByte()
                bytes[i * 2 + 1] = ((pcm[i].toInt() shr 8) and 0xff).toByte()
            }
            out.write(bytes)
        }
        return file
    }
}
