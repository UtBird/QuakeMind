class RiskModuleResult {
  const RiskModuleResult({
    required this.city,
    required this.riskLevel,
    required this.riskScore,
    required this.lastUpdate,
    required this.latitude,
    required this.longitude,
    required this.nearbyFaults,
    required this.recentEvents,
    required this.factors,
    required this.summary,
    required this.shortRisk,
    required this.longHazard,
    required this.faultScore,
    required this.faultDistanceKm,
    required this.mapEvents,
    required this.heatmapEvents,
    required this.faultLines,
    required this.mapHtml,
    required this.usedManualCoordinates,
    required this.nearbyQuakeCount,
    required this.maxMagnitude,
    required this.averageDepth,
    required this.heatSampleCount,
    required this.totalFaultFeatures,
    required this.technicalLayers,
    required this.technicalQuakes,
    required this.refreshMessage,
  });

  factory RiskModuleResult.fromJson(Map<String, dynamic> json) {
    final coordinates = (json['coordinates'] as Map<String, dynamic>? ?? {});
    final metrics = (json['metrics'] as Map<String, dynamic>? ?? {});

    return RiskModuleResult(
      city: json['city'] as String? ?? '',
      riskLevel: json['riskLevel'] as String? ?? '',
      riskScore: (json['riskScore'] as num?)?.toDouble() ?? 0,
      lastUpdate: json['lastUpdate'] as String? ?? 'Bilinmiyor',
      latitude: (coordinates['lat'] as num?)?.toDouble() ?? 0,
      longitude: (coordinates['lon'] as num?)?.toDouble() ?? 0,
      nearbyFaults: ((json['nearbyFaults'] as List?) ?? const [])
          .map((item) => item.toString())
          .toList(),
      recentEvents: ((json['recentEvents'] as List?) ?? const [])
          .map((item) => item.toString())
          .toList(),
      factors: ((json['factors'] as Map?) ?? const {}).map(
        (key, value) => MapEntry(key.toString(), (value as num).toDouble()),
      ),
      summary: json['summary'] as String? ?? '',
      shortRisk: (metrics['shortRisk'] as num?)?.toDouble() ?? 0,
      longHazard: (metrics['longHazard'] as num?)?.toDouble() ?? 0,
      faultScore: (metrics['faultScore'] as num?)?.toDouble() ?? 0,
      faultDistanceKm: (metrics['faultDistanceKm'] as num?)?.toDouble() ?? 0,
      mapEvents: ((json['mapEvents'] as List?) ?? const [])
          .map(
            (item) =>
                RiskMapEvent.fromJson((item as Map).cast<String, dynamic>()),
          )
          .toList(),
      heatmapEvents: ((json['heatmapEvents'] as List?) ?? const [])
          .map(
            (item) =>
                RiskMapEvent.fromJson((item as Map).cast<String, dynamic>()),
          )
          .toList(),
      faultLines: ((json['faultLines'] as List?) ?? const [])
          .map(
            (item) =>
                RiskFaultLine.fromJson((item as Map).cast<String, dynamic>()),
          )
          .toList(),
      mapHtml: json['mapHtml'] as String? ?? '',
      usedManualCoordinates:
          json['usedManualCoordinates'] as bool? ?? false,
      nearbyQuakeCount: (metrics['nearbyQuakeCount'] as num?)?.toInt() ?? 0,
      maxMagnitude: (metrics['maxMagnitude'] as num?)?.toDouble() ?? 0,
      averageDepth: (metrics['averageDepth'] as num?)?.toDouble() ?? 0,
      heatSampleCount: (metrics['heatSampleCount'] as num?)?.toInt() ?? 0,
      totalFaultFeatures:
          (metrics['totalFaultFeatures'] as num?)?.toInt() ?? 0,
      technicalLayers: ((json['technicalLayers'] as List?) ?? const [])
          .map(
            (item) => RiskTechnicalLayer.fromJson(
              (item as Map).cast<String, dynamic>(),
            ),
          )
          .toList(),
      technicalQuakes: ((json['technicalQuakes'] as List?) ?? const [])
          .map(
            (item) =>
                RiskTechnicalQuake.fromJson((item as Map).cast<String, dynamic>()),
          )
          .toList(),
      refreshMessage: json['refreshMessage'] as String? ?? '',
    );
  }

  final String city;
  final String riskLevel;
  final double riskScore;
  final String lastUpdate;
  final double latitude;
  final double longitude;
  final List<String> nearbyFaults;
  final List<String> recentEvents;
  final Map<String, double> factors;
  final String summary;
  final double shortRisk;
  final double longHazard;
  final double faultScore;
  final double faultDistanceKm;
  final List<RiskMapEvent> mapEvents;
  final List<RiskMapEvent> heatmapEvents;
  final List<RiskFaultLine> faultLines;
  final String mapHtml;
  final bool usedManualCoordinates;
  final int nearbyQuakeCount;
  final double maxMagnitude;
  final double averageDepth;
  final int heatSampleCount;
  final int totalFaultFeatures;
  final List<RiskTechnicalLayer> technicalLayers;
  final List<RiskTechnicalQuake> technicalQuakes;
  final String refreshMessage;
}

class RiskMapEvent {
  const RiskMapEvent({
    required this.label,
    required this.latitude,
    required this.longitude,
    required this.magnitude,
    required this.timeLabel,
  });

  factory RiskMapEvent.fromJson(Map<String, dynamic> json) {
    return RiskMapEvent(
      label: json['label'] as String? ?? '',
      latitude: (json['latitude'] as num?)?.toDouble() ?? 0,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 0,
      magnitude: (json['magnitude'] as num?)?.toDouble() ?? 0,
      timeLabel: json['timeLabel'] as String? ?? '',
    );
  }

  final String label;
  final double latitude;
  final double longitude;
  final double magnitude;
  final String timeLabel;
}

class RiskFaultLine {
  const RiskFaultLine({required this.name, required this.points});

  factory RiskFaultLine.fromJson(Map<String, dynamic> json) {
    return RiskFaultLine(
      name: json['name'] as String? ?? '',
      points: ((json['points'] as List?) ?? const [])
          .map(
            (item) =>
                RiskGeoPoint.fromJson((item as Map).cast<String, dynamic>()),
          )
          .toList(),
    );
  }

  final String name;
  final List<RiskGeoPoint> points;
}

class RiskGeoPoint {
  const RiskGeoPoint({required this.latitude, required this.longitude});

  factory RiskGeoPoint.fromJson(Map<String, dynamic> json) {
    return RiskGeoPoint(
      latitude: (json['latitude'] as num?)?.toDouble() ?? 0,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 0,
    );
  }

  final double latitude;
  final double longitude;
}

class RiskTechnicalLayer {
  const RiskTechnicalLayer({
    required this.name,
    required this.path,
    required this.featureCount,
  });

  factory RiskTechnicalLayer.fromJson(Map<String, dynamic> json) {
    return RiskTechnicalLayer(
      name: json['name'] as String? ?? '',
      path: json['path'] as String? ?? '',
      featureCount: (json['featureCount'] as num?)?.toInt() ?? 0,
    );
  }

  final String name;
  final String path;
  final int featureCount;
}

class RiskTechnicalQuake {
  const RiskTechnicalQuake({
    required this.time,
    required this.place,
    required this.magnitude,
    required this.depth,
    required this.distanceKm,
    required this.latitude,
    required this.longitude,
  });

  factory RiskTechnicalQuake.fromJson(Map<String, dynamic> json) {
    return RiskTechnicalQuake(
      time: json['time'] as String? ?? '',
      place: json['place'] as String? ?? '',
      magnitude: (json['magnitude'] as num?)?.toDouble() ?? 0,
      depth: (json['depth'] as num?)?.toDouble() ?? 0,
      distanceKm: (json['distanceKm'] as num?)?.toDouble() ?? 0,
      latitude: (json['latitude'] as num?)?.toDouble() ?? 0,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 0,
    );
  }

  final String time;
  final String place;
  final double magnitude;
  final double depth;
  final double distanceKm;
  final double latitude;
  final double longitude;
}
