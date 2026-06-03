import 'move.dart';

/// Outcome of an optimal-move search (moves + whether the time limit was hit).
final class OptimalMovesResult {
  const OptimalMovesResult({
    required this.moves,
    required this.searchTimedOut,
  });

  static const empty = OptimalMovesResult(
    moves: [],
    searchTimedOut: false,
  );

  final List<Move> moves;
  final bool searchTimedOut;
}
