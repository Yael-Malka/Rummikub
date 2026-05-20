import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../game_engine/domain/entities/move.dart';
import '../../../game_engine/domain/move_steps_builder.dart';
import '../../domain/entities/game_state.dart';
import '../state/optimal_moves_state.dart';
import 'move_steps_list.dart';
import 'rack_view.dart';
import 'table_view.dart';

class OptimalMovesSection extends StatelessWidget {
  const OptimalMovesSection({
    required this.movesState,
    required this.stateBefore,
    super.key,
  });

  final OptimalMovesState movesState;
  final GameState stateBefore;

  @override
  Widget build(BuildContext context) {
    return switch (movesState) {
      OptimalMovesIdle() => const SizedBox.shrink(),
      OptimalMovesLoading() => const Padding(
          padding: EdgeInsets.symmetric(vertical: 16),
          child: Center(child: CircularProgressIndicator()),
        ),
      OptimalMovesError(:final message) => Padding(
          padding: const EdgeInsets.only(top: 16),
          child: Text(
            message,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        ),
      OptimalMovesLoaded(:final moves) => _LoadedMoves(
          moves: moves,
          stateBefore: stateBefore,
        ),
    };
  }
}

class _LoadedMoves extends StatelessWidget {
  const _LoadedMoves({
    required this.moves,
    required this.stateBefore,
  });

  final List<Move> moves;
  final GameState stateBefore;

  @override
  Widget build(BuildContext context) {
    final playable =
        moves.where((move) => move.tilesPlayedFromRack > 0).toList();

    if (playable.isEmpty) {
      return Padding(
        padding: const EdgeInsets.only(top: 16),
        child: Text(
          AppStrings.noOptimalMovesMessage,
          style: Theme.of(context).textTheme.titleMedium,
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 16),
        Text(
          AppStrings.optimalMovesTitle,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        ListView.separated(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: playable.length,
          separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (context, index) {
            return _MoveCard(
              move: playable[index],
              index: index + 1,
              stateBefore: stateBefore,
            );
          },
        ),
      ],
    );
  }
}

class _MoveCard extends StatelessWidget {
  const _MoveCard({
    required this.move,
    required this.index,
    required this.stateBefore,
  });

  final Move move;
  final int index;
  final GameState stateBefore;

  @override
  Widget build(BuildContext context) {
    final gameStateAfter = move.toGameState();
    final steps = MoveStepsBuilder.buildSteps(
      stateBefore: stateBefore,
      move: move,
    );

    return Card(
      child: ExpansionTile(
        initiallyExpanded: index == 1,
        title: Text(
          '${AppStrings.moveNumberLabel} $index — '
          '${move.tilesPlayedFromRack} ${AppStrings.tilesPlayedFromRackLabel}',
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                MoveStepsList(steps: steps),
                const SizedBox(height: 12),
                Text(
                  AppStrings.beforeTableTitle,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                TableView(melds: stateBefore.tableMelds),
                const SizedBox(height: 12),
                Text(
                  AppStrings.beforeRackTitle,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                RackView(tiles: stateBefore.rack),
                const Divider(height: 24),
                Text(
                  AppStrings.finalTableTitle,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                TableView(melds: gameStateAfter.tableMelds),
                const SizedBox(height: 12),
                Text(
                  AppStrings.finalRackTitle,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                RackView(tiles: gameStateAfter.rack),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
