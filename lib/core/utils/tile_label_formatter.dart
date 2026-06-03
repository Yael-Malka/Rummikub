import '../../features/simulation/domain/entities/tile.dart';
import '../../features/simulation/domain/entities/tile_color.dart';
import '../constants/app_strings.dart';

/// Formats tiles for Hebrew UI labels.
abstract final class TileLabelFormatter {
  static String formatTile(Tile tile) {
    if (tile.isJoker) {
      return AppStrings.jokerTileName;
    }
    return formatTileLabel(tile.color!, tile.number!);
  }

  static String formatTileLabel(TileColor color, int number) {
    return '${_colorName(color)} $number';
  }

  static String formatTiles(Iterable<Tile> tiles) {
    return tiles.map(formatTile).join(', ');
  }

  static String _colorName(TileColor color) {
    return switch (color) {
      TileColor.red => AppStrings.colorRed,
      TileColor.blue => AppStrings.colorBlue,
      TileColor.black => AppStrings.colorBlack,
      TileColor.orange => AppStrings.colorOrange,
      TileColor.joker => AppStrings.jokerTileName,
    };
  }
}
