package com.quakemind.feature.auth.login

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.quakemind.feature.auth.AuthScreen

@Composable
fun AuthRoute(
    onSuccess: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    LaunchedEffect(state.isAuthenticated) {
        if (state.isAuthenticated) onSuccess()
    }
    AuthScreen(
        onLogin = viewModel::login,
        onRegister = viewModel::register,
        onGuest = viewModel::createGuestSession,
        isBusy = state.isBusy,
        error = state.error,
    )
}
