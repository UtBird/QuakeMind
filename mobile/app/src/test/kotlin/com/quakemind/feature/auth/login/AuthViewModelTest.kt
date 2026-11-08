package com.quakemind.feature.auth.login

import com.quakemind.core.model.UserSession
import com.quakemind.core.network.api.AuthService
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class)
class AuthViewModelTest {
    private val dispatcher = StandardTestDispatcher()
    private val service = mockk<AuthService>()
    private val session = UserSession("Misafir", "", emptySet(), true)

    @Before fun before() { Dispatchers.setMain(dispatcher) }
    @After fun after() { Dispatchers.resetMain() }

    @Test fun `guest navigation unlocks only after server accepts session`() = runTest(dispatcher) {
        coEvery { service.createGuestSession() } returns session
        val vm = AuthViewModel(service)
        vm.createGuestSession()
        vm.createGuestSession()
        assertTrue(vm.state.value.isBusy)
        assertFalse(vm.state.value.isAuthenticated)
        advanceUntilIdle()
        assertTrue(vm.state.value.isAuthenticated)
        assertFalse(vm.state.value.isBusy)
        coVerify(exactly = 1) { service.createGuestSession() }
    }

    @Test fun `failed login does not unlock navigation`() = runTest(dispatcher) {
        coEvery { service.login(any(), any()) } throws IOException("Unauthorized")
        val vm = AuthViewModel(service)
        vm.login("test@example.com", "incorrect")
        advanceUntilIdle()
        assertFalse(vm.state.value.isAuthenticated)
        assertNotNull(vm.state.value.error)
        assertFalse(vm.state.value.isBusy)
    }

    @Test fun `register forwards actual user details to backend`() = runTest(dispatcher) {
        coEvery { service.register("test@example.com", "Deniz Test", "secret123") } returns session
        val vm = AuthViewModel(service)
        vm.register(" test@example.com ", " Deniz Test ", "secret123")
        advanceUntilIdle()
        coVerify(exactly = 1) { service.register("test@example.com", "Deniz Test", "secret123") }
        assertTrue(vm.state.value.isAuthenticated)
    }

    @Test fun `blank email does not call backend`() = runTest(dispatcher) {
        val vm = AuthViewModel(service)
        vm.login(" ", "123456")
        advanceUntilIdle()
        coVerify(exactly = 0) { service.login(any(), any()) }
        assertFalse(vm.state.value.isAuthenticated)
        assertNotNull(vm.state.value.error)
    }
}
