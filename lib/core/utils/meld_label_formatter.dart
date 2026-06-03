import '../../features/game_engine/domain/entities/move_explanation.dart';
import '../../features/simulation/domain/entities/meld.dart';
import '../../features/simulation/domain/entities/meld_type.dart';
import '../constants/app_strings.dart';
import 'tile_label_formatter.dart';

/// Short Hebrew labels for melds in move explanations.
abstract final class MeldLabelFormatter {
  static String formatMeld(Meld meld, {List<JokerRole> jokerRoles = const []}) {
    final type = switch (meld.type) {
      MeldType.group => AppStrings.meldGroupLabel,
      MeldType.run => AppStrings.meldRunLabel,
    };
    final tiles = TileLabelFormatter.formatTiles(meld.tiles);
    final jokerHint = _jokerHint(meld, jokerRoles);
    if (jokerHint.isEmpty) {
      return '$type ($tiles)';
    }
    return '$type ($tiles) — $jokerHint';
  }

  static String _jokerHint(Meld meld, List<JokerRole> roles) {
    if (roles.isEmpty) {
      return '';
    }
    final parts = <String>[];
    for (final role in roles) {
      final color = role.standsInForColor;
      if (color != null) {
        parts.add(
          "${AppStrings.jokerTileName} = "
          '${TileLabelFormatter.formatTileLabel(color, role.standsInForNumber)}',
        );
      } else {
        parts.add(
          "${AppStrings.jokerTileName} = ${role.standsInForNumber}",
        );
      }
    }
    return parts.join('; ');
  }
}
