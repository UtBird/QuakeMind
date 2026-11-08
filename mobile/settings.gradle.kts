pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "QuakeMind"
include(":app")
include(":core:model")
include(":core:database")
include(":core:network")
include(":core:ui")
include(":core:testing")
include(":core:designsystem")
include(":core:data")
include(":sync")
include(":benchmark")
