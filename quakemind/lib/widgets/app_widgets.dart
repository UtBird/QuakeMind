import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart' show LatLng;
import 'package:webview_flutter/webview_flutter.dart';

import '../models/road_damage_result.dart';
import '../models/risk_module_result.dart';
import '../theme/app_theme.dart';

class SectionCard extends StatelessWidget {
  const SectionCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.color,
  });

  final Widget child;
  final EdgeInsets padding;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: color ?? Colors.white,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: const Color(0xFFF0E7D8)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x140D1B2A),
            blurRadius: 24,
            offset: Offset(0, 14),
          ),
        ],
      ),
      child: Padding(padding: padding, child: child),
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle({super.key, required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 6),
        Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
      ],
    );
  }
}

class MetricTile extends StatelessWidget {
  const MetricTile({
    super.key,
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 10),
          Text(
            value,
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(color: color),
          ),
        ],
      ),
    );
  }
}

class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          color: color,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class FakeMapPanel extends StatelessWidget {
  const FakeMapPanel({
    super.key,
    this.title = 'Harita katmani',
    required this.markers,
    this.height = 240,
  });

  final String title;
  final List<Alignment> markers;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(26),
        gradient: const LinearGradient(
          colors: [Color(0xFF0E3B43), Color(0xFF1A6B75), Color(0xFF90B77D)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Stack(
        children: [
          Positioned.fill(child: CustomPaint(painter: _TerrainPainter())),
          Positioned(
            left: 18,
            top: 18,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.88),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
          ),
          for (final marker in markers)
            Align(
              alignment: marker,
              child: Container(
                width: 18,
                height: 18,
                decoration: BoxDecoration(
                  color: AppTheme.accent,
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: Colors.white, width: 3),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x55000000),
                      blurRadius: 12,
                      offset: Offset(0, 6),
                    ),
                  ],
                ),
              ),
            ),
          Align(
            alignment: Alignment.bottomRight,
            child: Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.25),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Text(
                'Mobil taslak harita',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class RiskMapPanel extends StatefulWidget {
  const RiskMapPanel({
    super.key,
    required this.title,
    required this.city,
    required this.result,
    this.height = 280,
    this.showHeatmapMode = true,
  });

  final String title;
  final String city;
  final RiskModuleResult result;
  final double height;
  final bool showHeatmapMode;

  @override
  State<RiskMapPanel> createState() => _RiskMapPanelState();
}

enum _RiskMapMode { overview, heatmap, technical }

class _RiskMapPanelState extends State<RiskMapPanel> {
  _RiskMapMode _mode = _RiskMapMode.overview;
  late final WebViewController _webViewController;

  @override
  void initState() {
    super.initState();
    if (!widget.showHeatmapMode) {
      _mode = _RiskMapMode.overview;
    }
    _webViewController = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(Colors.transparent)
      ..setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (request) => NavigationDecision.navigate,
        ),
      )
      ..loadRequest(_buildMapUri(widget.result.mapHtml));
  }

  @override
  void didUpdateWidget(covariant RiskMapPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.result.mapHtml != widget.result.mapHtml) {
      _webViewController.loadRequest(_buildMapUri(widget.result.mapHtml));
    }
  }

  Uri _buildMapUri(String html) {
    return Uri.dataFromString(html, mimeType: 'text/html', encoding: utf8);
  }

  @override
  Widget build(BuildContext context) {
    final segments = <ButtonSegment<_RiskMapMode>>[
      const ButtonSegment(
        value: _RiskMapMode.overview,
        label: Text('Genel Harita'),
        icon: Icon(Icons.map_outlined),
      ),
      if (widget.showHeatmapMode)
        const ButtonSegment(
          value: _RiskMapMode.heatmap,
          label: Text('Isi Haritasi'),
          icon: Icon(Icons.local_fire_department_outlined),
        ),
      const ButtonSegment(
        value: _RiskMapMode.technical,
        label: Text('Teknik Katman'),
        icon: Icon(Icons.timeline),
      ),
    ];

    return Container(
      height: widget.height,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: const Color(0xFFF0E7D8)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x140D1B2A),
            blurRadius: 24,
            offset: Offset(0, 14),
          ),
        ],
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 18, 18, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.title,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 4),
                Text(
                  '${widget.city} merkezli canli harita katmanlari',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: AppTheme.ink,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Text(
                    '${widget.result.totalFaultFeatures} segment / ${widget.result.nearbyQuakeCount} deprem',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 18),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: SegmentedButton<_RiskMapMode>(
                segments: segments,
                selected: {_mode},
                onSelectionChanged: (value) {
                  setState(() {
                    _mode = value.first;
                  });
                },
              ),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(22),
              child: _mode == _RiskMapMode.technical
                  ? _RiskTechnicalPanel(result: widget.result)
                  : Stack(
                      children: [
                        WebViewWidget(controller: _webViewController),
                        Positioned(
                          left: 14,
                          top: 14,
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 10,
                            ),
                            decoration: BoxDecoration(
                              color: const Color(0xDD0D1B2A),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const _MapLegendRow(
                                  color: Color(0xFFCC5A31),
                                  label: 'Ana faylar',
                                ),
                                const SizedBox(height: 6),
                                const _MapLegendRow(
                                  color: Color(0xFFF7C548),
                                  label: 'Deprem odaklari',
                                ),
                                const SizedBox(height: 6),
                                const _MapLegendRow(
                                  color: Color(0xFFE63946),
                                  label: 'Secili sehir',
                                ),
                                if (widget.showHeatmapMode &&
                                    _mode == _RiskMapMode.heatmap) ...[
                                  const SizedBox(height: 6),
                                  const _MapLegendRow(
                                    color: Color(0xFF4CC9F0),
                                    label: 'Isi katmani acik',
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
            ),
          ),
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: AppTheme.sand,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Text(
                _mode == _RiskMapMode.technical
                    ? 'Teknik katmanda backend tarafindaki detayli fay GeoJSON sayilari ve en guclu 20 deprem listeleniyor.'
                    : widget.showHeatmapMode
                    ? 'Bu harita backendde uretilen gercek Folium icerigini gosterir. Harita uzerinde gezinebilir, yakinlasabilir ve layer control ile isi haritasi ile fay katmanlarini acip kapatabilirsin.'
                    : 'Bu harita backendde uretilen gercek Folium icerigini gosterir. Harita uzerinde gezinebilir, yakinlasabilir ve katmanlari inceleyebilirsin.',
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w500),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RiskTechnicalPanel extends StatelessWidget {
  const _RiskTechnicalPanel({required this.result});

  final RiskModuleResult result;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            SizedBox(
              width: 170,
              child: MetricTile(
                label: '150 km icindeki deprem',
                value: '${result.nearbyQuakeCount}',
                color: const Color(0xFFE15B64),
              ),
            ),
            SizedBox(
              width: 170,
              child: MetricTile(
                label: 'Maksimum buyukluk',
                value: result.maxMagnitude.toStringAsFixed(2),
                color: const Color(0xFF15616D),
              ),
            ),
            SizedBox(
              width: 170,
              child: MetricTile(
                label: 'Ortalama derinlik',
                value: '${result.averageDepth.toStringAsFixed(1)} km',
                color: const Color(0xFF5A6C7D),
              ),
            ),
          ],
        ),
        const SizedBox(height: 18),
        Text(
          'GeoJSON fay katmanlari',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        ...result.technicalLayers.map(
          (layer) => ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(
              Icons.account_tree_outlined,
              color: AppTheme.accent,
            ),
            title: Text(layer.name),
            subtitle: Text(layer.path),
            trailing: Text('${layer.featureCount}'),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Toplam gosterilen detayli fay segmenti: ${result.totalFaultFeatures}',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 18),
        Text(
          'En guclu 20 deprem kaydi',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        ...result.technicalQuakes.map(
          (quake) => Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFF8F3E7),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              'M${quake.magnitude.toStringAsFixed(1)}  |  ${quake.place}\n'
              '${quake.time}\n'
              'Derinlik: ${quake.depth.toStringAsFixed(1)} km  |  Mesafe: ${quake.distanceKm.toStringAsFixed(1)} km',
            ),
          ),
        ),
        if (result.technicalQuakes.isEmpty)
          const Text(
            'Bu bolge icin teknik listelenecek deprem kaydi bulunamadi.',
          ),
      ],
    );
  }
}

class GeoMarkerData {
  const GeoMarkerData({
    required this.latitude,
    required this.longitude,
    required this.label,
    this.highlight = false,
  });

  final double latitude;
  final double longitude;
  final String label;
  final bool highlight;
}

class GeoPointsMapPanel extends StatelessWidget {
  const GeoPointsMapPanel({
    super.key,
    required this.title,
    required this.subtitle,
    required this.markers,
    this.height = 280,
  });

  final String title;
  final String subtitle;
  final List<GeoMarkerData> markers;
  final double height;

  @override
  Widget build(BuildContext context) {
    final center = markers.isNotEmpty
        ? LatLng(markers.last.latitude, markers.last.longitude)
        : const LatLng(39.0, 35.0);

    return Container(
      height: height,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: const Color(0xFFF0E7D8)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x140D1B2A),
            blurRadius: 24,
            offset: Offset(0, 14),
          ),
        ],
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 18, 18, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                Text(subtitle, style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: AppTheme.ink,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Text(
                    '${markers.length} konum',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(22),
              child: FlutterMap(
                options: MapOptions(
                  initialCenter: center,
                  initialZoom: markers.isNotEmpty ? 11 : 5.5,
                ),
                children: [
                  TileLayer(
                    urlTemplate:
                        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'com.example.quakemind',
                  ),
                  MarkerLayer(
                    markers: markers
                        .map(
                          (item) => Marker(
                            point: LatLng(item.latitude, item.longitude),
                            width: 32,
                            height: 32,
                            child: Tooltip(
                              message: item.label,
                              child: Icon(
                                item.highlight
                                    ? Icons.location_on
                                    : Icons.location_pin,
                                color: item.highlight
                                    ? const Color(0xFFE15B64)
                                    : const Color(0xFF15616D),
                                size: item.highlight ? 30 : 24,
                              ),
                            ),
                          ),
                        )
                        .toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: AppTheme.sand,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Text(
                markers.isEmpty
                    ? 'Metinden cikarilan koordinat bulunamadiginda bu panel bos kalir.'
                    : 'Harita, NLP analizinde cikarilan konumlari oturum bazli biriktirerek gosterir.',
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w500),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class RoadLogisticsMapPanel extends StatelessWidget {
  const RoadLogisticsMapPanel({
    super.key,
    required this.title,
    required this.result,
    this.height = 320,
  });

  final String title;
  final RoadDamageResult result;
  final double height;

  @override
  Widget build(BuildContext context) {
    final blockedPoints = result.blockedRoadSegments.expand((s) => s).toList();
    final safePoints = result.safeRoadSegments.expand((s) => s).toList();
    final centerPoint = blockedPoints.isNotEmpty
        ? blockedPoints.first
        : (safePoints.isNotEmpty
              ? safePoints.first
              : const RoadPoint(37.0, 35.0));

    final blockedPolylines = result.blockedRoadSegments
        .map(
          (segment) => Polyline(
            points: segment
                .map((p) => LatLng(p.latitude, p.longitude))
                .toList(growable: false),
            color: const Color(0xFFE15B64),
            strokeWidth: 4,
          ),
        )
        .toList(growable: false);

    final safePolylines = result.safeRoadSegments
        .map(
          (segment) => Polyline(
            points: segment
                .map((p) => LatLng(p.latitude, p.longitude))
                .toList(growable: false),
            color: AppTheme.teal,
            strokeWidth: 3,
          ),
        )
        .toList(growable: false);

    return Container(
      height: height,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: const Color(0xFFF0E7D8)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x140D1B2A),
            blurRadius: 24,
            offset: Offset(0, 14),
          ),
        ],
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 18, 18, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                Text(
                  '${result.city} - acik/kapali yol cizimleri',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    StatusPill(
                      label: 'Kapali segment: ${result.blockedRoadSegments.length}',
                      color: const Color(0xFFE15B64),
                    ),
                    StatusPill(
                      label: 'Acik segment: ${result.safeRoadSegments.length}',
                      color: AppTheme.teal,
                    ),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(22),
              child: FlutterMap(
                options: MapOptions(
                  initialCenter: LatLng(
                    centerPoint.latitude,
                    centerPoint.longitude,
                  ),
                  initialZoom: 14,
                ),
                children: [
                  TileLayer(
                    urlTemplate:
                        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'com.example.quakemind',
                  ),
                  PolylineLayer(polylines: safePolylines),
                  PolylineLayer(polylines: blockedPolylines),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: AppTheme.sand,
                borderRadius: BorderRadius.circular(18),
              ),
              child: const Text(
                'Yesil cizgiler acik yollari, kirmizi cizgiler engelli/kapali yol segmentlerini gosterir.',
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MapLegendRow extends StatelessWidget {
  const _MapLegendRow({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(99),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _TerrainPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final linePaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.18)
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    final routePaint = Paint()
      ..color = const Color(0xFFF8F3D6).withValues(alpha: 0.9)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final path1 = Path()
      ..moveTo(size.width * 0.08, size.height * 0.18)
      ..quadraticBezierTo(
        size.width * 0.36,
        size.height * 0.1,
        size.width * 0.56,
        size.height * 0.22,
      )
      ..quadraticBezierTo(
        size.width * 0.78,
        size.height * 0.34,
        size.width * 0.92,
        size.height * 0.24,
      );
    canvas.drawPath(path1, linePaint);

    final path2 = Path()
      ..moveTo(size.width * 0.15, size.height * 0.82)
      ..quadraticBezierTo(
        size.width * 0.42,
        size.height * 0.68,
        size.width * 0.64,
        size.height * 0.72,
      )
      ..quadraticBezierTo(
        size.width * 0.82,
        size.height * 0.78,
        size.width * 0.94,
        size.height * 0.62,
      );
    canvas.drawPath(path2, routePaint);

    for (var i = 1; i < 6; i++) {
      final y = size.height * i / 6;
      canvas.drawLine(
        Offset(0, y),
        Offset(size.width, y),
        linePaint..strokeWidth = 1.2,
      );
    }
    for (var i = 1; i < 5; i++) {
      final x = size.width * i / 5;
      canvas.drawLine(
        Offset(x, 0),
        Offset(x, size.height),
        linePaint..strokeWidth = 1.2,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
