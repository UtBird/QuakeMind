import java.net.URI

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
    val productionUrl = "https://quakemind-api.dehaozcan.online/"
    val configuredUrl = providers.gradleProperty("quakemindApiBaseUrl").orNull
        ?: providers.environmentVariable("QUAKEMIND_API_BASE_URL").orNull
    val debugOverride = providers.gradleProperty("quakemindDebugApiBaseUrl").orNull
        ?: providers.environmentVariable("QUAKEMIND_DEBUG_API_BASE_URL").orNull
    fun apiUrl(value: String, allowHttp: Boolean): String {
        val uri = URI(value.trim())
        require(uri.host != null && uri.rawUserInfo == null &&
            uri.rawQuery == null && uri.rawFragment == null) {
            "API URL must have a hostname and must not contain credentials, query parameters or a fragment."
        }
        require(uri.scheme == "https" || (allowHttp && uri.scheme == "http")) {
            "API URL must use HTTPS. Use quakemindDebugApiBaseUrl for local HTTP development."
        }
        return uri.toASCIIString().trimEnd('/') + "/"
    }
    val releaseUrl = apiUrl(configuredUrl ?: productionUrl, allowHttp = false)
    buildTypes {
        getByName("debug") {
            buildConfigField("String", "API_BASE_URL", "\"${apiUrl(debugOverride ?: releaseUrl, allowHttp = true)}\"")
        }
        getByName("release") {
            buildConfigField("String", "API_BASE_URL", "\"$releaseUrl\"")
        }
        create("benchmark") {
            initWith(getByName("release"))
            matchingFallbacks += "release"
            val benchmarkUrl = providers.gradleProperty("quakemindBenchmarkApiBaseUrl").orNull
            val selectedUrl = benchmarkUrl?.let { value ->
                require(URI(value).host in setOf("127.0.0.1", "localhost", "10.0.2.2")) {
                    "Benchmark API override must target the local development server."
                }
                apiUrl(value, allowHttp = true)
            } ?: releaseUrl
            buildConfigField("String", "API_BASE_URL", "\"$selectedUrl\"")
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
