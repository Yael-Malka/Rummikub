import '../../domain/entities/game_state.dart';
import '../../domain/repositories/game_state_repository.dart';
import '../datasources/state_generator.dart';

final class GameStateRepositoryImpl implements GameStateRepository {
  GameStateRepositoryImpl({StateGenerator? generator})
      : _generator = generator ?? StateGenerator();

  final StateGenerator _generator;

  @override
  GameState generateSimulatedState({bool emptyTable = false}) =>
      _generator.generate(emptyTable: emptyTable);
}
