import '../models/risk_module_result.dart';

class RiskModuleService {
  const RiskModuleService();

  Future<RiskModuleResult> fetchCityRisk(String city) {
    throw UnsupportedError(
      'Risk module integration is only available on local IO platforms for now.',
    );
  }
}
