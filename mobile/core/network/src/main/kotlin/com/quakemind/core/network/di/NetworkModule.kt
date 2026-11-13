package com.quakemind.core.network.di

import com.quakemind.core.network.DefaultDispatcher
import com.quakemind.core.network.IoDispatcher
import com.quakemind.core.network.MainDispatcher
import com.quakemind.core.network.api.AuthService
import com.quakemind.core.network.api.DamageDetectionService
import com.quakemind.core.network.api.EarthquakeService
import com.quakemind.core.network.api.IncidentService
import com.quakemind.core.network.api.NlpAnalysisService
import com.quakemind.core.network.api.NotificationService
import com.quakemind.core.network.api.RiskAssessmentService
import com.quakemind.core.network.api.RoadStatusService
import com.quakemind.core.network.api.RoutingService
import com.quakemind.core.network.api.UploadService
import com.quakemind.core.network.api.UserSafetyService
import com.quakemind.core.network.api.SosService
import com.quakemind.core.network.api.MapService
import com.quakemind.core.network.real.BackendAuthService
import com.quakemind.core.network.real.BackendDamageDetectionService
import com.quakemind.core.network.real.BackendEarthquakeService
import com.quakemind.core.network.real.BackendIncidentService
import com.quakemind.core.network.real.BackendNlpService
import com.quakemind.core.network.real.BackendNotificationService
import com.quakemind.core.network.real.BackendRiskAssessmentService
import com.quakemind.core.network.real.BackendRoadStatusService
import com.quakemind.core.network.real.BackendRoutingService
import com.quakemind.core.network.real.BackendUploadService
import com.quakemind.core.network.real.BackendUserSafetyService
import com.quakemind.core.network.real.BackendSosService
import com.quakemind.core.network.real.BackendMapService
import com.quakemind.core.network.monitor.ConnectivityManagerNetworkMonitor
import com.quakemind.core.network.monitor.NetworkMonitor
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient =
        OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build()

    @Provides
    @IoDispatcher
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO

    @Provides
    @DefaultDispatcher
    fun provideDefaultDispatcher(): CoroutineDispatcher = Dispatchers.Default

    @Provides
    @MainDispatcher
    fun provideMainDispatcher(): CoroutineDispatcher = Dispatchers.Main
}

@Module
@InstallIn(SingletonComponent::class)
abstract class NetworkBindingModule {

    @Binds
    @Singleton
    abstract fun bindNetworkMonitor(
        impl: ConnectivityManagerNetworkMonitor,
    ): NetworkMonitor

    @Binds
    @Singleton
    abstract fun bindAuthService(impl: BackendAuthService): AuthService

    @Binds
    @Singleton
    abstract fun bindEarthquakeService(impl: BackendEarthquakeService): EarthquakeService

    @Binds
    @Singleton
    abstract fun bindIncidentService(impl: BackendIncidentService): IncidentService

    @Binds
    @Singleton
    abstract fun bindNlpAnalysisService(impl: BackendNlpService): NlpAnalysisService

    @Binds
    @Singleton
    abstract fun bindDamageDetectionService(impl: BackendDamageDetectionService): DamageDetectionService

    @Binds
    @Singleton
    abstract fun bindRoadStatusService(impl: BackendRoadStatusService): RoadStatusService

    @Binds
    @Singleton
    abstract fun bindRoutingService(impl: BackendRoutingService): RoutingService

    @Binds
    @Singleton
    abstract fun bindRiskAssessmentService(impl: BackendRiskAssessmentService): RiskAssessmentService

    @Binds
    @Singleton
    abstract fun bindNotificationService(impl: BackendNotificationService): NotificationService

    @Binds
    @Singleton
    abstract fun bindUserSafetyService(impl: BackendUserSafetyService): UserSafetyService

    @Binds
    @Singleton
    abstract fun bindUploadService(impl: BackendUploadService): UploadService

    @Binds
    @Singleton
    abstract fun bindSosService(impl: BackendSosService): SosService

    @Binds
    @Singleton
    abstract fun bindMapService(impl: BackendMapService): MapService
}
