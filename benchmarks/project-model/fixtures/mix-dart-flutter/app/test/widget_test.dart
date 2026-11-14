import 'package:flutter_test/flutter_test.dart';
import 'package:shop_app/main.dart';

void main() {
  testWidgets('shows a price', (tester) async {
    await tester.pumpWidget(const ShopApp());
    expect(find.text('12.50'), findsOneWidget);
  });
}
