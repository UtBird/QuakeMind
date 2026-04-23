import '../models/nlp_module_result.dart';
import 'bridge_client.dart';

class NlpBridgeUnavailableException extends BridgeUnavailableException {
  const NlpBridgeUnavailableException({
    required super.message,
    required super.instructions,
    super.bridgeBaseUrl,
    super.lastError,
  });
}

class NlpModuleService {
  const NlpModuleService();

  static const _httpClient = BridgeHttpClient(
    configuredBaseUrl: '',
    defaultPort: 8000,
  );

  Future<NlpModuleResult> analyzeText(String text) async {
    final jsonMap = await _httpClient.postJson(
      endpoint: '/api/nlp/analyze',
      payload: {'text': text},
      unavailableException: const NlpBridgeUnavailableException(
        message: 'FastAPI sunucusuna baglanilamadi.',
        instructions: ['Ayarlardan API adresini (IP:Port) dogru girdiginizden emin olun.'],
      ),
    );

    return NlpModuleResult.fromJson(jsonMap);
  }
}
