package com.quakemind.core.data.repository

import com.quakemind.core.model.UserSession
import kotlinx.coroutines.flow.Flow

interface SessionRepository {
    fun session(): Flow<UserSession>
    fun currentSession(): UserSession? = null
}
