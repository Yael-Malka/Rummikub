import 'package:provider/provider.dart';
import 'package:provider/single_child_widget.dart';

import '../../features/simulation/data/repositories/game_state_repository_impl.dart';
import '../../features/simulation/domain/usecases/generate_simulated_state_use_case.dart';
import '../../features/simulation/presentation/providers/simulation_view_model.dart';

/// Root dependency injection for the app.
abstract final class AppProviders {
  static List<SingleChildWidget> get providers => [
        ChangeNotifierProvider<SimulationViewModel>(
          create: (_) => SimulationViewModel(
            GenerateSimulatedStateUseCase(
              GameStateRepositoryImpl(),
            ),
          ),
        ),
      ];
}
