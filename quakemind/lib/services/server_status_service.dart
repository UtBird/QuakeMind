import 'bridge_client.dart';

class ServerStatus {
  const ServerStatus({
    required this.isOnline,
    required this.nlpReady,
    required this.riskReady,
    required this.roadDamageReady,
  });

  final bool isOnline;
  final bool nlpReady;
  final bool riskReady;
  final bool roadDamageReady;

  static const offline = ServerStatus(
    isOnline: false,
    nlpReady: false,
    riskReady: false,
    roadDamageReady: false,
  );
}

class ServerStatusService {
  const ServerStatusService();

  static const _httpClient = BridgeHttpClient(
    configuredBaseUrl: '',
    defaultPort: 8000,
  );

  Future<ServerStatus> checkStatus() async {
    try {
      final json = await _httpClient.getJson(
        endpoint: '/api/status',
        timeoutSeconds: 5,
      );
      if (json.isEmpty) return ServerStatus.offline;

      final modules = json['modules'] as Map<String, dynamic>? ?? {};
      return ServerStatus(
        isOnline: true,
        nlpReady: modules['nlp'] as bool? ?? false,
        riskReady: modules['risk'] as bool? ?? false,
        roadDamageReady: modules['road_damage'] as bool? ?? false,
      );
    } catch (_) {
      return ServerStatus.offline;
    }
  }
}
