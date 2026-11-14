import 'package:args/args.dart';
import 'package:shop_core/shop_core.dart';

void main(List<String> arguments) {
  final parser = ArgParser()..addOption('cents', defaultsTo: '100');
  final results = parser.parse(arguments);
  print(formatPrice(int.parse(results['cents'] as String)));
}
