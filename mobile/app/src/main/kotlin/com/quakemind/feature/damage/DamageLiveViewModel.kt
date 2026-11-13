package com.quakemind.feature.damage

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Base64
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.quakemind.core.network.api.DamageDetectionService
import com.quakemind.core.network.api.DamageResult
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import javax.inject.Inject

data class DamageLiveUiState(
    val imageSelected: Boolean = false,
    val isAnalyzing: Boolean = false,
    val result: DamageResult? = null,
    val error: String? = null,
)

@HiltViewModel
class DamageLiveViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val damageService: DamageDetectionService,
) : ViewModel() {
    private val _state = MutableStateFlow(DamageLiveUiState())
    val state = _state.asStateFlow()
    private var imageUri: Uri? = null

    fun selectPhoto(uri: Uri?) {
        imageUri = uri
        _state.value = DamageLiveUiState(imageSelected = uri != null)
    }

    fun analyzePhoto() {
        val selected = imageUri ?: return
        if (_state.value.isAnalyzing) return
        viewModelScope.launch {
            _state.update { it.copy(isAnalyzing = true, result = null, error = null) }
            try {
                val encoded = withContext(Dispatchers.IO) { encodePhoto(selected) }
                val result = damageService.analyze(encoded, "ikisi")
                _state.update { it.copy(isAnalyzing = false, result = result) }
            } catch (cancel: CancellationException) {
                _state.update { it.copy(isAnalyzing = false) }
                throw cancel
            } catch (_: Exception) {
                _state.update {
                    it.copy(
                        isAnalyzing = false,
                        result = null,
                        error = "Fotoğraf analizi tamamlanamadı. Sunucu, oturum ve model durumunu kontrol edin.",
                    )
                }
            }
        }
    }

    private fun encodePhoto(uri: Uri): String {
        val resolver = context.contentResolver
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        resolver.openInputStream(uri)?.use {
            BitmapFactory.decodeStream(it, null, bounds)
            true
        } ?: throw IllegalArgumentException("Görsele erişilemiyor.")
        if (bounds.outWidth < 1 || bounds.outHeight < 1) {
            throw IllegalArgumentException("Görsel okunamadı.")
        }
        var sample = 1
        while (bounds.outWidth / sample > 1600 || bounds.outHeight / sample > 1600) {
            sample *= 2
        }
        val options = BitmapFactory.Options().apply { inSampleSize = sample }
        val bitmap = resolver.openInputStream(uri)?.use {
            BitmapFactory.decodeStream(it, null, options)
        } ?: throw IllegalArgumentException("Görsel okunamadı.")
        return try {
            ByteArrayOutputStream().use { bytes ->
                if (!bitmap.compress(Bitmap.CompressFormat.JPEG, 82, bytes)) {
                    throw IllegalStateException("Görsel JPEG olarak hazırlanamadı.")
                }
                if (bytes.size() > 5_500_000) throw IllegalArgumentException("Görsel çok büyük.")
                Base64.encodeToString(bytes.toByteArray(), Base64.NO_WRAP)
            }
        } finally {
            bitmap.recycle()
        }
    }
}
