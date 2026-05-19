import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/constants/app_strings.dart';
import 'core/theme/app_theme.dart';
import 'features/simulation/presentation/providers/simulation_view_model.dart';
import 'features/simulation/presentation/screens/simulation_screen.dart';

void main() {
  runApp(const RummikubApp());
}

class RummikubApp extends StatelessWidget {
  const RummikubApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<SimulationViewModel>(
          create: (_) => SimulationViewModel(),
        ),
      ],
      child: MaterialApp(
        title: AppStrings.appTitle,
        theme: AppTheme.light,
        home: const SimulationScreen(),
      ),
    );
  }
}
