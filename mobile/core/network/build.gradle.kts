plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

android {
    namespace = "com.quakemind.core.network"
    compileSdk = 37
    buildFeatures { buildConfig = true }
    defaultConfig {
        minSdk = 26
        consumerProguardFiles("consumer-rules.pro")
    }
    val configuredUrl = providers.gradleProperty("quakemindApiBaseUrl").orNull
        ?: providers.environmentVariable("QUAKEMIND_API_BASE_URL").orNull
    buildTypes {
        getByName("debug") {
            buildConfigField("String", "API_BASE_URL", "\""+ (configuredUrl ?: "http://10.0.2.2:8000/") +"\"")
        }
        getByName("release") {
            buildConfigField("String", "API_BASE_URL", "\""+ (configuredUrl ?: "https://quakemind.invalid/") +"\"")
        }
    }
}

dependencies {
    api(project(":core:model"))
    implementation(libs.androidx.core.ktx)
    implementation(libs.kotlinx.coroutines)
    implementation(libs.kotlinx.serialization)
    implementation(libs.retrofit.core)
    implementation(libs.retrofit.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)

    testImplementation(libs.junit)
    testImplementation(libs.mockk)
    testImplementation(libs.kotlinx.coroutines.test)
}
