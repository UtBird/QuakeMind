package com.quakemind.core.data.di

import com.quakemind.core.data.datasource.local.AlertLocalDataSource
import com.quakemind.core.data.datasource.local.ChecklistLocalDataSource
import com.quakemind.core.data.datasource.local.EarthquakeLocalDataSource
import com.quakemind.core.data.datasource.local.IncidentLocalDataSource
import com.quakemind.core.data.datasource.local.MapLocalDataSource
import com.quakemind.core.data.datasource.local.MemoryAlertLocalDataSource
import com.quakemind.core.data.datasource.local.MemoryChecklistLocalDataSource
import com.quakemind.core.data.datasource.local.MemoryEarthquakeLocalDataSource
import com.quakemind.core.data.datasource.local.MemoryMapLocalDataSource
import com.quakemind.core.data.datasource.local.MemorySafetyLocalDataSource
import com.quakemind.core.data.datasource.local.MemorySessionLocalDataSource
import com.quakemind.core.data.datasource.local.RoomIncidentLocalDataSource
import com.quakemind.core.data.datasource.local.SafetyLocalDataSource
import com.quakemind.core.data.datasource.local.SessionLocalDataSource
import com.quakemind.core.data.datasource.remote.AiRemoteDataSource
import com.quakemind.core.data.datasource.remote.AlertRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultAiRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultAlertRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultEarthquakeRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultIncidentRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultRoutingRemoteDataSource
import com.quakemind.core.data.datasource.remote.DefaultSafetyRemoteDataSource
import com.quakemind.core.data.datasource.remote.EarthquakeRemoteDataSource
import com.quakemind.core.data.datasource.remote.IncidentRemoteDataSource
import com.quakemind.core.data.datasource.remote.RoutingRemoteDataSource
import com.quakemind.core.data.datasource.remote.SafetyRemoteDataSource
import com.quakemind.core.data.repository.AiAnalysisRepository
import com.quakemind.core.data.repository.AlertRepository
import com.quakemind.core.data.repository.DefaultAiAnalysisRepository
import com.quakemind.core.data.repository.DefaultAlertRepository
import com.quakemind.core.data.repository.DefaultEarthquakeRepository
import com.quakemind.core.data.repository.DefaultMapRepository
import com.quakemind.core.data.repository.DefaultPreparednessRepository
import com.quakemind.core.data.repository.DefaultQuakeMindRepository
import com.quakemind.core.data.repository.DefaultRoutingRepository
import com.quakemind.core.data.repository.DefaultSafetyRepository
import com.quakemind.core.data.repository.DefaultSessionRepository
import com.quakemind.core.data.repository.EarthquakeRepository
import com.quakemind.core.data.repository.IncidentRepository
import com.quakemind.core.data.repository.MapRepository
import com.quakemind.core.data.repository.OfflineFirstIncidentRepository
import com.quakemind.core.data.repository.PreparednessRepository
import com.quakemind.core.data.repository.QuakeMindRepository
import com.quakemind.core.data.repository.RoutingRepository
import com.quakemind.core.data.repository.SafetyRepository
import com.quakemind.core.data.repository.SessionRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class DataSourceModule {

    @Binds
    @Singleton
    abstract fun bindIncidentLocalDataSource(impl: RoomIncidentLocalDataSource): IncidentLocalDataSource

    @Binds
    @Singleton
    abstract fun bindEarthquakeLocalDataSource(impl: MemoryEarthquakeLocalDataSource): EarthquakeLocalDataSource

    @Binds
    @Singleton
    abstract fun bindAlertLocalDataSource(impl: MemoryAlertLocalDataSource): AlertLocalDataSource

    @Binds
    @Singleton
    abstract fun bindMapLocalDataSource(impl: MemoryMapLocalDataSource): MapLocalDataSource

    @Binds
    @Singleton
    abstract fun bindSafetyLocalDataSource(impl: MemorySafetyLocalDataSource): SafetyLocalDataSource

    @Binds
    @Singleton
    abstract fun bindChecklistLocalDataSource(impl: MemoryChecklistLocalDataSource): ChecklistLocalDataSource

    @Binds
    @Singleton
    abstract fun bindSessionLocalDataSource(impl: MemorySessionLocalDataSource): SessionLocalDataSource

    @Binds
    @Singleton
    abstract fun bindIncidentRemoteDataSource(impl: DefaultIncidentRemoteDataSource): IncidentRemoteDataSource

    @Binds
    @Singleton
    abstract fun bindEarthquakeRemoteDataSource(impl: DefaultEarthquakeRemoteDataSource): EarthquakeRemoteDataSource

    @Binds
    @Singleton
    abstract fun bindAlertRemoteDataSource(impl: DefaultAlertRemoteDataSource): AlertRemoteDataSource

    @Binds
    @Singleton
    abstract fun bindRoutingRemoteDataSource(impl: DefaultRoutingRemoteDataSource): RoutingRemoteDataSource

    @Binds
    @Singleton
    abstract fun bindSafetyRemoteDataSource(impl: DefaultSafetyRemoteDataSource): SafetyRemoteDataSource

    @Binds
    @Singleton
    abstract fun bindAiRemoteDataSource(impl: DefaultAiRemoteDataSource): AiRemoteDataSource
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindQuakeMindRepository(implementation: DefaultQuakeMindRepository): QuakeMindRepository

    @Binds
    @Singleton
    abstract fun bindSessionRepository(implementation: DefaultSessionRepository): SessionRepository

    @Binds
    @Singleton
    abstract fun bindEarthquakeRepository(implementation: DefaultEarthquakeRepository): EarthquakeRepository

    @Binds
    @Singleton
    abstract fun bindIncidentRepository(implementation: OfflineFirstIncidentRepository): IncidentRepository

    @Binds
    @Singleton
    abstract fun bindAlertRepository(implementation: DefaultAlertRepository): AlertRepository

    @Binds
    @Singleton
    abstract fun bindMapRepository(implementation: DefaultMapRepository): MapRepository

    @Binds
    @Singleton
    abstract fun bindPreparednessRepository(implementation: DefaultPreparednessRepository): PreparednessRepository

    @Binds
    @Singleton
    abstract fun bindRoutingRepository(implementation: DefaultRoutingRepository): RoutingRepository

    @Binds
    @Singleton
    abstract fun bindSafetyRepository(implementation: DefaultSafetyRepository): SafetyRepository

    @Binds
    @Singleton
    abstract fun bindAiAnalysisRepository(implementation: DefaultAiAnalysisRepository): AiAnalysisRepository
}
