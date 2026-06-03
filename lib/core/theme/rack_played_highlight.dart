import 'package:flutter/material.dart';

/// Strong, theme-independent highlight for tiles played from the rack.
abstract final class RackPlayedHighlight {
  static const Color border = Color(0xFF000000);
  static const Color outerRing = Color(0xFFFFEB3B);
  static const double borderWidth = 4;
  static const double outerRingWidth = 2;
}
