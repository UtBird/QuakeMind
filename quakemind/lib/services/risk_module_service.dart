import '../models/risk_module_result.dart';
import 'bridge_client.dart';

class RiskBridgeUnavailableException extends BridgeUnavailableException {
  const RiskBridgeUnavailableException({
    required super.message,
    required super.instructions,
    super.bridgeBaseUrl,
    super.lastError,
  });
}

class RiskModuleService {
  const RiskModuleService();

  static const _httpClient = BridgeHttpClient(
    configuredBaseUrl: '',
    defaultPort: 8000,
  );

  Future<RiskModuleResult> fetchCityRisk(
    String city, {
    bool refreshData = false,
    double? manualLatitude,
    double? manualLongitude,
  }) async {
    final jsonMap = await _httpClient.postJson(
      endpoint: '/api/risk/predict',
      payload: {
        'city': city,
        'refreshData': refreshData,
        'manualLatitude': manualLatitude,
        'manualLongitude': manualLongitude,
      },
      unavailableException: const RiskBridgeUnavailableException(
        message: 'FastAPI sunucusuna baglanilamadi.',
        instructions: ['Ayarlardan API adresini (IP:Port) dogru girdiginizden emin olun.'],
      ),
    );

    return RiskModuleResult.fromJson(jsonMap);
  }
}
