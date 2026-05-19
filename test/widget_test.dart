import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:rummikub_app/core/constants/app_strings.dart';
import 'package:rummikub_app/features/simulation/presentation/providers/simulation_view_model.dart';
import 'package:rummikub_app/features/simulation/presentation/screens/simulation_screen.dart';

void main() {
  testWidgets('SimulationScreen shows welcome message', (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<SimulationViewModel>(
        create: (_) => SimulationViewModel(),
        child: const MaterialApp(
          home: SimulationScreen(),
        ),
      ),
    );

    expect(find.text(AppStrings.simulationScreenTitle), findsOneWidget);
    expect(find.text(AppStrings.welcomeMessage), findsOneWidget);
  });
}
