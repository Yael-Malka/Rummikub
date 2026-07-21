// Light/dark Material themes.

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';
import 'app_spacing.dart';

class AppTheme {
  static ThemeData get lightTheme {
    final textTheme = GoogleFonts.hankenGroteskTextTheme().copyWith(
      displayLarge: GoogleFonts.bricolageGrotesque(
        color: AppColors.ink900,
        fontWeight: FontWeight.w700,
      ),
      displayMedium: GoogleFonts.bricolageGrotesque(
        color: AppColors.ink900,
        fontWeight: FontWeight.w700,
      ),
      displaySmall: GoogleFonts.bricolageGrotesque(
        color: AppColors.ink900,
        fontWeight: FontWeight.w700,
      ),
      headlineLarge: GoogleFonts.bricolageGrotesque(
        color: AppColors.ink900,
        fontWeight: FontWeight.w700,
      ),
      headlineMedium: GoogleFonts.bricolageGrotesque(
        color: AppColors.ink900,
        fontWeight: FontWeight.w700,
      ),
      headlineSmall: GoogleFonts.bricolageGrotesque(
        color: AppColors.ink900,
        fontWeight: FontWeight.w700,
      ),
      titleLarge: GoogleFonts.bricolageGrotesque(
        color: AppColors.ink900,
        fontWeight: FontWeight.w600,
      ),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.light(
        primary: AppColors.brand,
        onPrimary: AppColors.onBrand,
        surface: AppColors.surfaceApp,
        onSurface: AppColors.textPrimary,
        error: AppColors.danger,
        onError: AppColors.white,
      ),
      scaffoldBackgroundColor: AppColors.surfaceApp,
      textTheme: textTheme,
      
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.brand,
          foregroundColor: AppColors.onBrand,
          minimumSize: const Size.fromHeight(AppSpacing.tapTarget),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
          ),
          textStyle: GoogleFonts.hankenGrotesk(
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
          elevation: 0,
        ),
      ),
      
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.brand,
          side: const BorderSide(color: AppColors.brand, width: 1.5),
          minimumSize: const Size.fromHeight(AppSpacing.tapTarget),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
          ),
          textStyle: GoogleFonts.hankenGrotesk(
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
        ),
      ),
      
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surfaceCard,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space4,
          vertical: AppSpacing.space3,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
          borderSide: const BorderSide(color: AppColors.borderDefault),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
          borderSide: const BorderSide(color: AppColors.borderDefault),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
          borderSide: const BorderSide(color: AppColors.brand, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
          borderSide: const BorderSide(color: AppColors.danger),
        ),
        labelStyle: GoogleFonts.hankenGrotesk(color: AppColors.textSecondary),
        hintStyle: GoogleFonts.hankenGrotesk(color: AppColors.textTertiary),
      ),
      
      cardTheme: CardThemeData(
        color: AppColors.surfaceCard,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
          side: const BorderSide(color: AppColors.borderSubtle),
        ),
      ),
    );
  }
}
