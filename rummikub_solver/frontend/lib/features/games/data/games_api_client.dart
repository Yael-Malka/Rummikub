// REST client for saved games.

import 'package:dio/dio.dart';
import '../domain/game.dart';

class GamesApiClient {
  final Dio _dio;

  GamesApiClient(this._dio);

  Future<List<Game>> getGames() async {
    final response = await _dio.get('play/games');
    return (response.data as List).map((json) => Game.fromJson(json)).toList();
  }

  Future<Game> createGame(String name, String? description) async {
    final response = await _dio.post('play/games', data: {
      'name': name,
      if (description != null) 'description': description,
    });
    return Game.fromJson(response.data);
  }

  Future<Game> shareGame(String gameId, bool isShared) async {
    final response = await _dio.patch('/play/games/$gameId/share', data: {
      'is_shared': isShared,
    });
    return Game.fromJson(response.data);
  }

  Future<void> deleteGame(String gameId) async {
    await _dio.delete('play/games/$gameId');
  }

  Future<Game> getPublicGame(String gameId) async {
    final response = await _dio.get('play/games/$gameId/public');
    return Game.fromJson(response.data);
  }
}
