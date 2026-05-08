class RoadDamageResult {
  const RoadDamageResult({
    required this.city,
    required this.damageRate,
    required this.openRoads,
    required this.blockedRoads,
    required this.openRoadPct,
    required this.blockedRoadPct,
    required this.logLines,
    required this.recommendedAction,
    required this.imageWidth,
    required this.imageHeight,
    required this.damageBooster,
    required this.threshold,
    required this.safeRoadSegments,
    required this.blockedRoadSegments,
    required this.satelliteSource,
    required this.satelliteTileUrl,
    required this.satelliteAttribution,
    required this.timingsMs,
  });

  factory RoadDamageResult.fromJson(Map<String, dynamic> json) {
    return RoadDamageResult(
      city: json['city'] as String? ?? '',
      damageRate: (json['damageRate'] as num?)?.toDouble() ?? 0,
      openRoads: (json['openRoads'] as num?)?.toInt() ?? 0,
      blockedRoads: (json['blockedRoads'] as num?)?.toInt() ?? 0,
      openRoadPct: (json['openRoadPct'] as num?)?.toDouble() ?? 0,
      blockedRoadPct: (json['blockedRoadPct'] as num?)?.toDouble() ?? 0,
      logLines: ((json['logLines'] as List?) ?? const [])
          .map((item) => item.toString())
          .toList(),
      recommendedAction: json['recommendedAction'] as String? ?? '',
      imageWidth: (json['imageWidth'] as num?)?.toInt() ?? 0,
      imageHeight: (json['imageHeight'] as num?)?.toInt() ?? 0,
      damageBooster: (json['damageBooster'] as num?)?.toDouble() ?? 3.5,
      threshold: (json['threshold'] as num?)?.toDouble() ?? 0.4,
      safeRoadSegments: _parseSegments(json['safeRoadSegments']),
      blockedRoadSegments: _parseSegments(json['blockedRoadSegments']),
      satelliteSource: json['satelliteSource'] as String? ?? '',
      satelliteTileUrl: json['satelliteTileUrl'] as String? ?? '',
      satelliteAttribution: json['satelliteAttribution'] as String? ?? '',
      timingsMs: _parseTimings(json['timingsMs']),
    );
  }

  static List<List<RoadPoint>> _parseSegments(dynamic raw) {
    if (raw is! List) return const [];
    return raw
        .whereType<List>()
        .map((segment) {
          return segment
              .whereType<List>()
              .where((pt) => pt.length >= 2)
              .map((pt) {
                final lat = (pt[0] as num?)?.toDouble();
                final lon = (pt[1] as num?)?.toDouble();
                if (lat == null || lon == null) return null;
                return RoadPoint(lat, lon);
              })
              .whereType<RoadPoint>()
              .toList();
        })
        .where((segment) => segment.length >= 2)
        .toList();
  }

  static Map<String, double> _parseTimings(dynamic raw) {
    if (raw is! Map) return const {};
    final out = <String, double>{};
    for (final entry in raw.entries) {
      final key = entry.key.toString();
      final value = (entry.value as num?)?.toDouble();
      if (value != null) out[key] = value;
    }
    return out;
  }

  final String city;
  final double damageRate;
  final int openRoads;
  final int blockedRoads;
  final double openRoadPct;
  final double blockedRoadPct;
  final List<String> logLines;
  final String recommendedAction;
  final int imageWidth;
  final int imageHeight;
  final double damageBooster;
  final double threshold;
  final List<List<RoadPoint>> safeRoadSegments;
  final List<List<RoadPoint>> blockedRoadSegments;
  final String satelliteSource;
  final String satelliteTileUrl;
  final String satelliteAttribution;
  final Map<String, double> timingsMs;
}

class RoadPoint {
  const RoadPoint(this.latitude, this.longitude);

  final double latitude;
  final double longitude;
}
