package com.quakemind.core.data.repository

import com.quakemind.core.model.FamilyMember
import kotlinx.coroutines.flow.Flow

interface SafetyRepository {
    fun familyMembers(): Flow<List<FamilyMember>>
    fun currentFamilyMembers(): List<FamilyMember> = emptyList()
    suspend fun updateSafetyStatus(status: String)
    suspend fun updateFamilyMemberStatus(memberId: String, status: String)
}
