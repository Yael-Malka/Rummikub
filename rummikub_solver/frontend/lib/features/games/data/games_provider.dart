// Riverpod providers for game list.

import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../../core/network/api_client.dart';
import '../domain/game.dart';
import 'games_api_client.dart';

part 'games_provider.g.dart';

@riverpod
GamesApiClient gamesApiClient(Ref ref) {
  return GamesApiClient(ref.watch(apiClientProvider));
}

@riverpod
class GamesNotifier extends _$GamesNotifier {
  @override
  FutureOr<List<Game>> build() async {
    return _fetchGames();
  }

  Future<List<Game>> _fetchGames() async {
    final client = ref.read(gamesApiClientProvider);
    return await client.getGames();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetchGames);
  }

  Future<void> createGame(String name, String? description) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final client = ref.read(gamesApiClientProvider);
      await client.createGame(name, description);
      return _fetchGames();
    });
  }

  Future<void> shareGame(String gameId, bool isShared) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final client = ref.read(gamesApiClientProvider);
      await client.shareGame(gameId, isShared);
      return _fetchGames();
    });
  }

  Future<void> deleteGame(String gameId) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final client = ref.read(gamesApiClientProvider);
      await client.deleteGame(gameId);
      return _fetchGames();
    });
  }
}
