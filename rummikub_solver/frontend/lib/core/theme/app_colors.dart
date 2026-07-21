// Brand color palette.

import 'package:flutter/material.dart';

class AppColors {
  // Paper / warm neutral surfaces
  static const Color paper50 = Color(0xFFFBF7EC);
  static const Color paper100 = Color(0xFFF6EFDE);
  static const Color paper200 = Color(0xFFEFE6CF);
  static const Color paper300 = Color(0xFFE4D7BB);
  static const Color ivory = Color(0xFFFCF9F0);

  // Ink / warm near-black text
  static const Color ink900 = Color(0xFF1C1B16);
  static const Color ink700 = Color(0xFF3B392F);
  static const Color ink500 = Color(0xFF6E6A5B);
  static const Color ink400 = Color(0x968E8978);
  static const Color ink300 = Color(0xFFABA590);

  // Felt green: BRAND / primary action
  static const Color felt900 = Color(0xFF0F3326);
  static const Color felt800 = Color(0xFF13402F);
  static const Color felt700 = Color(0xFF1A5740);
  static const Color felt600 = Color(0xFF1E6B4E);
  static const Color felt500 = Color(0xFF2A8763);
  static const Color felt300 = Color(0xFF8FC7AE);
  static const Color felt100 = Color(0xFFDCEDE3);

  // Classic tile colors (DATA only)
  static const Color tileRed = Color(0xFFCE3B2E);
  static const Color tileBlue = Color(0xFF1F6FB2);
  static const Color tileOrange = Color(0xFFE08A1E);
  static const Color tileBlack = Color(0xFF25241F);

  // Tints
  static const Color tileRedTint = Color(0xFFF6DCD7);
  static const Color tileBlueTint = Color(0xFFD8E7F3);
  static const Color tileOrangeTint = Color(0xFFF8E8CB);
  static const Color tileBlackTint = Color(0xFFDEDCD3);

  static const Color white = Color(0xFFFFFFFF);
  static const Color black = Color(0xFF000000);

  // Semantic Aliases
  static const Color surfaceApp = paper100;
  static const Color surfaceCard = paper50;
  static const Color surfaceRaised = white;
  static const Color surfaceSunken = paper200;
  static const Color surfaceFelt = felt700;
  static const Color surfaceTile = ivory;

  static const Color textPrimary = ink900;
  static const Color textSecondary = ink500;
  static const Color textTertiary = ink300;
  static const Color textOnFelt = paper50;
  static const Color textOnFeltDim = Color(0xFFA9C7B8);
  static const Color textOnPrimary = white;
  static const Color textLink = felt600;

  static const Color brand = felt600;
  static const Color brandHover = felt700;
  static const Color brandActive = felt800;
  static const Color brandTint = felt100;
  static const Color onBrand = white;

  static const Color borderSubtle = Color(0x1A1C1B16);
  static const Color borderDefault = Color(0x291C1B16);
  static const Color borderStrong = Color(0x471C1B16);
  static const Color borderFelt = Color(0x24FFFFFF);

  static const Color success = felt600;
  static const Color successTint = felt100;
  static const Color warning = Color(0xFFC8780F);
  static const Color warningTint = tileOrangeTint;
  static const Color danger = tileRed;
  static const Color dangerTint = tileRedTint;
  static const Color info = tileBlue;
  static const Color infoTint = tileBlueTint;
}
