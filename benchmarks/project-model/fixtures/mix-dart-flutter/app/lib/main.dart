import 'package:flutter/material.dart';
import 'package:shop_core/shop_core.dart';

void main() => runApp(const ShopApp());

class ShopApp extends StatelessWidget {
  const ShopApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(home: Text(formatPrice(1250)));
  }
}
