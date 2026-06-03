import 'package:flutter/material.dart';

import '../../../../core/constants/app_strings.dart';
import '../../../../core/widgets/computing_indicator.dart';
import '../../../../core/widgets/rtl_text.dart';
import '../../../game_engine/domain/entities/move.dart';
import '../../../game_engine/domain/move_explanation_builder.dart';
import '../../domain/entities/game_state.dart';
import '../state/optimal_moves_state.dart';
import 'before_move_snapshot.dart';
import 'move_explanation_panel.dart';

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
      OptimalMovesLoading() => const OptimalMovesComputingIndicator(),
      OptimalMovesError(:final message) => Padding(
          padding: const EdgeInsets.only(top: 16),
          child: RtlText(
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

/// One entry per visible end state (tiles on table + rack).
List<Move> _uniqueVisibleOutcomes(Iterable<Move> moves) {
  final seen = <String>{};
  final unique = <Move>[];
  for (final move in moves) {
    if (seen.add(move.visibleOutcomeKey)) {
      unique.add(move);
    }
  }
  return unique;
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
    final playable = _uniqueVisibleOutcomes(
      moves.where((move) => move.tilesPlayedFromRack > 0),
    );

    if (playable.isEmpty) {
      return Padding(
        padding: const EdgeInsets.only(top: 16),
        child: RtlText(
          AppStrings.noOptimalMovesMessage,
          style: Theme.of(context).textTheme.titleMedium,
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 16),
        RtlText(
          AppStrings.optimalMovesTitle,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        BeforeMoveSnapshot(stateBefore: stateBefore),
        const SizedBox(height: 16),
        RtlText(
          AppStrings.optimalMovesPickMoveHint,
          style: Theme.of(context).textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
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
    final explanation = MoveExplanationBuilder.build(
      stateBefore: stateBefore,
      move: move,
    );

    return Card(
      child: ExpansionTile(
        initiallyExpanded: index == 1,
        title: RtlText(
          '${AppStrings.moveNumberLabel} $index — '
          '${move.tilesPlayedFromRack} ${AppStrings.tilesPlayedFromRackLabel}',
        ),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
            child: MoveExplanationPanel(explanation: explanation),
          ),
        ],
      ),
    );
  }
}
