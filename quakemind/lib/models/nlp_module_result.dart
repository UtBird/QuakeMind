import 'dart:convert';

class NlpModuleResult {
  const NlpModuleResult({
    required this.category,
    required this.confidence,
    required this.urgency,
    required this.locationText,
    required this.coordinates,
    required this.candidates,
    required this.jsonPayload,
    required this.isRelevant,
  });

  factory NlpModuleResult.fromJson(Map<String, dynamic> json) {
    final coordinates = (json['konum'] as List?) ?? const [];
    final normalizedJson = Map<String, dynamic>.from(json);

    return NlpModuleResult(
      category: json['kategori'] as String? ?? 'Bilinmiyor',
      confidence: (json['guven_skoru'] as num?)?.toDouble() ?? 0,
      urgency: (json['aciliyet'] as num?)?.toInt() ?? 0,
      locationText: json['konum_metin'] as String? ?? '',
      coordinates: coordinates.length >= 2
          ? NlpCoordinates(
              latitude: (coordinates[0] as num).toDouble(),
              longitude: (coordinates[1] as num).toDouble(),
            )
          : null,
      candidates: ((json['konum_adaylari'] as List?) ?? const [])
          .map((item) => item.toString())
          .toList(),
      jsonPayload: const JsonEncoder.withIndent('  ').convert(normalizedJson),
      isRelevant: json['isRelevant'] as bool? ?? true,
    );
  }

  final String category;
  final double confidence;
  final int urgency;
  final String locationText;
  final NlpCoordinates? coordinates;
  final List<String> candidates;
  final String jsonPayload;
  final bool isRelevant;
}

class NlpCoordinates {
  const NlpCoordinates({required this.latitude, required this.longitude});

  final double latitude;
  final double longitude;
}
