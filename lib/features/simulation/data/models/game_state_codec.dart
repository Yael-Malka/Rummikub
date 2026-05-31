import '../../domain/entities/game_state.dart';
import '../../domain/entities/meld.dart';
import '../../domain/entities/meld_type.dart';
import '../../domain/entities/tile.dart';
import '../../domain/entities/tile_color.dart';
import '../../domain/entities/tile_id.dart';
import 'saved_session.dart';

/// JSON encoding for [GameState] persistence (no code generation).
abstract final class GameStateCodec {
  static Map<String, dynamic> encodeSession(SavedSession session) {
    return {
      'isFirstMeldTurn': session.isFirstMeldTurn,
      'emptyTable': session.emptyTable,
      'gameState': encodeState(session.gameState),
    };
  }

  static SavedSession? decodeSession(Map<String, dynamic> json) {
    final stateJson = json['gameState'];
    if (stateJson is! Map) {
      return null;
    }
    final gameState = decodeState(Map<String, dynamic>.from(stateJson));
    if (gameState == null) {
      return null;
    }
    return SavedSession(
      gameState: gameState,
      isFirstMeldTurn: json['isFirstMeldTurn'] == true,
      emptyTable: json['emptyTable'] == true,
    );
  }

  static Map<String, dynamic> encodeState(GameState state) {
    return {
      'rack': state.rack.map(_encodeTile).toList(),
      'tableMelds': state.tableMelds.map(_encodeMeld).toList(),
    };
  }

  static GameState? decodeState(Map<String, dynamic> json) {
    final rackJson = json['rack'];
    final meldsJson = json['tableMelds'];
    if (rackJson is! List || meldsJson is! List) {
      return null;
    }

    final rack = <Tile>[];
    for (final entry in rackJson) {
      final tile = _decodeTile(entry);
      if (tile == null) {
        return null;
      }
      rack.add(tile);
    }

    final melds = <Meld>[];
    for (final entry in meldsJson) {
      final meld = _decodeMeld(entry);
      if (meld == null) {
        return null;
      }
      melds.add(meld);
    }

    return GameState(rack: rack, tableMelds: melds);
  }

  static Map<String, dynamic> _encodeTile(Tile tile) {
    return switch (tile.id) {
      RegularTileId(:final color, :final number, :final copyIndex) => {
          'kind': 'regular',
          'color': color.name,
          'number': number,
          'copyIndex': copyIndex,
        },
      JokerTileId(:final copyIndex) => {
          'kind': 'joker',
          'copyIndex': copyIndex,
        },
    };
  }

  static Tile? _decodeTile(Object? json) {
    if (json is! Map) {
      return null;
    }
    final map = Map<String, dynamic>.from(json);
    final kind = map['kind'];
    if (kind == 'joker') {
      final copyIndex = map['copyIndex'];
      if (copyIndex is! int) {
        return null;
      }
      return Tile(id: JokerTileId(copyIndex: copyIndex));
    }
    if (kind == 'regular') {
      final colorName = map['color'];
      final number = map['number'];
      final copyIndex = map['copyIndex'];
      if (colorName is! String || number is! int || copyIndex is! int) {
        return null;
      }
      final color = _colorFromName(colorName);
      if (color == null) {
        return null;
      }
      return Tile(
        id: RegularTileId(
          color: color,
          number: number,
          copyIndex: copyIndex,
        ),
      );
    }
    return null;
  }

  static Map<String, dynamic> _encodeMeld(Meld meld) {
    return {
      'type': meld.type.name,
      'tiles': meld.tiles.map(_encodeTile).toList(),
    };
  }

  static Meld? _decodeMeld(Object? json) {
    if (json is! Map) {
      return null;
    }
    final map = Map<String, dynamic>.from(json);
    final typeName = map['type'];
    final tilesJson = map['tiles'];
    if (typeName is! String || tilesJson is! List) {
      return null;
    }
    final type = _meldTypeFromName(typeName);
    if (type == null) {
      return null;
    }
    final tiles = <Tile>[];
    for (final entry in tilesJson) {
      final tile = _decodeTile(entry);
      if (tile == null) {
        return null;
      }
      tiles.add(tile);
    }
    return Meld(type: type, tiles: tiles);
  }

  static TileColor? _colorFromName(String name) {
    return switch (name) {
      'red' => TileColor.red,
      'blue' => TileColor.blue,
      'black' => TileColor.black,
      'orange' => TileColor.orange,
      _ => null,
    };
  }

  static MeldType? _meldTypeFromName(String name) {
    return switch (name) {
      'group' => MeldType.group,
      'run' => MeldType.run,
      _ => null,
    };
  }
}
