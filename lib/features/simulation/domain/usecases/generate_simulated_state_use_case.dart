import '../../../game_engine/domain/rules_validator.dart';
import '../entities/game_state.dart';
import '../exceptions/state_generation_exception.dart';
import '../repositories/game_state_repository.dart';

/// Generates a random valid rack + table state for simulation mode.
final class GenerateSimulatedStateUseCase {
  const GenerateSimulatedStateUseCase(this._repository);

  final GameStateRepository _repository;

  GameState call({bool emptyTable = false}) {
    final state = _repository.generateSimulatedState(emptyTable: emptyTable);
    final validation = RulesValidator.validateGameState(state);

    if (!validation.isValid) {
      throw StateGenerationException(
        validation.message ?? 'Invalid simulated state',
      );
    }

    return state;
  }
}
