import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:rummikub_app/core/constants/app_strings.dart';
import 'package:rummikub_app/features/simulation/domain/entities/game_state.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld.dart';
import 'package:rummikub_app/features/simulation/domain/entities/meld_type.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/repositories/game_state_repository.dart';
import 'package:rummikub_app/features/game_engine/domain/usecases/find_optimal_moves_use_case.dart';
import 'package:rummikub_app/features/simulation/domain/usecases/generate_simulated_state_use_case.dart';
import 'package:rummikub_app/features/simulation/presentation/providers/simulation_view_model.dart';
import 'package:rummikub_app/features/simulation/presentation/screens/simulation_screen.dart';

import 'features/game_engine/domain/test_tiles.dart';

final class _WidgetTestRepository implements GameStateRepository {
  @override
  GameState generateSimulatedState() {
    return GameState(
      rack: [regularTile(TileColor.orange, 8)],
      tableMelds: [
        Meld(
          type: MeldType.group,
          tiles: [
            regularTile(TileColor.red, 8),
            regularTile(TileColor.blue, 8),
            regularTile(TileColor.black, 8),
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
          const FindOptimalMovesUseCase(),
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
          const FindOptimalMovesUseCase(),
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
    expect(find.text('8'), findsWidgets);
  });

  testWidgets('givenLoaded_whenShowOptimalMoves_thenShowsResults',
      (tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider<SimulationViewModel>(
        create: (_) => SimulationViewModel(
          GenerateSimulatedStateUseCase(_WidgetTestRepository()),
          const FindOptimalMovesUseCase(),
        ),
        child: const MaterialApp(
          home: SimulationScreen(),
        ),
      ),
    );

    await tester.tap(find.text(AppStrings.simulateButton));
    await tester.pumpAndSettle();

    await tester.tap(find.text(AppStrings.showOptimalMovesButton));
    await tester.pump();
    await tester.pumpAndSettle();

    expect(find.text(AppStrings.optimalMovesTitle), findsOneWidget);
  });
}
