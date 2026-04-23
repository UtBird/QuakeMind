import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:ultralytics_yolo/ultralytics_yolo.dart';

enum CameraDetectionMode { debris, crack }

class CameraDetectionTick {
  const CameraDetectionTick({
    required this.mode,
    required this.confidence,
    required this.detectedAt,
  });

  final CameraDetectionMode mode;
  final double confidence;
  final DateTime detectedAt;
}

class LiveCameraView extends StatefulWidget {
  const LiveCameraView({
    super.key,
    required this.detectionMode,
    required this.preferFrontCamera,
    this.onDetection,
  });

  final CameraDetectionMode detectionMode;
  final bool preferFrontCamera;
  final ValueChanged<CameraDetectionTick>? onDetection;

  @override
  State<LiveCameraView> createState() => _LiveCameraViewState();
}

class _LiveCameraViewState extends State<LiveCameraView> {
  final YOLOViewController _controller = YOLOViewController();

  String? _modelPath;
  String _error = '';
  double _lastConfidence = 0;
  double _lastFps = 0;
  bool _usingFrontCamera = false;
  bool _cameraSynced = false;
  DateTime _lastEmit = DateTime.fromMillisecondsSinceEpoch(0);

  @override
  void initState() {
    super.initState();
    _prepareModel();
  }

  @override
  void didUpdateWidget(covariant LiveCameraView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.detectionMode != widget.detectionMode) {
      _prepareModel();
      return;
    }

    if (oldWidget.preferFrontCamera != widget.preferFrontCamera) {
      _syncCameraFacing();
    }
  }

  Future<void> _prepareModel() async {
    final modelPath = widget.detectionMode == CameraDetectionMode.debris
        ? 'assets/models/bina.tflite'
        : 'assets/models/catlak.tflite';

    setState(() {
      _modelPath = null;
      _error = '';
      _lastConfidence = 0;
      _lastFps = 0;
      _cameraSynced = false;
    });

    final exists = await _assetExists(modelPath);
    if (!mounted) return;

    if (!exists) {
      setState(() {
        _error = 'Model bulunamadi: $modelPath';
      });
      return;
    }

    setState(() {
      _modelPath = modelPath;
    });
  }

  Future<bool> _assetExists(String assetPath) async {
    try {
      await rootBundle.load(assetPath);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> _syncCameraFacing() async {
    if (!mounted || _modelPath == null) return;

    final shouldUseFront = widget.preferFrontCamera;
    if (_usingFrontCamera == shouldUseFront) {
      _cameraSynced = true;
      return;
    }

    try {
      await _controller.switchCamera();
      if (!mounted) return;
      setState(() {
        _usingFrontCamera = shouldUseFront;
        _cameraSynced = true;
      });
    } catch (_) {
      // Camera may not be initialized yet; next result callback retries.
    }
  }

  void _onResults(List<YOLOResult> results) {
    if (!mounted) return;

    if (!_cameraSynced) {
      _syncCameraFacing();
    }

    final confidence = results.isEmpty
        ? 0.0
        : results.first.confidence.clamp(0.0, 1.0);

    setState(() {
      _lastConfidence = confidence;
    });

    final now = DateTime.now();
    if (now.difference(_lastEmit).inMilliseconds < 250) {
      return;
    }
    _lastEmit = now;

    widget.onDetection?.call(
      CameraDetectionTick(
        mode: widget.detectionMode,
        confidence: confidence,
        detectedAt: now,
      ),
    );
  }

  void _onMetrics(YOLOPerformanceMetrics metrics) {
    if (!mounted) return;
    setState(() {
      _lastFps = metrics.fps;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_error.isNotEmpty) {
      return Center(
        child: Text(_error, style: const TextStyle(color: Colors.redAccent)),
      );
    }

    if (_modelPath == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final modeLabel = widget.detectionMode == CameraDetectionMode.debris
        ? 'Enkaz Algilama'
        : 'Catlak Algilama';

    return ClipRRect(
      borderRadius: BorderRadius.circular(30),
      child: Stack(
        fit: StackFit.expand,
        children: [
          YOLOView(
            modelPath: _modelPath!,
            task: YOLOTask.detect,
            controller: _controller,
            cameraResolution: '720p',
            showNativeUI: false,
            onResult: _onResults,
            onPerformanceMetrics: _onMetrics,
          ),
          Positioned(
            left: 12,
            bottom: 12,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xCC0D1B2A),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '$modeLabel  |  Guven: %${(_lastConfidence * 100).round()}  |  FPS: ${_lastFps.toStringAsFixed(1)}',
                style: const TextStyle(
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
