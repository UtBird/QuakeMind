package com.quakemind.core.network.real

import android.content.Context
import com.quakemind.core.network.BuildConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import okhttp3.Cookie
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

class BackendException(val statusCode: Int, message: String) : IOException(message)

internal fun JsonElement?.obj(): JsonObject? = this as? JsonObject
internal fun JsonElement?.array(): JsonArray = this as? JsonArray ?: JsonArray(emptyList())
internal fun JsonElement?.string(): String? =
    (this as? JsonPrimitive)?.content?.takeUnless { this == JsonNull }
internal fun JsonElement?.number(): Double? = string()?.toDoubleOrNull()
internal fun JsonElement?.int(): Int? = number()?.toInt()
internal fun JsonElement?.bool(): Boolean = string()?.toBooleanStrictOrNull() == true

/**
 * All mobile requests share one authenticated client. Access tokens are never placed
 * in URLs or HTTP logs. Refresh tokens come from the backend's httpOnly cookie.
 * Android's private preferences retain the cookie across process restarts.
 */
@Singleton
class BackendClient @Inject constructor(
    @ApplicationContext context: Context,
    private val http: OkHttpClient,
) {
    private val prefs = context.getSharedPreferences("quakemind_backend_session", Context.MODE_PRIVATE)
    private val json = Json { ignoreUnknownKeys = true }
    private val baseUrl = BuildConfig.API_BASE_URL.trimEnd('/') + "/"
    private val renewalLock = Any()
    private val inferenceHttp by lazy {
        http.newBuilder()
            .readTimeout(150, TimeUnit.SECONDS)
            .callTimeout(180, TimeUnit.SECONDS)
            .build()
    }
    private val _profiles = MutableStateFlow(savedProfile())
    val profiles = _profiles.asStateFlow()

    val isSignedIn: Boolean get() = !prefs.getString("access", null).isNullOrEmpty()
    fun savedProfile(): JsonObject? =
        prefs.getString("profile", null)?.let { runCatching { json.parseToJsonElement(it).obj() }.getOrNull() }

    fun clearSession() {
        prefs.edit().remove("access").remove("refresh").remove("profile").apply()
        _profiles.value = null
    }

    private fun sessionToken(): String? = prefs.getString("access", null)
    private fun cookie(): String? = prefs.getString("refresh", null)

    private fun storeSession(body: JsonObject, responseCookies: List<String>) {
        val token = body["erisimJetonu"].string()
            ?: throw IOException("Sunucu oturum jetonu döndürmedi.")
        val profile = body["kullanici"].obj()
            ?: throw IOException("Sunucu kullanıcı profili döndürmedi.")
        val responseUrl = baseUrl.toHttpUrl()
        val newRefresh = responseCookies.mapNotNull { Cookie.parse(responseUrl, it) }
            .firstOrNull { it.name == "qm_yenileme" }?.value
        val edit = prefs.edit()
            .putString("access", token)
            .putString("profile", profile.toString())
        if (newRefresh != null) edit.putString("refresh", "qm_yenileme=" + newRefresh)
        else edit.remove("refresh")
        edit.apply()
        _profiles.value = profile
    }

    suspend fun session(path: String, payload: JsonObject = JsonObject(emptyMap())): JsonObject =
        withContext(Dispatchers.IO) {
            val response = raw("POST", path, payload, signed = false)
            storeSession(response.first, response.second)
            response.first
        }

    suspend fun renew(): JsonObject = withContext(Dispatchers.IO) {
        synchronized(renewalLock) { renewBlocking() }
    }

    suspend fun closeSession(): Unit = withContext(Dispatchers.IO) {
        try {
            raw("POST", "api/oturum/cikis", JsonObject(emptyMap()), signed = false, withCookie = true)
        } finally {
            clearSession()
        }
        Unit
    }

    private fun renewBlocking(): JsonObject {
        if (cookie().isNullOrBlank()) throw BackendException(401, "Yenileme oturumu bulunamadı.")
        return try {
            val response = raw("POST", "api/oturum/yenile", JsonObject(emptyMap()), signed = false, withCookie = true)
            storeSession(response.first, response.second)
            response.first
        } catch (e: BackendException) {
            if (e.statusCode == 401) clearSession()
            throw e
        }
    }

    suspend fun request(
        method: String,
        path: String,
        payload: JsonObject? = null,
        params: Map<String, String> = emptyMap(),
        idempotencyKey: String? = null,
    ): JsonElement = withContext(Dispatchers.IO) {
        try {
            raw(method, path, payload, params, signed = true, idempotencyKey = idempotencyKey).first
        } catch (e: BackendException) {
            if (e.statusCode != 401 || cookie() == null) throw e
            val priorToken = sessionToken()
            synchronized(renewalLock) {
                if (sessionToken() == priorToken) renewBlocking()
            }
            raw(method, path, payload, params, signed = true, idempotencyKey = idempotencyKey).first
        }
    }

    private fun raw(
        method: String,
        path: String,
        payload: JsonObject? = null,
        params: Map<String, String> = emptyMap(),
        signed: Boolean,
        withCookie: Boolean = false,
        idempotencyKey: String? = null,
    ): Pair<JsonObject, List<String>> {
        val urlBuilder = (baseUrl + path.trimStart('/')).toHttpUrl().newBuilder()
        for ((key, value) in params) urlBuilder.addQueryParameter(key, value)
        val requestBuilder = Request.Builder()
            .url(urlBuilder.build())
            .header("Accept", "application/json")
        val body = if (method != "GET") {
            (payload?.toString() ?: "{}").toRequestBody("application/json; charset=utf-8".toMediaType())
        } else null
        requestBuilder.method(method, body)
        if (signed) {
            sessionToken()?.let { requestBuilder.header("Authorization", "Bearer " + it) }
        }
        if (withCookie) cookie()?.let { requestBuilder.header("Cookie", it) }
        idempotencyKey?.let { requestBuilder.header("Idempotency-Key", it) }
        val selectedHttp = if (path.startsWith("api/afetzede/fotograf-analiz") ||
            path.startsWith("api/afetzede/metin-analiz") ||
            path.startsWith("api/risk/predict") ||
            path.startsWith("api/road_damage/") ||
            path.startsWith("api/afetzede/rota")) inferenceHttp else http
        return selectedHttp.newCall(requestBuilder.build()).execute().use { response ->
            val rawBody = response.body?.string().orEmpty()
            val data: JsonElement? = if (rawBody.isBlank()) null else try {
                json.parseToJsonElement(rawBody)
            } catch (e: Exception) {
                if (response.isSuccessful) throw IOException("Sunucudan geçersiz JSON alındı.", e)
                null
            }
            if (!response.isSuccessful) {
                val detail = data.obj()?.get("detail").string()
                throw BackendException(
                    response.code,
                    detail ?: when (response.code) {
                        401 -> "Oturum açmanız gerekiyor."
                        403 -> "Bu işlem için yetkiniz bulunmuyor."
                        404 -> "İstenen kaynak bulunamadı."
                        429 -> "Çok fazla istek gönderildi."
                        in 500..599 -> "Sunucu şu anda yanıt veremiyor."
                        else -> "Sunucu isteği kabul etmedi (HTTP " + response.code + ")."
                    },
                )
            }
            // All existing REST endpoints used by this client return objects or arrays.
            val wrapped = data as? JsonObject ?: JsonObject(mapOf("_items" to (data ?: JsonNull)))
            wrapped to response.headers.values("Set-Cookie")
        }
    }
}
