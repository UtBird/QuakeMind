package com.quakemind.core.database

import androidx.room.Database
import androidx.room.RoomDatabase
import com.quakemind.core.database.dao.IncidentDao
import com.quakemind.core.database.entity.IncidentEntity

@Database(entities = [IncidentEntity::class], version = 2, exportSchema = true)
abstract class QuakeMindDatabase : RoomDatabase() {
    abstract fun incidentDao(): IncidentDao
}
