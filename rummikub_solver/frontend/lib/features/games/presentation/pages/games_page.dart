// List of saved games.

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';

class GamesPage extends StatelessWidget {
  const GamesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surfaceApp,
      appBar: AppBar(
        leadingWidth: 60,
        leading: Padding(
          padding: const EdgeInsets.only(left: AppSpacing.space4),
          child: Center(
            child: SvgPicture.asset('assets/logos/logo-mark.svg', height: 30),
          ),
        ),
        title: const Text(
          'Your games',
          style: TextStyle(
            fontFamily: 'Bricolage Grotesque',
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: AppColors.ink900,
            letterSpacing: -0.015,
          ),
        ),
        backgroundColor: AppColors.surfaceApp,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
      ),
      body: const Center(
        child: Padding(
          padding: EdgeInsets.all(AppSpacing.space4),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.grid_view_rounded, size: 64, color: AppColors.ink300),
              SizedBox(height: AppSpacing.space6),
              Text(
                "Never miss your best move again.",
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                  fontFamily: 'Bricolage Grotesque',
                  color: AppColors.ink900,
                  letterSpacing: -0.015,
                ),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: AppSpacing.space3),
              Text(
                "Saved games will appear here.",
                style: TextStyle(
                  fontSize: 16,
                  fontFamily: 'Hanken Grotesk',
                  color: AppColors.ink500,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
