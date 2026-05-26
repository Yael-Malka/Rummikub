import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:provider/provider.dart';

import 'core/constants/app_strings.dart';
import 'core/di/app_providers.dart';
import 'core/di/auth_providers.dart';
import 'core/firebase/firebase_bootstrap.dart';
import 'core/l10n/app_locale.dart';
import 'core/theme/app_theme.dart';
import 'core/widgets/auth_gate.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();
  await FirebaseBootstrap.initialize();
  runApp(const RummikubApp());
}

class RummikubApp extends StatelessWidget {
  const RummikubApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ...AuthProviders.providers,
        ...AppProviders.providers,
      ],
      child: MaterialApp(
        title: AppStrings.appTitle,
        locale: AppLocale.hebrew,
        supportedLocales: AppLocale.supportedLocales,
        localizationsDelegates: AppLocale.localizationsDelegates,
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: ThemeMode.system,
        home: const AuthGate(),
      ),
    );
  }
}
