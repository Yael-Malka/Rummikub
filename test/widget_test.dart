import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:rummikub_app/core/constants/app_strings.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/repositories/game_state_repository.dart';
import 'package:rummikub_app/features/simulation/domain/usecases/generate_simulated_state_use_case.dart';
import 'package:rummikub_app/features/simulation/presentation/providers/simulation_view_model.dart';
import 'package:rummikub_app/features/simulation/presentation/screens/simulation_screen.dart';

import 'features/game_engine/domain/test_tiles.dart';

final class _WidgetTestRepository implements GameStateRepository {
  @override
  GameState generateSimulatedState() {
    return GameState(
      rack: [
        regularTile(TileColor.red, 1),
        regularTile(TileColor.red, 2),
      ],
      tableMelds: [
        Meld(
          type: MeldType.group,
          tiles: [
            regularTile(TileColor.blue, 9),
            regularTile(TileColor.black, 9),
            regularTile(TileColor.orange, 9),
          ],
        ),
      ],
    );
  }
}

void main() {
  testWidgets('SimulationScreen shows welcome and simulate button', (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<SimulationViewModel>(
        create: (_) => SimulationViewModel(
          GenerateSimulatedStateUseCase(_WidgetTestRepository()),
        ),
        child: const MaterialApp(
          home: SimulationScreen(),
        ),
      ),
    );

    expect(find.text(AppStrings.simulationScreenTitle), findsOneWidget);
    expect(find.text(AppStrings.simulateButton), findsOneWidget);
  });

  testWidgets('givenSimulateTap_whenLoaded_thenShowsRackAndTable',
      (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<SimulationViewModel>(
        create: (_) => SimulationViewModel(
          GenerateSimulatedStateUseCase(_WidgetTestRepository()),
        ),
        child: const MaterialApp(
          home: SimulationScreen(),
        ),
      ),
    );

    await tester.tap(find.text(AppStrings.simulateButton));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(find.textContaining(AppStrings.rackTitle), findsOneWidget);
    expect(find.textContaining(AppStrings.tableTitle), findsOneWidget);
    expect(find.text('1'), findsOneWidget);
    expect(find.text('9'), findsWidgets);
  });
}
