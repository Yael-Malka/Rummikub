import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';

/// Initial simulation content — no business logic.
class SimulationBody extends StatelessWidget {
  const SimulationBody({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Text(
          AppStrings.welcomeMessage,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 16),
        ),
      ),
    );
  }
}
