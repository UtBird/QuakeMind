package com.quakemind.core.database.di

import android.content.Context
import androidx.room.Room
import com.quakemind.core.database.QuakeMindDatabase
import com.quakemind.core.database.dao.IncidentDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

import com.quakemind.core.database.migrations.DatabaseMigrations

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): QuakeMindDatabase =
        Room.databaseBuilder(context, QuakeMindDatabase::class.java, "quakemind.db")
            .addMigrations(DatabaseMigrations.MIGRATION_1_2)
            .fallbackToDestructiveMigration(false)
            .build()

    @Provides
    fun provideIncidentDao(database: QuakeMindDatabase): IncidentDao = database.incidentDao()
}
