import 'package:flutter/material.dart';

import 'screens/home_shell.dart';
import 'theme/app_theme.dart';

class QuakeMindApp extends StatelessWidget {
  const QuakeMindApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'QuakeMind Mobile',
      theme: AppTheme.theme,
      home: const HomeShell(),
    );
  }
}
