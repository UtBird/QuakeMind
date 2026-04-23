import 'package:flutter/material.dart';

class ModuleSummary {
  const ModuleSummary({
    required this.title,
    required this.subtitle,
    required this.status,
    required this.icon,
    required this.color,
    required this.highlights,
  });

  final String title;
  final String subtitle;
  final String status;
  final IconData icon;
  final Color color;
  final List<String> highlights;
}

class CityRiskData {
  const CityRiskData({
    required this.city,
    required this.riskLevel,
    required this.riskScore,
    required this.lastUpdate,
    required this.coordinates,
    required this.nearbyFaults,
    required this.recentEvents,
    required this.factors,
  });

  final String city;
  final String riskLevel;
  final double riskScore;
  final String lastUpdate;
  final Offset coordinates;
  final List<String> nearbyFaults;
  final List<String> recentEvents;
  final Map<String, double> factors;
}

class NlpResult {
  const NlpResult({
    required this.category,
    required this.confidence,
    required this.urgency,
    required this.locationText,
    required this.coordinates,
    required this.candidates,
    required this.jsonPayload,
  });

  final String category;
  final double confidence;
  final int urgency;
  final String locationText;
  final Offset coordinates;
  final List<String> candidates;
  final String jsonPayload;
}

class RoadDamageReport {
  const RoadDamageReport({
    required this.areaName,
    required this.damageRate,
    required this.openRoads,
    required this.blockedRoads,
    required this.recommendedAction,
    required this.logLines,
  });

  final String areaName;
  final double damageRate;
  final int openRoads;
  final int blockedRoads;
  final String recommendedAction;
  final List<String> logLines;
}

class CameraDetection {
  const CameraDetection({
    required this.label,
    required this.confidence,
    required this.severity,
    required this.time,
  });

  final String label;
  final double confidence;
  final String severity;
  final String time;
}
