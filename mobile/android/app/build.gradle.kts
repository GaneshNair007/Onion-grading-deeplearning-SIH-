// ONION-Q Android — reference module build file.
//
// NOT COMPILED in this repository: no Android SDK/Gradle toolchain is available
// in the development environment. Kept as the documented integration boundary.
//
// Build (with an Android SDK and JDK 17+):
//     gradle :app:assembleDebug

plugins {
    id("com.android.application") version "8.5.2"
    kotlin("android") version "1.9.24"
    kotlin("plugin.serialization") version "1.9.24"
}

android {
    namespace = "in.onionq.scan"
    compileSdk = 34

    defaultConfig {
        applicationId = "in.onionq.scan"
        minSdk = 26              // CameraX + AudioRecord UNPROCESSED source
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures { compose = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.14" }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    packaging {
        resources.excludes += setOf("META-INF/{AL2.0,LGPL2.1}")
    }
}

dependencies {
    // Camera + guided capture UI
    implementation("androidx.camera:camera-core:1.3.4")
    implementation("androidx.camera:camera-camera2:1.3.4")
    implementation("androidx.camera:camera-lifecycle:1.3.4")
    implementation("androidx.camera:camera-view:1.3.4")

    // Compose UI
    implementation("androidx.compose.ui:ui:1.6.8")
    implementation("androidx.compose.material3:material3:1.2.1")
    implementation("androidx.activity:activity-compose:1.9.0")

    // On-device inference (models exported from the tracked PyTorch artifacts)
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.18.0")

    // Offline-first sync
    implementation("androidx.work:work-runtime-ktx:2.9.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")

    // HTTP to the ONION-Q API (server/app.py)
    implementation("com.squareup.okhttp3:okhttp:4.12.0")

    testImplementation("junit:junit:4.13.2")
}

// Reminder: the policy engine is NOT reimplemented here. Decisions come from
// the API (or a verified port of config/grading/*.json), because a mobile copy
// of the rules would silently drift from the audited version.
