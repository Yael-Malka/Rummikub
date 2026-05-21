import 'package:rummikub_app/features/simulation/domain/entities/tile.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_color.dart';
import 'package:rummikub_app/features/simulation/domain/entities/tile_id.dart';

Tile regularTile(
  TileColor color,
  int number, {
  int copyIndex = 0,
}) {
  return Tile(
    id: RegularTileId(
      color: color,
      number: number,
      copyIndex: copyIndex,
    ),
  );
}

Tile jokerTile({int copyIndex = 0}) {
  return Tile(id: JokerTileId(copyIndex: copyIndex));
}
