// Boots the app with theme, router, and Riverpod.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_web_plugins/url_strategy.dart';
import 'core/theme/app_theme.dart';
import 'core/router/app_router.dart';

void main() {
  usePathUrlStrategy();
  runApp(const ProviderScope(child: RummikubAssistantApp()));
}

class RummikubAssistantApp extends ConsumerWidget {
  const RummikubAssistantApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'Rummikub Assistant',
      theme: AppTheme.lightTheme,
      routerConfig: router,
    );
  }
}
