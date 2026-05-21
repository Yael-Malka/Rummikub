import 'package:flutter/material.dart';

import '../../features/simulation/domain/entities/tile_color.dart';

/// Maps domain [TileColor] to display colors (presentation layer).
abstract final class TilePalette {
  static Color background(TileColor color) {
    return switch (color) {
      TileColor.red => const Color(0xFFC62828),
      TileColor.blue => const Color(0xFF1565C0),
      TileColor.black => const Color(0xFF212121),
      TileColor.orange => const Color(0xFFEF6C00),
      TileColor.joker => const Color(0xFF6A1B9A),
    };
  }

  static Color foreground(TileColor color) {
    return switch (color) {
      TileColor.black => Colors.white,
      _ => Colors.white,
    };
  }
}
