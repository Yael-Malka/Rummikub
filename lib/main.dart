import 'package:flutter/material.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:provider/provider.dart';

import 'core/constants/app_strings.dart';
import 'core/di/app_providers.dart';
import 'core/theme/app_theme.dart';
import 'features/simulation/presentation/screens/simulation_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();
  runApp(const RummikubApp());
}

class RummikubApp extends StatelessWidget {
  const RummikubApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: AppProviders.providers,
      child: MaterialApp(
        title: AppStrings.appTitle,
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: ThemeMode.system,
        home: const SimulationScreen(),
      ),
    );
  }
}
