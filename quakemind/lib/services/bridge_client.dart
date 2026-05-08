import 'dart:async';
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

  static final http.Client _sharedClient = http.Client();

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
      final response = await _sharedClient
          .post(
            uri,
            headers: {
              'Content-Type': 'application/json',
              'Connection': 'keep-alive',
            },
            body: jsonEncode(payload),
          )
          .timeout(Duration(seconds: timeoutSeconds));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return decodeBridgeJson(response.body);
      }
      throw _BridgeHttpException(
        _extractServerError(
          baseUrl: baseUrl,
          statusCode: response.statusCode,
          rawBody: response.body,
        ),
      );
    } on _BridgeHttpException {
      rethrow;
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
      final response = await _sharedClient
          .get(uri, headers: const {'Connection': 'keep-alive'})
          .timeout(Duration(seconds: timeoutSeconds));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return decodeBridgeJson(response.body);
      }
    } catch (_) {}
    return {};
  }
}

class _BridgeHttpException implements Exception {
  const _BridgeHttpException(this.message);
  final String message;

  @override
  String toString() => message;
}

String _extractServerError({
  required String baseUrl,
  required int statusCode,
  required String rawBody,
}) {
  if (rawBody.trim().isEmpty) {
    return '[$baseUrl] Sunucu hatasi: HTTP $statusCode';
  }
  try {
    final decoded = jsonDecode(rawBody);
    if (decoded is Map<String, dynamic>) {
      final detail = decoded['detail'];
      if (detail != null) {
        return '[$baseUrl] Sunucu hatasi ($statusCode): $detail';
      }
      final error = decoded['error'];
      if (error != null) {
        return '[$baseUrl] Sunucu hatasi ($statusCode): $error';
      }
    }
  } catch (_) {}
  return '[$baseUrl] Sunucu hatasi ($statusCode): $rawBody';
}

Future<Map<String, dynamic>> runBridgeProcess({
  required String scriptPath,
  required List<String> args,
}) async {
  throw Exception(
    "Native execution is deprecated. Please use the HTTP API configured in Settings.",
  );
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
