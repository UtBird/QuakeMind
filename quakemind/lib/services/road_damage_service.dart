import '../models/road_damage_result.dart';
import 'bridge_client.dart';

class RoadDamageBridgeUnavailableException extends BridgeUnavailableException {
  const RoadDamageBridgeUnavailableException({
    required super.message,
    required super.instructions,
    super.bridgeBaseUrl,
    super.lastError,
  });
}

class RoadDamageService {
  const RoadDamageService();

  static const _httpClient = BridgeHttpClient(
    configuredBaseUrl: '',
    defaultPort: 8000,
  );

  Future<RoadDamageResult> analyzeArea({
    required String city,
    required double latitude,
    required double longitude,
    String source = 'google',
    String? oamPreferredTitle,
    double damageBooster = 3.5,
    double threshold = 0.40,
    bool useImagenetNorm = true,
    int postProcessLevel = 2,
  }) async {
    final jsonMap = await _httpClient.postJson(
      endpoint: '/api/road_damage/analyze',
      payload: {
        'city': city,
        'latitude': latitude,
        'longitude': longitude,
        'source': source,
        if (oamPreferredTitle != null && oamPreferredTitle.trim().isNotEmpty)
          'oamPreferredTitle': oamPreferredTitle.trim(),
        'damageBooster': damageBooster,
        'threshold': threshold,
        'useImagenetNorm': useImagenetNorm,
        'postProcessLevel': postProcessLevel,
      },
      unavailableException: const RoadDamageBridgeUnavailableException(
        message: 'FastAPI sunucusuna baglanilamadi.',
        instructions: [
          'Ayarlardan API adresini (IP:Port) dogru girdiginizden emin olun.',
        ],
      ),
      timeoutSeconds: 300,
    );

    return RoadDamageResult.fromJson(jsonMap);
  }
}
