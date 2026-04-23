import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';

class BridgeUnavailableException implements Exception {
  const BridgeUnavailableException({
    required this.message,
    required this.instructions,
    this.bridgeBaseUrl,
    this.lastError,
  });

  final String message;
  final List<String> instructions;
  final String? bridgeBaseUrl;
  final Object? lastError;

  @override
  String toString() => message;
}

class BridgeHttpClient {
  const BridgeHttpClient({
    required this.configuredBaseUrl,
    required this.defaultPort,
  });

  final String configuredBaseUrl;
  final int defaultPort;

  Future<Map<String, dynamic>> postJson({
    required String endpoint,
    required Map<String, dynamic> payload,
    required BridgeUnavailableException unavailableException,
    int timeoutSeconds = 30,
  }) async {
    final baseUrl = await ApiConfig.getBackendUrl();
    Object? lastError;
    try {
      final uri = Uri.parse('$baseUrl$endpoint');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      ).timeout(Duration(seconds: timeoutSeconds));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return decodeBridgeJson(response.body);
      }
      lastError = Exception('[$baseUrl] ${response.statusCode}: ${response.body}');
    } catch (error) {
      lastError = error;
    }

    throw BridgeUnavailableException(
      message: unavailableException.message,
      instructions: unavailableException.instructions,
      bridgeBaseUrl: baseUrl,
      lastError: lastError,
    );
  }

  Future<Map<String, dynamic>> getJson({
    required String endpoint,
    int timeoutSeconds = 10,
  }) async {
    final baseUrl = await ApiConfig.getBackendUrl();
    try {
      final uri = Uri.parse('$baseUrl$endpoint');
      final response = await http.get(uri).timeout(Duration(seconds: timeoutSeconds));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return decodeBridgeJson(response.body);
      }
    } catch (_) {}
    return {};
  }
}

Future<Map<String, dynamic>> runBridgeProcess({
  required String scriptPath,
  required List<String> args,
}) async {
  throw Exception("Native execution is deprecated. Please use the HTTP API configured in Settings.");
}

Map<String, dynamic> decodeBridgeJson(String raw) {
  if (raw.isEmpty) {
    throw Exception('Bridge servisinden bos yanit dondu.');
  }

  final jsonMap = jsonDecode(raw) as Map<String, dynamic>;
  if (jsonMap['error'] case final Object error) {
    throw Exception(error.toString());
  }

  return jsonMap;
}
