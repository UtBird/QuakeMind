import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;

class ApiConfig {
  static const String _ipKey = 'backend_ip';
  static const String _defaultIp = '10.42.0.1:8000'; // Linux PC hotspot default
  static const List<String> _fallbackIps = <String>[
    '10.42.0.1:8000', // Linux hotspot
    '192.168.137.1:8000', // Windows hotspot
    '10.0.2.2:8000', // Android emulator -> host machine
    '127.0.0.1:8000', // Desktop local test
  ];

  static String? _resolvedBackendUrl;

  static Future<String> getBackendUrl() async {
    if (_resolvedBackendUrl != null) return _resolvedBackendUrl!;

    final prefs = await SharedPreferences.getInstance();
    final configuredIp = prefs.getString(_ipKey);
    final candidates = <String>[
      if (configuredIp != null && configuredIp.trim().isNotEmpty)
        configuredIp.trim(),
      ..._fallbackIps,
      _defaultIp,
    ];

    final visited = <String>{};
    for (final rawIp in candidates) {
      final ip = rawIp.trim();
      if (ip.isEmpty || !visited.add(ip)) continue;
      if (await _isBackendReachable(ip)) {
        await prefs.setString(_ipKey, ip);
        _resolvedBackendUrl = 'http://$ip';
        return _resolvedBackendUrl!;
      }
    }

    final fallbackIp = configuredIp?.trim().isNotEmpty == true
        ? configuredIp!.trim()
        : _defaultIp;
    _resolvedBackendUrl = 'http://$fallbackIp';
    return _resolvedBackendUrl!;
  }

  static Future<void> setBackendIp(String ip) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_ipKey, ip);
    _resolvedBackendUrl = null;
  }

  static Future<String> getBackendIp() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_ipKey) ?? _defaultIp;
  }

  static Future<bool> _isBackendReachable(String ipPort) async {
    final client = http.Client();
    try {
      final uri = Uri.parse('http://$ipPort/api/status');
      final response = await client
          .get(uri)
          .timeout(const Duration(milliseconds: 800));
      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (_) {
      return false;
    } finally {
      client.close();
    }
  }
}
