// Saved game model.

import 'package:freezed_annotation/freezed_annotation.dart';

part 'game.freezed.dart';
part 'game.g.dart';

@freezed
abstract class Game with _$Game {
  const factory Game({
    required String id,
    @JsonKey(name: 'user_id') required String userId,
    required String name,
    String? description,
    @JsonKey(name: 'is_shared') @Default(false) bool isShared,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @JsonKey(name: 'last_updated') required DateTime lastUpdated,
  }) = _Game;

  factory Game.fromJson(Map<String, dynamic> json) => _$GameFromJson(json);
}
