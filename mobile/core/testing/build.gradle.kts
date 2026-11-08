plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.quakemind.core.testing"
    compileSdk = 37
    defaultConfig { minSdk = 26 }
}

dependencies {
    api(project(":core:model"))
    api(project(":core:database"))
    api(project(":core:network"))
    api(project(":core:data"))
    implementation(libs.kotlinx.coroutines)
    implementation(libs.kotlinx.coroutines.test)
    implementation(libs.junit)
    implementation(libs.mockk)
}
