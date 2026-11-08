package com.quakemind.core.database.migrations

import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

object DatabaseMigrations {
    val MIGRATION_1_2 = object : Migration(1, 2) {
        override fun migrate(db: SupportSQLiteDatabase) {
            db.execSQL(
                "CREATE INDEX IF NOT EXISTS `index_incident_queue_syncStatus_createdAt` ON `incident_queue` (`syncStatus`, `createdAt`)"
            )
            db.execSQL(
                "CREATE INDEX IF NOT EXISTS `index_incident_queue_idempotencyKey` ON `incident_queue` (`idempotencyKey`)"
            )
        }
    }
}
