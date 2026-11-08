package com.quakemind.feature.auth.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.network.api.AuthService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AuthUiState(
    val isBusy: Boolean = false,
    val isAuthenticated: Boolean = false,
    val error: String? = null,
)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authService: AuthService,
) : ViewModel() {
    private val _state = MutableStateFlow(AuthUiState())
    val state: StateFlow<AuthUiState> = _state.asStateFlow()

    fun login(email: String, password: String) {
        if (email.isBlank() || password.isBlank()) {
            _state.update { it.copy(error = "E-posta adresi ve şifre gerekli.") }
            return
        }
        authenticate { authService.login(email.trim(), password) }
    }

    fun register(email: String, fullName: String, password: String) {
        if (email.isBlank() || fullName.isBlank() || password.isBlank()) {
            _state.update { it.copy(error = "Ad soyad, e-posta ve şifre gerekli.") }
            return
        }
        authenticate { authService.register(email.trim(), fullName.trim(), password) }
    }

    fun createGuestSession() = authenticate { authService.createGuestSession() }

    private fun authenticate(action: suspend () -> com.quakemind.core.model.UserSession) {
        if (_state.value.isBusy || _state.value.isAuthenticated) return
        _state.update { it.copy(isBusy = true, error = null) }
        viewModelScope.launch {
            try {
                action()
                _state.update { it.copy(isBusy = false, isAuthenticated = true) }
            } catch (cancel: CancellationException) {
                throw cancel
            } catch (_: Exception) {
                _state.update { it.copy(isBusy = false, error = "Oturum açılamadı. Bilgilerinizi ve internet bağlantınızı kontrol edin.") }
            }
        }
    }
}
