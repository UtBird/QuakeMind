import 'package:flutter/material.dart';
import '../services/api_config.dart';

class IpConfigDialog extends StatefulWidget {
  const IpConfigDialog({super.key});

  @override
  State<IpConfigDialog> createState() => _IpConfigDialogState();
}

class _IpConfigDialogState extends State<IpConfigDialog> {
  final TextEditingController _controller = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadIp();
  }

  Future<void> _loadIp() async {
    final ip = await ApiConfig.getBackendIp();
    setState(() {
      _controller.text = ip;
    });
  }

  void _applyPreset(String ip) {
    _controller.text = ip;
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Sunucu Baglanti Ayari'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'FastAPI sunucusunun calistigi bilgisayarin IP adresi ve portunu girin.',
              style: TextStyle(fontSize: 13, color: Color(0xFF5A6C7D)),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: 'IP:Port',
                hintText: '10.42.0.1:8000',
              ),
              keyboardType: TextInputType.url,
            ),
            const SizedBox(height: 16),
            const Text(
              'Hizli secim (PC hotspot)',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _PresetChip(
                  label: 'Linux',
                  ip: '10.42.0.1:8000',
                  onTap: _applyPreset,
                ),
                _PresetChip(
                  label: 'Windows',
                  ip: '192.168.137.1:8000',
                  onTap: _applyPreset,
                ),
                _PresetChip(
                  label: 'Emulator',
                  ip: '10.0.2.2:8000',
                  onTap: _applyPreset,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFF8F3E7),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                'PC uzerinden hotspot acildiginda:\n'
                '  Linux  ->  10.42.0.1\n'
                '  Windows  ->  192.168.137.1\n\n'
                'Telefon bu hotspot\'a baglanir, uygulama yukardaki IP ile sunucuya erisir.',
                style: TextStyle(fontSize: 12, height: 1.5),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Iptal'),
        ),
        FilledButton(
          onPressed: () async {
            await ApiConfig.setBackendIp(_controller.text.trim());
            if (context.mounted) Navigator.of(context).pop();
          },
          child: const Text('Kaydet'),
        ),
      ],
    );
  }
}

class _PresetChip extends StatelessWidget {
  const _PresetChip({
    required this.label,
    required this.ip,
    required this.onTap,
  });

  final String label;
  final String ip;
  final ValueChanged<String> onTap;

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      label: Text('$label ($ip)'),
      onPressed: () => onTap(ip),
    );
  }
}
