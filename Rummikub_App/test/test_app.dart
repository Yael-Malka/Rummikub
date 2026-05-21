import 'package:flutter/material.dart';
import 'package:rummikub_app/core/l10n/app_locale.dart';

/// Wraps a widget in [MaterialApp] with Hebrew RTL, for widget tests.
class TestApp extends StatelessWidget {
  const TestApp({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      locale: AppLocale.hebrew,
      supportedLocales: AppLocale.supportedLocales,
      localizationsDelegates: AppLocale.localizationsDelegates,
      home: child,
    );
  }
}
