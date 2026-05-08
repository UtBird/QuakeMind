import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../data/mock_data.dart';
import '../models/nlp_module_result.dart';
import '../models/risk_module_result.dart';
import '../models/road_damage_result.dart';
import '../services/nlp_module_service.dart';
import '../services/risk_module_service.dart';
import '../services/road_damage_service.dart';
import '../services/server_status_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';
import '../widgets/ip_config_dialog.dart';
import '../widgets/live_camera_view.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;
  String _selectedCity = turkeyCities.first;
  String _selectedRoadCity = roadCities.first;
  String _selectedSource = 'OpenAerialMap';
  String _selectedSample = nlpSamples.first;
  double _damageBooster = 3.5;
  double _threshold = 0.40;
  bool _useImagenetNorm = true;
  int _postProcessLevel = 2;

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      _DashboardPage(onOpenModule: _openModule),
      _RiskPage(
        city: _selectedCity,
        onCityChanged: (value) => setState(() => _selectedCity = value!),
      ),
      _RoadDamagePage(
        city: _selectedRoadCity,
        source: _selectedSource,
        damageBooster: _damageBooster,
        threshold: _threshold,
        useImagenetNorm: _useImagenetNorm,
        postProcessLevel: _postProcessLevel,
        onCityChanged: (value) => setState(() => _selectedRoadCity = value!),
        onSourceChanged: (value) => setState(() => _selectedSource = value!),
        onDamageBoosterChanged: (value) =>
            setState(() => _damageBooster = value),
        onThresholdChanged: (value) => setState(() => _threshold = value),
        onNormalizationChanged: (value) =>
            setState(() => _useImagenetNorm = value),
        onPostProcessChanged: (value) =>
            setState(() => _postProcessLevel = value),
      ),
      _NlpPage(
        sample: _selectedSample,
        onSampleChanged: (value) => setState(() => _selectedSample = value!),
      ),
      const _CameraPage(),
    ];

    return Scaffold(
      body: Stack(
        children: [
          const Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppTheme.bg, Color(0xFF0D1526), Color(0xFF0A1220)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
            ),
          ),
          Positioned(
            right: -60,
            top: -80,
            child: IgnorePointer(
              child: Container(
                width: 220,
                height: 220,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppTheme.teal.withValues(alpha: 0.12),
                ),
              ),
            ),
          ),
          Positioned(
            left: -40,
            bottom: 110,
            child: IgnorePointer(
              child: Container(
                width: 180,
                height: 180,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppTheme.accent.withValues(alpha: 0.08),
                ),
              ),
            ),
          ),
          SafeArea(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 250),
              child: KeyedSubtree(key: ValueKey(_index), child: pages[_index]),
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        minimum: const EdgeInsets.fromLTRB(14, 0, 14, 12),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    AppTheme.panelHigh.withValues(alpha: 0.48),
                    AppTheme.panel.withValues(alpha: 0.34),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppTheme.glassStroke),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x66000000),
                    blurRadius: 24,
                    offset: Offset(0, 12),
                  ),
                ],
              ),
              child: NavigationBar(
                selectedIndex: _index,
                onDestinationSelected: (value) =>
                    setState(() => _index = value),
                destinations: const [
                  NavigationDestination(
                    icon: Icon(Icons.dashboard_customize),
                    label: 'Panel',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.public),
                    label: 'Risk',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.satellite_alt),
                    label: 'Uydu',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.crisis_alert),
                    label: 'NLP',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.videocam),
                    label: 'Kamera',
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _openModule(int index) {
    setState(() => _index = index);
  }
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

class _DashboardPage extends StatefulWidget {
  const _DashboardPage({required this.onOpenModule});

  final ValueChanged<int> onOpenModule;

  @override
  State<_DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<_DashboardPage> {
  static const _statusService = ServerStatusService();
  ServerStatus? _status;
  bool _checking = false;

  @override
  void initState() {
    super.initState();
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    setState(() => _checking = true);
    final status = await _statusService.checkStatus();
    if (mounted) {
      setState(() {
        _status = status;
        _checking = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 120),
      children: [
        const _AppHeader(
          title: 'QuakeMind Mobile',
          subtitle:
              'Afet mudahale operasyon paneli. Hotspot ile baglanti kurarak tum modullere erisin.',
        ),
        const SizedBox(height: 18),
        _buildConnectionCard(context),
        const SizedBox(height: 18),
        _buildModuleStatusCard(context),
        const SizedBox(height: 18),
        ...List.generate(moduleSummaries.length, (index) {
          final module = moduleSummaries[index];
          return Padding(
            padding: EdgeInsets.only(
              bottom: index == moduleSummaries.length - 1 ? 0 : 16,
            ),
            child: SectionCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 52,
                        height: 52,
                        decoration: BoxDecoration(
                          color: module.color.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: Icon(module.icon, color: module.color),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              module.title,
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              module.subtitle,
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _moduleStatusPill(index),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: module.highlights
                        .map(
                          (item) => Chip(
                            label: Text(item),
                            backgroundColor: AppTheme.sand,
                          ),
                        )
                        .toList(),
                  ),
                  const SizedBox(height: 16),
                  Align(
                    alignment: Alignment.centerRight,
                    child: FilledButton(
                      onPressed: () => widget.onOpenModule(index + 1),
                      child: const Text('Modulu Ac'),
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _moduleStatusPill(int index) {
    if (_status == null) {
      return StatusPill(
        label: moduleSummaries[index].status,
        color: moduleSummaries[index].color,
      );
    }

    final s = _status!;
    bool ready;
    switch (index) {
      case 0: // Risk
        ready = s.riskReady;
        break;
      case 1: // Road Damage
        ready = s.roadDamageReady;
        break;
      case 2: // NLP
        ready = s.nlpReady;
        break;
      default: // Camera - local
        ready = true;
    }

    if (!s.isOnline) {
      return const StatusPill(
        label: 'Sunucu baglantisi yok',
        color: Color(0xFFE15B64),
      );
    }

    return StatusPill(
      label: ready ? 'Backend bagli - Hazir' : 'Modul yuklenemedi',
      color: ready ? AppTheme.teal : const Color(0xFFF59F00),
    );
  }

  Widget _buildConnectionCard(BuildContext context) {
    final isOnline = _status?.isOnline ?? false;
    return SectionCard(
      color: isOnline ? AppTheme.ink : const Color(0xFF4A1C1C),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isOnline ? Icons.wifi : Icons.wifi_off,
                color: isOnline ? AppTheme.teal : const Color(0xFFE15B64),
                size: 28,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  isOnline
                      ? 'Backend sunucusuna baglanildi'
                      : 'Sunucu baglantisi kurulamadi',
                  style: Theme.of(
                    context,
                  ).textTheme.headlineMedium?.copyWith(color: Colors.white),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            isOnline
                ? 'Tum moduller backend API uzerinden calismaya hazir. PC hotspot baglantisi aktif.'
                : 'PC uzerinden hotspot ac, sunucuyu baslat ve telefonu bu hotspot\'a bagla.',
            style: const TextStyle(color: Color(0xFFD8E1EA), height: 1.5),
          ),
          const SizedBox(height: 16),
          if (isOnline)
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                StatusPill(
                  label: _status!.riskReady
                      ? 'Risk Modulu Hazir'
                      : 'Risk Yuklenemedi',
                  color: _status!.riskReady
                      ? AppTheme.teal
                      : const Color(0xFFF59F00),
                ),
                StatusPill(
                  label: _status!.nlpReady
                      ? 'NLP Modulu Hazir'
                      : 'NLP Yuklenemedi',
                  color: _status!.nlpReady
                      ? AppTheme.teal
                      : const Color(0xFFF59F00),
                ),
                StatusPill(
                  label: _status!.roadDamageReady
                      ? 'Uydu Modulu Hazir'
                      : 'Uydu Yuklenemedi',
                  color: _status!.roadDamageReady
                      ? AppTheme.teal
                      : const Color(0xFFF59F00),
                ),
              ],
            ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              OutlinedButton.icon(
                onPressed: () async {
                  await showDialog(
                    context: context,
                    builder: (_) => const IpConfigDialog(),
                  );
                  _checkConnection();
                },
                icon: const Icon(Icons.settings_ethernet),
                label: const Text('Sunucu Ayari'),
              ),
              OutlinedButton.icon(
                onPressed: _checking ? null : _checkConnection,
                icon: _checking
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.refresh),
                label: const Text('Baglantiyi Test Et'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildModuleStatusCard(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Kullanim Talimati',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          const _InstructionStep(
            number: '1',
            text:
                'Bilgisayarda hotspot ac (Linux: nm-connection-editor, Windows: Mobil etkin nokta)',
          ),
          const _InstructionStep(
            number: '2',
            text:
                'Bilgisayarda: python3 fastapi_app.py komutu ile sunucuyu baslat',
          ),
          const _InstructionStep(
            number: '3',
            text: 'Telefonu bilgisayarin hotspot\'una bagla',
          ),
          const _InstructionStep(
            number: '4',
            text:
                'Sunucu Ayari\'ndan PC IP\'sini gir (Linux: 10.42.0.1:8000, Windows: 192.168.137.1:8000)',
          ),
          const _InstructionStep(
            number: '5',
            text:
                'Baglantiyi Test Et ile dogrula, sonra modulleri kullanmaya basla',
          ),
        ],
      ),
    );
  }
}

class _InstructionStep extends StatelessWidget {
  const _InstructionStep({required this.number, required this.text});

  final String number;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: AppTheme.teal.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(99),
            ),
            alignment: Alignment.center,
            child: Text(
              number,
              style: const TextStyle(
                color: AppTheme.teal,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Risk Page
// ---------------------------------------------------------------------------

class _RiskPage extends StatefulWidget {
  const _RiskPage({required this.city, required this.onCityChanged});

  final String city;
  final ValueChanged<String?> onCityChanged;

  @override
  State<_RiskPage> createState() => _RiskPageState();
}

class _RiskPageState extends State<_RiskPage> {
  static const _service = RiskModuleService();

  late Future<RiskModuleResult> _future;
  final _manualLatitudeController = TextEditingController();
  final _manualLongitudeController = TextEditingController();
  bool _useManualCoordinates = false;

  @override
  void initState() {
    super.initState();
    _future = _loadRisk();
  }

  @override
  void dispose() {
    _manualLatitudeController.dispose();
    _manualLongitudeController.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant _RiskPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.city != widget.city) {
      _future = _loadRisk();
    }
  }

  Future<RiskModuleResult> _loadRisk({bool refreshData = false}) async {
    final manualLatitude = _useManualCoordinates
        ? double.tryParse(_manualLatitudeController.text.replaceAll(',', '.'))
        : null;
    final manualLongitude = _useManualCoordinates
        ? double.tryParse(_manualLongitudeController.text.replaceAll(',', '.'))
        : null;

    if (_useManualCoordinates &&
        (manualLatitude == null || manualLongitude == null)) {
      throw Exception('Manuel koordinat icin gecerli enlem ve boylam gir.');
    }

    final result = await _service.fetchCityRisk(
      widget.city,
      refreshData: refreshData,
      manualLatitude: manualLatitude,
      manualLongitude: manualLongitude,
    );
    _manualLatitudeController.text = result.latitude.toStringAsFixed(6);
    _manualLongitudeController.text = result.longitude.toStringAsFixed(6);
    return result;
  }

  void _runRisk() {
    setState(() {
      _future = _loadRisk();
    });
  }

  void _refreshData() {
    setState(() {
      _future = _loadRisk(refreshData: true);
    });
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 120),
      children: [
        const _AppHeader(
          title: 'Deprem Risk Paneli',
          subtitle:
              'Sehir bazli deprem risk analizi. Backend uzerinden CatBoost ML modeli ile hesaplanir.',
        ),
        const SizedBox(height: 18),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionTitle(
                title: 'Analiz Kontrolleri',
                subtitle:
                    'Sehir secimi, manuel koordinat ve veri yenileme ayarlari.',
              ),
              const SizedBox(height: 18),
              DropdownButtonFormField<String>(
                initialValue: widget.city,
                items: turkeyCities
                    .map(
                      (value) =>
                          DropdownMenuItem(value: value, child: Text(value)),
                    )
                    .toList(),
                onChanged: widget.onCityChanged,
                decoration: const InputDecoration(labelText: 'Sehir secin'),
              ),
              const SizedBox(height: 14),
              CheckboxListTile(
                value: _useManualCoordinates,
                onChanged: (value) {
                  setState(() {
                    _useManualCoordinates = value ?? false;
                  });
                },
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                title: const Text('Manuel koordinat kullan'),
                subtitle: const Text(
                  'Secili sehir yerine ozel koordinatlarla hesap yap.',
                ),
              ),
              if (_useManualCoordinates) ...[
                const SizedBox(height: 8),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final width = (constraints.maxWidth - 12) / 2;
                    final fieldWidth = width > 170
                        ? width
                        : constraints.maxWidth;
                    return Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        SizedBox(
                          width: fieldWidth,
                          child: TextField(
                            controller: _manualLatitudeController,
                            keyboardType: const TextInputType.numberWithOptions(
                              decimal: true,
                              signed: true,
                            ),
                            decoration: const InputDecoration(
                              labelText: 'Enlem',
                            ),
                          ),
                        ),
                        SizedBox(
                          width: fieldWidth,
                          child: TextField(
                            controller: _manualLongitudeController,
                            keyboardType: const TextInputType.numberWithOptions(
                              decimal: true,
                              signed: true,
                            ),
                            decoration: const InputDecoration(
                              labelText: 'Boylam',
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 14),
              ],
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: _refreshData,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Veriyi Guncelle'),
                  ),
                  FilledButton.icon(
                    onPressed: _runRisk,
                    icon: const Icon(Icons.public),
                    label: const Text('Deprem Riskini Hesapla'),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        FutureBuilder<RiskModuleResult>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return const _LoadingState(
                message: 'Risk motoru backend uzerinden hesaplama yapiyor...',
              );
            }

            if (snapshot.hasError || !snapshot.hasData) {
              return _ErrorState(
                title: '${widget.city} icin risk verisi alinamadi',
                error: snapshot.error?.toString() ?? 'Bilinmeyen hata',
                onRetry: _runRisk,
              );
            }

            final result = snapshot.data!;
            return Column(
              children: [
                LayoutBuilder(
                  builder: (context, constraints) {
                    final width = (constraints.maxWidth - 12) / 2;
                    final tileWidth = width > 170
                        ? width
                        : constraints.maxWidth;
                    return Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        SizedBox(
                          width: tileWidth,
                          child: MetricTile(
                            label: 'Risk skoru',
                            value: result.riskScore.toStringAsFixed(1),
                            color: const Color(0xFFE15B64),
                          ),
                        ),
                        SizedBox(
                          width: tileWidth,
                          child: MetricTile(
                            label: 'Risk seviyesi',
                            value: result.riskLevel,
                            color: const Color(0xFFB24C63),
                          ),
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 12),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final width = (constraints.maxWidth - 12) / 2;
                    final tileWidth = width > 170
                        ? width
                        : constraints.maxWidth;
                    return Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        SizedBox(
                          width: tileWidth,
                          child: MetricTile(
                            label: 'Son guncelleme',
                            value: result.lastUpdate,
                            color: const Color(0xFF15616D),
                          ),
                        ),
                        SizedBox(
                          width: tileWidth,
                          child: MetricTile(
                            label: result.usedManualCoordinates
                                ? 'Manuel koordinat'
                                : 'Koordinat',
                            value:
                                '${result.latitude.toStringAsFixed(2)} / ${result.longitude.toStringAsFixed(2)}',
                            color: const Color(0xFF5A6C7D),
                          ),
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 18),
                if (result.refreshMessage.isNotEmpty) ...[
                  SectionCard(
                    color: AppTheme.panelHigh,
                    child: Text(result.refreshMessage),
                  ),
                  const SizedBox(height: 18),
                ],
                Align(
                  alignment: Alignment.centerLeft,
                  child: FilledButton.icon(
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute<void>(
                          builder: (_) =>
                              _RiskMapFullScreenPage(result: result),
                        ),
                      );
                    },
                    icon: const Icon(Icons.open_in_full),
                    label: const Text('Haritada Incele'),
                  ),
                ),
                const SizedBox(height: 18),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    SizedBox(
                      width: 180,
                      child: MetricTile(
                        label: '150 km deprem',
                        value: '${result.nearbyQuakeCount}',
                        color: const Color(0xFFE15B64),
                      ),
                    ),
                    SizedBox(
                      width: 180,
                      child: MetricTile(
                        label: 'Max buyukluk',
                        value: result.maxMagnitude.toStringAsFixed(2),
                        color: const Color(0xFF15616D),
                      ),
                    ),
                    SizedBox(
                      width: 180,
                      child: MetricTile(
                        label: 'Isi orneklemi',
                        value: '${result.heatSampleCount}',
                        color: const Color(0xFF5A6C7D),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Risk faktorleri',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 14),
                      ...result.factors.entries.map(
                        (entry) => Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      entry.key,
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text('%${(entry.value * 100).round()}'),
                                ],
                              ),
                              const SizedBox(height: 8),
                              ClipRRect(
                                borderRadius: BorderRadius.circular(99),
                                child: LinearProgressIndicator(
                                  minHeight: 10,
                                  value: entry.value,
                                  backgroundColor: AppTheme.mist,
                                  color: entry.value > 0.75
                                      ? const Color(0xFFE15B64)
                                      : AppTheme.teal,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const Divider(height: 32),
                      Text(
                        'Motor ozeti',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 10),
                      Text(result.summary.replaceAll('\n', '\n\n')),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Yakin faylar',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 12),
                      ...result.nearbyFaults.map(
                        (fault) => ListTile(
                          leading: const Icon(
                            Icons.timeline,
                            color: AppTheme.accent,
                          ),
                          title: Text(fault),
                          subtitle: Text(
                            '${result.city} merkezine gore siralandi',
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Yakin olaylar',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 12),
                      if (result.recentEvents.isEmpty)
                        const Text('Bu alan icin son deprem kaydi bulunamadi.'),
                      ...result.recentEvents.map(
                        (event) => ListTile(
                          leading: const Icon(
                            Icons.warning_amber_rounded,
                            color: Color(0xFFE15B64),
                          ),
                          title: Text(event),
                          subtitle: const Text(
                            '150 km icindeki en yeni kayitlardan',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ],
    );
  }
}

class _RiskMapFullScreenPage extends StatelessWidget {
  const _RiskMapFullScreenPage({required this.result});

  final RiskModuleResult result;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Risk Haritasi')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
          child: RiskMapPanel(
            title: 'Fay ve olay katmani',
            city: result.city,
            result: result,
            showHeatmapMode: false,
            height: MediaQuery.of(context).size.height - 70,
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Road Damage Page
// ---------------------------------------------------------------------------

class _RoadDamagePage extends StatefulWidget {
  const _RoadDamagePage({
    required this.city,
    required this.source,
    required this.damageBooster,
    required this.threshold,
    required this.useImagenetNorm,
    required this.postProcessLevel,
    required this.onCityChanged,
    required this.onSourceChanged,
    required this.onDamageBoosterChanged,
    required this.onThresholdChanged,
    required this.onNormalizationChanged,
    required this.onPostProcessChanged,
  });

  final String city;
  final String source;
  final double damageBooster;
  final double threshold;
  final bool useImagenetNorm;
  final int postProcessLevel;
  final ValueChanged<String?> onCityChanged;
  final ValueChanged<String?> onSourceChanged;
  final ValueChanged<double> onDamageBoosterChanged;
  final ValueChanged<double> onThresholdChanged;
  final ValueChanged<bool> onNormalizationChanged;
  final ValueChanged<int> onPostProcessChanged;

  @override
  State<_RoadDamagePage> createState() => _RoadDamagePageState();
}

enum _RoadLocationMode { current, sample }

class _RoadDamagePageState extends State<_RoadDamagePage> {
  static const _service = RoadDamageService();
  static const _oamSampleTitle = '2023-02-09T17:00:00.000Z - Help.NGO';

  Future<RoadDamageResult>? _future;
  _RoadLocationMode _locationMode = _RoadLocationMode.sample;
  double? _currentLatitude;
  double? _currentLongitude;
  String? _locationError;

  Future<void> _runAnalysis() async {
    double latitude;
    double longitude;
    String cityLabel;

    if (_locationMode == _RoadLocationMode.current) {
      final coords = await _resolveCurrentCoordinates();
      if (coords == null) {
        setState(() {
          _future = Future.error(
            _locationError ??
                'Mevcut konum alinamadi. Ornek uydu seti moduna gecip tekrar deneyin.',
          );
        });
        return;
      }
      latitude = coords[0];
      longitude = coords[1];
      cityLabel = 'Mevcut Konum';
    } else {
      final coords = _cityCoordinates(widget.city);
      latitude = coords[0];
      longitude = coords[1];
      cityLabel = widget.city;
    }

    setState(() {
      _future = _service.analyzeArea(
        city: cityLabel,
        latitude: latitude,
        longitude: longitude,
        source: widget.source,
        oamPreferredTitle:
            _locationMode == _RoadLocationMode.sample &&
                widget.source.toLowerCase().contains('openaerial')
            ? _oamSampleTitle
            : null,
        damageBooster: widget.damageBooster,
        threshold: widget.threshold,
        useImagenetNorm: widget.useImagenetNorm,
        postProcessLevel: widget.postProcessLevel,
      );
    });
  }

  List<double> _cityCoordinates(String city) {
    const coords = {
      'Antakya (Hatay)': [36.20, 36.16],
      'Kahramanmaras': [37.57, 36.93],
      'Gaziantep': [37.06, 37.38],
      'Malatya': [38.35, 38.30],
      'Adiyaman': [37.76, 38.27],
    };
    return coords[city] ?? [37.0, 37.0];
  }

  Future<List<double>?> _resolveCurrentCoordinates() async {
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() => _locationError = 'Konum servisi kapali.');
        return null;
      }

      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        setState(() => _locationError = 'Konum izni verilmedi.');
        return null;
      }

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
        ),
      );
      _locationError = null;
      _currentLatitude = position.latitude;
      _currentLongitude = position.longitude;
      return [position.latitude, position.longitude];
    } catch (e) {
      setState(() => _locationError = 'Konum alinirken hata: $e');
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 120),
      children: [
        const _AppHeader(
          title: 'Uydu Yol Hasari Analizi',
          subtitle:
              'Segformer AI modeli ile uydu goruntusunden yol hasari tespiti. Backend uzerinden calisir.',
        ),
        const SizedBox(height: 18),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionTitle(
                title: 'Konum ve veri kaynagi',
                subtitle:
                    'Analiz edilecek sehri ve uydu goruntu kaynagini secin.',
              ),
              const SizedBox(height: 18),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: SegmentedButton<_RoadLocationMode>(
                  segments: const [
                    ButtonSegment(
                      value: _RoadLocationMode.current,
                      label: Text('Bulundugum Konum'),
                      icon: Icon(Icons.my_location),
                    ),
                    ButtonSegment(
                      value: _RoadLocationMode.sample,
                      label: Text('Ornek Uydu Seti'),
                      icon: Icon(Icons.layers),
                    ),
                  ],
                  selected: {_locationMode},
                  onSelectionChanged: (value) {
                    setState(() {
                      _locationMode = value.first;
                    });
                  },
                ),
              ),
              const SizedBox(height: 12),
              if (_locationMode == _RoadLocationMode.current) ...[
                OutlinedButton.icon(
                  onPressed: () async {
                    await _resolveCurrentCoordinates();
                    if (mounted) setState(() {});
                  },
                  icon: const Icon(Icons.gps_fixed),
                  label: const Text('Konumu Al / Yenile'),
                ),
                const SizedBox(height: 10),
                Text(
                  _currentLatitude != null && _currentLongitude != null
                      ? 'Aktif koordinat: ${_currentLatitude!.toStringAsFixed(5)}, ${_currentLongitude!.toStringAsFixed(5)}'
                      : (_locationError ?? 'Konum alinmadi.'),
                ),
                const SizedBox(height: 10),
              ] else ...[
                DropdownButtonFormField<String>(
                  initialValue: widget.city,
                  items: roadCities
                      .map(
                        (value) =>
                            DropdownMenuItem(value: value, child: Text(value)),
                      )
                      .toList(),
                  onChanged: widget.onCityChanged,
                  decoration: const InputDecoration(
                    labelText: 'Ornek bolge secin',
                  ),
                ),
                const SizedBox(height: 12),
              ],
              DropdownButtonFormField<String>(
                initialValue: widget.source,
                items: const [
                  DropdownMenuItem(
                    value: 'Google Maps',
                    child: Text('Google Maps (Latest / High Res)'),
                  ),
                  DropdownMenuItem(
                    value: 'OpenAerialMap',
                    child: Text('OpenAerialMap (Event Specific)'),
                  ),
                  DropdownMenuItem(
                    value: 'Esri Wayback',
                    child: Text('Esri Wayback (Historical)'),
                  ),
                ],
                onChanged: widget.onSourceChanged,
                decoration: const InputDecoration(labelText: 'Uydu kaynagi'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Analiz ayarlari',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 18),
              Text(
                'Hasar hassasiyeti: ${widget.damageBooster.toStringAsFixed(1)}',
              ),
              Slider(
                value: widget.damageBooster,
                min: 1,
                max: 10,
                divisions: 18,
                onChanged: widget.onDamageBoosterChanged,
              ),
              Text('Tespit esigi: ${widget.threshold.toStringAsFixed(2)}'),
              Slider(
                value: widget.threshold,
                min: 0.05,
                max: 0.95,
                divisions: 18,
                onChanged: widget.onThresholdChanged,
              ),
              SwitchListTile.adaptive(
                value: widget.useImagenetNorm,
                onChanged: widget.onNormalizationChanged,
                contentPadding: EdgeInsets.zero,
                title: const Text('ImageNet normalizasyonu'),
                subtitle: const Text(
                  'Modelin egitim formatina uygun preprocess',
                ),
              ),
              const SizedBox(height: 12),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: SegmentedButton<int>(
                  segments: const [
                    ButtonSegment(value: 0, label: Text('Kapali')),
                    ButtonSegment(value: 1, label: Text('Hafif')),
                    ButtonSegment(value: 2, label: Text('Guclu')),
                  ],
                  selected: {widget.postProcessLevel},
                  onSelectionChanged: (value) =>
                      widget.onPostProcessChanged(value.first),
                ),
              ),
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: () => _runAnalysis(),
                  icon: const Icon(Icons.satellite_alt),
                  label: const Text('Analizi Baslat'),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        if (_future == null)
          const _RoadDamageIdleState()
        else
          FutureBuilder<RoadDamageResult>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const _LoadingState(
                  message:
                      'Uydu goruntusu indiriliyor ve AI modeli calisiyor... Bu islem 1-2 dakika surebilir.',
                );
              }

              if (snapshot.hasError || !snapshot.hasData) {
                return _ErrorState(
                  title: 'Yol hasari analizi tamamlanamadi',
                  error: snapshot.error?.toString() ?? 'Bilinmeyen hata',
                  onRetry: () => _runAnalysis(),
                );
              }

              final result = snapshot.data!;
              return _RoadDamageResultView(result: result);
            },
          ),
      ],
    );
  }
}

class _RoadDamageIdleState extends StatelessWidget {
  const _RoadDamageIdleState();

  @override
  Widget build(BuildContext context) {
    return const SectionCard(
      child: Column(
        children: [
          Icon(Icons.satellite_alt, size: 38, color: AppTheme.teal),
          SizedBox(height: 14),
          Text(
            'Ayarlari yapip "Analizi Baslat" butonuna bastiginizda backend uzerinden uydu goruntusu indirilecek, Segformer AI modeli ile hasar tespiti yapilacak ve sonuclar burada gosterilecek.',
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _RoadDamageResultView extends StatelessWidget {
  const _RoadDamageResultView({required this.result});

  final RoadDamageResult result;

  void _showAnalysisSteps(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(18, 8, 18, 18),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Analiz Adimlari',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 10),
                Flexible(
                  child: ListView(
                    shrinkWrap: true,
                    children: [
                      ...result.logLines.map(
                        (line) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: const Icon(
                            Icons.task_alt,
                            color: AppTheme.teal,
                          ),
                          title: Text(line),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            SizedBox(
              width: 180,
              child: MetricTile(
                label: 'Hasar orani',
                value: '%${(result.damageRate * 100).toStringAsFixed(1)}',
                color: const Color(0xFFE15B64),
              ),
            ),
            SizedBox(
              width: 180,
              child: MetricTile(
                label: 'Kapali yol',
                value: '${result.blockedRoads}',
                color: const Color(0xFF9C3D54),
              ),
            ),
            SizedBox(
              width: 180,
              child: MetricTile(
                label: 'Acik yol',
                value: '${result.openRoads}',
                color: AppTheme.teal,
              ),
            ),
          ],
        ),
        const SizedBox(height: 18),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Analiz gunlugu',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 12),
              const Text(
                'Adim detaylari ve teknik sureler "Adimlari Goster" butonunda acilir.',
              ),
              const Divider(height: 32),
              Text(
                'Onerilen aksiyon',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 10),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppTheme.panelHigh,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Text(
                  result.recommendedAction,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  OutlinedButton.icon(
                    onPressed: () => _showAnalysisSteps(context),
                    icon: const Icon(Icons.format_list_numbered),
                    label: const Text('Adimlari Goster'),
                  ),
                  if (result.timingsMs['total'] != null)
                    StatusPill(
                      label:
                          'Toplam sure: ${(result.timingsMs['total']! / 1000).toStringAsFixed(1)} sn',
                      color: const Color(0xFF3276E8),
                    ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        RoadLogisticsMapPanel(
          title: 'Lojistik Cizim Katmani',
          result: result,
          height: 500,
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// NLP Page
// ---------------------------------------------------------------------------

class _NlpPage extends StatefulWidget {
  const _NlpPage({required this.sample, required this.onSampleChanged});

  final String sample;
  final ValueChanged<String?> onSampleChanged;

  @override
  State<_NlpPage> createState() => _NlpPageState();
}

class _NlpPageState extends State<_NlpPage> {
  static const _service = NlpModuleService();

  late final TextEditingController _controller;
  Future<NlpModuleResult>? _future;
  final List<NlpCoordinates> _locationHistory = [];

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.sample);
  }

  @override
  void didUpdateWidget(covariant _NlpPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sample != widget.sample &&
        _controller.text != widget.sample) {
      _controller.text = widget.sample;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 120),
      children: [
        const _AppHeader(
          title: 'Afet NLP Analizi',
          subtitle:
              'BERTurk siniflandirma, NER ve geocoding ile afet metni analizi. Backend pipeline uzerinden calisir.',
        ),
        const SizedBox(height: 18),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionTitle(
                title: 'Metin girisi',
                subtitle: 'Ornek metinlerden secin veya serbest metin girin.',
              ),
              const SizedBox(height: 18),
              DropdownButtonFormField<String>(
                initialValue: widget.sample,
                items: nlpSamples
                    .map(
                      (value) => DropdownMenuItem(
                        value: value,
                        child: Text(
                          value,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  widget.onSampleChanged(value);
                  if (value != null) {
                    _controller.text = value;
                  }
                },
                decoration: const InputDecoration(
                  labelText: 'Ornek test verisi',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _controller,
                minLines: 5,
                maxLines: 8,
                decoration: const InputDecoration(
                  labelText: 'Sosyal medya / saha metni',
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _runAnalysis,
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Analizi calistir'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        if (_future == null)
          const _NlpIdleState()
        else
          FutureBuilder<NlpModuleResult>(
            future: _future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const _LoadingState(
                  message: 'NLP pipeline backend uzerinden calisiyor...',
                );
              }

              if (snapshot.hasError || !snapshot.hasData) {
                return _ErrorState(
                  title: 'Afet NLP verisi alinamadi',
                  error: snapshot.error?.toString() ?? 'Bilinmeyen hata',
                  onRetry: _runAnalysis,
                );
              }

              final result = snapshot.data!;
              return Column(
                children: [
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final width = (constraints.maxWidth - 12) / 2;
                      final tileWidth = width > 170
                          ? width
                          : constraints.maxWidth;
                      return Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: [
                          SizedBox(
                            width: tileWidth,
                            child: MetricTile(
                              label: 'Kategori',
                              value: result.category,
                              color: const Color(0xFF0F9D7A),
                            ),
                          ),
                          SizedBox(
                            width: tileWidth,
                            child: MetricTile(
                              label: 'Guven',
                              value: '%${(result.confidence * 100).round()}',
                              color: const Color(0xFF3276E8),
                            ),
                          ),
                        ],
                      );
                    },
                  ),
                  const SizedBox(height: 12),
                  MetricTile(
                    label: 'P-5 Aciliyet',
                    value: '${result.urgency} / 5',
                    color: const Color(0xFFE15B64),
                  ),
                  const SizedBox(height: 18),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: FilledButton.icon(
                      onPressed: () {
                        final markers = _historyMarkers(result.coordinates);
                        Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) =>
                                _NlpMapFullScreenPage(markers: markers),
                          ),
                        );
                      },
                      icon: const Icon(Icons.map_outlined),
                      label: const Text('Haritada Incele'),
                    ),
                  ),
                  const SizedBox(height: 18),
                  SectionCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'JSON cikti',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 12),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppTheme.ink,
                            borderRadius: BorderRadius.circular(22),
                          ),
                          child: Text(
                            result.jsonPayload,
                            style: const TextStyle(
                              color: Color(0xFFF2F6FA),
                              fontFamily: 'monospace',
                              height: 1.5,
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Konum metni: ${result.locationText.isEmpty ? 'Cikarilamadi' : result.locationText}',
                        ),
                        if (result.coordinates case final coordinates?) ...[
                          const SizedBox(height: 10),
                          Text(
                            'Koordinat: ${coordinates.latitude.toStringAsFixed(4)}, ${coordinates.longitude.toStringAsFixed(4)}',
                          ),
                        ],
                        if (result.candidates.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: result.candidates
                                .map((item) => Chip(label: Text(item)))
                                .toList(),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              );
            },
          ),
      ],
    );
  }

  void _runAnalysis() {
    setState(() {
      _future = _analyze();
    });
  }

  Future<NlpModuleResult> _analyze() async {
    final text = _controller.text.trim();
    if (text.isEmpty) {
      throw Exception('Analiz edilecek bir metin gir.');
    }
    final result = await _service.analyzeText(text);
    final coordinate = result.coordinates;
    if (coordinate != null) {
      final alreadyExists = _locationHistory.any(
        (item) =>
            (item.latitude - coordinate.latitude).abs() < 0.00001 &&
            (item.longitude - coordinate.longitude).abs() < 0.00001,
      );
      if (!alreadyExists) {
        _locationHistory.add(coordinate);
        if (_locationHistory.length > 30) {
          _locationHistory.removeAt(0);
        }
      }
    }
    return result;
  }

  List<GeoMarkerData> _historyMarkers(NlpCoordinates? latest) {
    final markers = _locationHistory
        .map(
          (item) => GeoMarkerData(
            latitude: item.latitude,
            longitude: item.longitude,
            label:
                'NLP konum: ${item.latitude.toStringAsFixed(4)}, ${item.longitude.toStringAsFixed(4)}',
          ),
        )
        .toList();

    if (latest != null) {
      markers.add(
        GeoMarkerData(
          latitude: latest.latitude,
          longitude: latest.longitude,
          label:
              'Son analiz: ${latest.latitude.toStringAsFixed(4)}, ${latest.longitude.toStringAsFixed(4)}',
          highlight: true,
        ),
      );
    }
    return markers;
  }
}

class _NlpMapFullScreenPage extends StatelessWidget {
  const _NlpMapFullScreenPage({required this.markers});

  final List<GeoMarkerData> markers;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('NLP Konum Haritasi')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
          child: GeoPointsMapPanel(
            title: 'NER ve geocoding konum haritasi',
            subtitle: 'Analiz edilen metinlerden cikarilan konumlar',
            markers: markers,
            height: MediaQuery.of(context).size.height - 70,
          ),
        ),
      ),
    );
  }
}

class _NlpIdleState extends StatelessWidget {
  const _NlpIdleState();

  @override
  Widget build(BuildContext context) {
    return const SectionCard(
      child: Column(
        children: [
          Icon(Icons.text_snippet_outlined, size: 38, color: AppTheme.teal),
          SizedBox(height: 14),
          Text(
            'Metni gonderdiginde BERT siniflandirma, NER ve geocoding sonucu burada gosterilecek.',
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Camera Page
// ---------------------------------------------------------------------------

class _CameraPage extends StatefulWidget {
  const _CameraPage();

  @override
  State<_CameraPage> createState() => _CameraPageState();
}

class _CameraPageState extends State<_CameraPage> {
  String _cameraSource = 'Arka kamera';
  CameraDetectionMode _mode = CameraDetectionMode.debris;
  final List<CameraDetectionTick> _ticks = [];

  @override
  Widget build(BuildContext context) {
    final latest = _ticks.isNotEmpty ? _ticks.last : null;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 120),
      children: [
        const _AppHeader(
          title: 'Kamera Tespiti',
          subtitle:
              'Enkaz ve catlak tespiti, yerel TFLite modelleri ile cihazda calisir.',
        ),
        const SizedBox(height: 18),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionTitle(
                title: 'Kamera ve model durumu',
                subtitle:
                    'Algilama modunu sec ve canli model skorunu takip et.',
              ),
              const SizedBox(height: 18),
              DropdownButtonFormField<String>(
                initialValue: _cameraSource,
                items: const [
                  DropdownMenuItem(
                    value: 'Arka kamera',
                    child: Text('Arka kamera'),
                  ),
                  DropdownMenuItem(
                    value: 'On kamera',
                    child: Text('On kamera'),
                  ),
                ],
                onChanged: (value) {
                  if (value == null) return;
                  setState(() => _cameraSource = value);
                },
                decoration: const InputDecoration(labelText: 'Goruntu kaynagi'),
              ),
              const SizedBox(height: 12),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: SegmentedButton<CameraDetectionMode>(
                  segments: const [
                    ButtonSegment(
                      value: CameraDetectionMode.debris,
                      label: Text('Enkaz Tespiti'),
                      icon: Icon(Icons.apartment),
                    ),
                    ButtonSegment(
                      value: CameraDetectionMode.crack,
                      label: Text('Catlak Tespiti'),
                      icon: Icon(Icons.crisis_alert),
                    ),
                  ],
                  selected: {_mode},
                  onSelectionChanged: (value) {
                    setState(() => _mode = value.first);
                  },
                ),
              ),
              const SizedBox(height: 14),
              const Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  StatusPill(
                    label: 'assets/models/bina.tflite',
                    color: Color(0xFFE15B64),
                  ),
                  StatusPill(
                    label: 'assets/models/catlak.tflite',
                    color: Color(0xFFF59F00),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        Container(
          height: 280,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(30),
            gradient: const LinearGradient(
              colors: [Color(0xFF1B1E28), Color(0xFF2B4257)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Stack(
            children: [
              Positioned.fill(
                child: LiveCameraView(
                  detectionMode: _mode,
                  preferFrontCamera: _cameraSource == 'On kamera',
                  onDetection: (tick) {
                    setState(() {
                      _ticks.add(tick);
                      if (_ticks.length > 30) {
                        _ticks.removeAt(0);
                      }
                    });
                  },
                ),
              ),
              const Positioned(
                left: 18,
                top: 18,
                child: StatusPill(
                  label: 'Canli Telefon Kamerasi',
                  color: Color(0xFF7CC6FE),
                ),
              ),
              Positioned(
                right: 18,
                top: 18,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withValues(alpha: 0.9),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Text(
                    'REC',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        LayoutBuilder(
          builder: (context, constraints) {
            final width = (constraints.maxWidth - 12) / 2;
            final tileWidth = width > 170 ? width : constraints.maxWidth;
            return Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(
                  width: tileWidth,
                  child: MetricTile(
                    label: 'Son guven skoru',
                    value: latest == null
                        ? '-'
                        : '%${(latest.confidence * 100).round()}',
                    color: const Color(0xFF7CC6FE),
                  ),
                ),
                SizedBox(
                  width: tileWidth,
                  child: MetricTile(
                    label: 'Toplam tespit sinyali',
                    value: '${_ticks.length}',
                    color: const Color(0xFFF59F00),
                  ),
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 18),
        SectionCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Tespit akisi',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 12),
              if (_ticks.isEmpty)
                const Text(
                  'HenUz tespit sinyali yok. Kamera goruntusunu hedefe dogrultun.',
                ),
              ..._ticks.reversed.take(10).map((item) {
                final severity = _severityFromConfidence(item.confidence);
                return ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(
                    backgroundColor: _severityColor(
                      severity,
                    ).withValues(alpha: 0.14),
                    foregroundColor: _severityColor(severity),
                    child: const Icon(Icons.center_focus_strong),
                  ),
                  title: Text(
                    item.mode == CameraDetectionMode.debris
                        ? 'Enkaz sinyali'
                        : 'Catlak sinyali',
                  ),
                  subtitle: Text(
                    '${_formatTime(item.detectedAt)}  |  Guven: %${(item.confidence * 100).round()}',
                  ),
                  trailing: StatusPill(
                    label: severity,
                    color: _severityColor(severity),
                  ),
                );
              }),
            ],
          ),
        ),
      ],
    );
  }

  static String _formatTime(DateTime dt) {
    final hh = dt.hour.toString().padLeft(2, '0');
    final mm = dt.minute.toString().padLeft(2, '0');
    final ss = dt.second.toString().padLeft(2, '0');
    return '$hh:$mm:$ss';
  }

  static String _severityFromConfidence(double confidence) {
    if (confidence >= 0.75) return 'Yuksek';
    if (confidence >= 0.50) return 'Orta';
    return 'Dusuk';
  }

  static Color _severityColor(String severity) {
    switch (severity) {
      case 'Yuksek':
        return const Color(0xFFE15B64);
      case 'Orta':
        return const Color(0xFFF59F00);
      default:
        return AppTheme.teal;
    }
  }
}

// ---------------------------------------------------------------------------
// Shared Widgets
// ---------------------------------------------------------------------------

class _AppHeader extends StatelessWidget {
  const _AppHeader({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.displaySmall),
        const SizedBox(height: 10),
        Text(subtitle, style: Theme.of(context).textTheme.bodyLarge),
      ],
    );
  }
}

class _LoadingState extends StatelessWidget {
  const _LoadingState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        children: [
          const SizedBox(height: 12),
          const CircularProgressIndicator(),
          const SizedBox(height: 18),
          Text(message, textAlign: TextAlign.center),
        ],
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({
    required this.title,
    required this.error,
    required this.onRetry,
  });

  final String title;
  final String error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final isConnectionError =
        error.contains('baglanilamadi') ||
        error.contains('TimeoutException') ||
        error.contains('SocketException') ||
        error.contains('Connection refused');

    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 10),
          Text(
            error.replaceFirst('Exception: ', ''),
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          if (isConnectionError) ...[
            const SizedBox(height: 14),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.panelHigh,
                borderRadius: BorderRadius.circular(18),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Baglanti kontrol listesi',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  SizedBox(height: 10),
                  Text(
                    '1. Bilgisayarda FastAPI sunucusunun calistigini kontrol et',
                  ),
                  SizedBox(height: 4),
                  Text('2. Telefon ve bilgisayar ayni agda (hotspot) mi?'),
                  SizedBox(height: 4),
                  Text(
                    '3. Panel > Sunucu Ayari\'ndan dogru IP:Port girildi mi?',
                  ),
                  SizedBox(height: 4),
                  Text(
                    '4. Bilgisayar guvenlik duvari 8000 portunu engelliyor olabilir',
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('Tekrar dene'),
          ),
        ],
      ),
    );
  }
}
