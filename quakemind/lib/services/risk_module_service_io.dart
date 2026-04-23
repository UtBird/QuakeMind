import 'dart:convert';
import 'dart:io';

import '../models/risk_module_result.dart';

class RiskModuleService {
  const RiskModuleService();

  Future<RiskModuleResult> fetchCityRisk(String city) async {
    final result = await Process.run('python3', [
      'tool/risk_bridge.py',
      city,
    ], runInShell: true);

    if (result.exitCode != 0) {
      final stderr = result.stderr.toString().trim();
      final stdout = result.stdout.toString().trim();
      throw Exception(stderr.isNotEmpty ? stderr : stdout);
    }

    final raw = result.stdout.toString().trim();
    if (raw.isEmpty) {
      throw Exception('Risk servisinden bos yanit dondu.');
    }

    final jsonMap = jsonDecode(raw) as Map<String, dynamic>;
    if (jsonMap['error'] case final Object error) {
      throw Exception(error.toString());
    }

    return RiskModuleResult.fromJson(jsonMap);
  }
}
