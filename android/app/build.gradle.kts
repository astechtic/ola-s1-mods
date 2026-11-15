import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

// Release signing is read from keystore.properties (git-ignored) or CI env vars.
// Contributors without a keystore fall back to the debug key so the build still works;
// official/CI release builds must provide a real keystore. See docs/BUILD.md.
val keystorePropsFile = rootProject.file("keystore.properties")
val keystoreProps = Properties().apply {
    if (keystorePropsFile.exists()) keystorePropsFile.inputStream().use { load(it) }
}
val hasReleaseKeystore = keystorePropsFile.exists() ||
    System.getenv("S1MODS_KEYSTORE_FILE") != null

android {
    namespace = "com.asjohn720.s1mods"
    compileSdk {
        version = release(37) {
            minorApiLevel = 1
        }
    }

    defaultConfig {
        applicationId = "com.asjohn720.s1mods"
        minSdk = 26
        targetSdk = 35
        versionCode = 5
        versionName = "1.2"

        vectorDrawables.useSupportLibrary = true

        // GitHub repo that holds the public Releases used for update checks.
        buildConfigField("String", "GIT_OWNER", "\"Asjohn720\"")
        buildConfigField("String", "GIT_REPO", "\"ola-s1-mods\"")
    }

    signingConfigs {
        if (hasReleaseKeystore) {
            create("release") {
                storeFile = rootProject.file(
                    System.getenv("S1MODS_KEYSTORE_FILE")
                        ?: keystoreProps.getProperty("storeFile")
                )
                storePassword = System.getenv("S1MODS_KEYSTORE_PASSWORD")
                    ?: keystoreProps.getProperty("storePassword")
                keyAlias = System.getenv("S1MODS_KEY_ALIAS")
                    ?: keystoreProps.getProperty("keyAlias")
                keyPassword = System.getenv("S1MODS_KEY_PASSWORD")
                    ?: keystoreProps.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            signingConfig = if (hasReleaseKeystore) {
                signingConfigs.getByName("release")
            } else {
                logger.warn("S1Mods: no release keystore found; release build will be DEBUG-signed. See docs/BUILD.md.")
                signingConfigs.getByName("debug")
            }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    // Mod APKs live in the top-level apks/ (single source of truth). They are copied into a
    // generated assets dir at build time instead of being committed under src/main/assets.
    sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("generated/modApks"))

    packaging {
        resources {
            excludes += setOf(
                "META-INF/INDEX.LIST",
                "META-INF/io.netty.versions.properties",
                "META-INF/DEPENDENCIES",
                "META-INF/LICENSE",
                "META-INF/LICENSE.txt",
                "META-INF/license.txt",
                "META-INF/NOTICE",
                "META-INF/NOTICE.txt",
                "META-INF/notice.txt"
            )
        }
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons.extended)

    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.coroutines.android)

    // Embedded Pure Kotlin ADB Client
    implementation(libs.dadb)

    // Root gRPC Client for Scooter Port 50005
    implementation(libs.grpc.okhttp)
    implementation(libs.grpc.stub)

    debugImplementation(libs.androidx.compose.ui.tooling)
}

// --- Mod APK sync -----------------------------------------------------------
// Copies the bundled mod APKs from the repo's top-level apks/ into the generated
// assets dir (registered as an assets srcDir above). Keeps a single source of truth
// and avoids committing duplicate binaries under src/main/assets.
val bundledModApks = listOf(
    "balls-1.1.0-lite-release.apk",
    "musicmod-release.apk",
    "com.asjohn720.androidauto.apk",
)

val syncModApks by tasks.registering(Copy::class) {
    description = "Copy bundled mod APKs from //apks into generated assets"
    val apksDir = rootProject.projectDir.resolve("../apks")
    from(apksDir) { include(bundledModApks) }
    into(layout.buildDirectory.dir("generated/modApks"))
    doFirst {
        bundledModApks.forEach { name ->
            require(apksDir.resolve(name).exists()) {
                "Missing mod APK: ${apksDir.resolve(name)} — expected in top-level apks/"
            }
        }
    }
}

tasks.named("preBuild").configure { dependsOn(syncModApks) }
