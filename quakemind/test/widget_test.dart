import 'package:flutter_test/flutter_test.dart';

import 'package:quakemind/app.dart';

void main() {
  testWidgets('renders quake mind mobile shell', (WidgetTester tester) async {
    await tester.pumpWidget(const QuakeMindApp());
    await tester.pumpAndSettle();

    expect(find.text('QuakeMind Mobile'), findsOneWidget);
    expect(
      find.text('Tum moduller tek uygulama kabugunda hazir.'),
      findsOneWidget,
    );
    expect(find.text('Deprem Risk'), findsOneWidget);
    expect(find.text('Uydu Yol Hasari'), findsOneWidget);
  });
}
