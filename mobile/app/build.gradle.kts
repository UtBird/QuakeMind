import org.gradle.api.tasks.ClasspathNormalizer
import org.gradle.api.tasks.compile.JavaCompile

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.compose.compiler)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

android {
    namespace = "com.quakemind"
    compileSdk = 37

    defaultConfig {
        applicationId = "com.quakemind"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables { useSupportLibrary = true }
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-dev"
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles("proguard-rules.pro")
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }

    testOptions {
        unitTests.isIncludeAndroidResources = true
    }
}

composeCompiler {
    metricsDestination = layout.buildDirectory.dir("compose_metrics")
    reportsDestination = layout.buildDirectory.dir("compose_reports")
    stabilityConfigurationFiles.add(layout.projectDirectory.file("compose_stability.conf"))
}


// Android Studio can rerun javac independently when deployment properties such as
// android.injected.enableStableIds change. With AGP's built-in Kotlin compiler,
// make the Kotlin bytecode an explicit javac input so Hilt's KSP-generated Java
// sources can always resolve the app's Kotlin classes during Run/Apply Changes.
afterEvaluate {
    listOf("Debug", "Release").forEach { variantName ->
        val variantDirectory = variantName.replaceFirstChar { it.lowercase() }
        val kotlinClasses = layout.buildDirectory.dir(
            "intermediates/built_in_kotlinc/$variantDirectory/compile${variantName}Kotlin/classes",
        )
        tasks.named("compile${variantName}Kotlin").configure {
            outputs.upToDateWhen {
                kotlinClasses.get().asFile
                    .resolve("com/quakemind/QuakeMindApplication.class")
                    .isFile
            }
        }
        tasks.named<JavaCompile>("compile${variantName}JavaWithJavac").configure {
            dependsOn("compile${variantName}Kotlin")
            inputs.files(kotlinClasses)
                .withPropertyName("builtInKotlinClasses")
                .withNormalizer(ClasspathNormalizer::class.java)
            classpath = classpath.plus(files(kotlinClasses))
        }
    }
}

dependencies {
    implementation(project(":core:model"))
    implementation(project(":core:database"))
    implementation(project(":core:network"))
    implementation(project(":core:ui"))
    implementation(project(":core:designsystem"))
    implementation(project(":core:data"))
    implementation(project(":sync"))
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.hilt.navigation.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.foundation)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons)
    implementation(libs.openmapview.compose)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.kotlinx.coroutines)
    implementation(libs.kotlinx.serialization)
    implementation(libs.coil.compose)
    implementation(libs.camerax.core)
    implementation(libs.camerax.camera2)
    implementation(libs.camerax.lifecycle)
    implementation(libs.camerax.view)
    implementation(libs.androidx.work.runtime)
    implementation(libs.androidx.hilt.work)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)

    testImplementation(libs.junit)
    testImplementation(libs.mockk)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.turbine)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso)
    debugImplementation(libs.androidx.compose.ui.tooling)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}
