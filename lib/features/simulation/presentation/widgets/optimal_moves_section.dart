import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../game_engine/domain/entities/move.dart';
import '../state/optimal_moves_state.dart';
import 'rack_view.dart';
import 'table_view.dart';

class OptimalMovesSection extends StatelessWidget {
  const OptimalMovesSection({
    required this.movesState,
    super.key,
  });

  final OptimalMovesState movesState;

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
      OptimalMovesLoaded(:final moves) => _LoadedMoves(moves: moves),
    };
  }
}

class _LoadedMoves extends StatelessWidget {
  const _LoadedMoves({required this.moves});

  final List<Move> moves;

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
        for (var index = 0; index < playable.length; index++)
          _MoveCard(move: playable[index], index: index + 1),
      ],
    );
  }
}

class _MoveCard extends StatelessWidget {
  const _MoveCard({required this.move, required this.index});

  final Move move;
  final int index;

  @override
  Widget build(BuildContext context) {
    final gameState = move.toGameState();

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              '${AppStrings.moveNumberLabel} $index — '
              '${move.tilesPlayedFromRack} ${AppStrings.tilesPlayedFromRackLabel}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Text(
              AppStrings.finalTableTitle,
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            TableView(melds: gameState.tableMelds),
            const SizedBox(height: 12),
            Text(
              AppStrings.finalRackTitle,
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            RackView(tiles: gameState.rack),
          ],
        ),
      ),
    );
  }
}
