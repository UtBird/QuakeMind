import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:quakemind/app.dart';

void main() {
  testWidgets('renders quake mind mobile shell', (WidgetTester tester) async {
    await tester.pumpWidget(const QuakeMindApp());
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('QuakeMind Mobile'), findsOneWidget);
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.text('Panel'), findsOneWidget);
  });
}
