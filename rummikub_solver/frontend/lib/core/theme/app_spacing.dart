// Shared padding and radius constants.

import 'package:flutter/material.dart';

class AppSpacing {
  // Spacing (based on 1rem = 16px)
  static const double space0 = 0.0;
  static const double space1 = 4.0;
  static const double space2 = 8.0;
  static const double space3 = 12.0;
  static const double space4 = 16.0;
  static const double space5 = 20.0;
  static const double space6 = 24.0;
  static const double space8 = 32.0;
  static const double space10 = 40.0;
  static const double space12 = 48.0;
  static const double space16 = 64.0;
  static const double space20 = 80.0;
  static const double space24 = 96.0;

  // Layout
  static const double gutter = space4;
  static const double gutterLg = space6;
  static const double contentMax = 480.0;
  static const double contentMaxWide = 1080.0;
  static const double tapTarget = 44.0;
  static const double bottomNavH = 64.0;
  static const double headerH = 56.0;

  // Radii
  static const double radiusXs = 4.0;
  static const double radiusSm = 8.0;
  static const double radiusMd = 12.0;
  static const double radiusLg = 16.0;
  static const double radiusXl = 22.0;
  static const double radius2xl = 28.0;
  static const double radiusTile = 9.0;
  static const double radiusPill = 999.0;

  // Shadows
  static const List<BoxShadow> shadowSm = [
    BoxShadow(color: Color(0x0F1C1B16), offset: Offset(0, 1), blurRadius: 2),
    BoxShadow(color: Color(0x121C1B16), offset: Offset(0, 2), blurRadius: 5),
  ];
}
