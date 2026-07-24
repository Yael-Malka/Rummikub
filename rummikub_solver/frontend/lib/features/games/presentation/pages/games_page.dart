// List of saved games.

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../data/games_provider.dart';
import '../widgets/game_card.dart';
import '../widgets/add_game_dialog.dart';

class GamesPage extends ConsumerWidget {
  const GamesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final gamesState = ref.watch(gamesProvider);

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
        title: const Text('Your games', style: TextStyle(fontFamily: 'Bricolage Grotesque', fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.ink900, letterSpacing: -0.015)),
        backgroundColor: AppColors.surfaceApp,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined, color: AppColors.ink900),
            onPressed: () {},
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(gamesProvider.notifier).refresh(),
        child: gamesState.when(
          loading: () => const Center(child: CircularProgressIndicator(color: AppColors.brand)),
          error: (err, stack) => Center(
            child: Text(
              'Oops! Something went wrong.\n$err',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.danger, fontFamily: 'Hanken Grotesk'),
            ),
          ),
          data: (games) {
            final content = [
              // Search Input
              Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.space3),
                child: TextField(
                  decoration: InputDecoration(
                    hintText: 'Search games',
                    hintStyle: const TextStyle(color: AppColors.ink500, fontFamily: 'Hanken Grotesk'),
                    prefixIcon: const Icon(Icons.search, color: AppColors.ink500),
                    filled: true,
                    fillColor: AppColors.surfaceCard,
                    contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 16),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(AppSpacing.radiusLg), borderSide: const BorderSide(color: AppColors.borderSubtle)),
                    enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(AppSpacing.radiusLg), borderSide: const BorderSide(color: AppColors.borderSubtle)),
                  ),
                  style: const TextStyle(fontFamily: 'Hanken Grotesk', color: AppColors.ink900),
                ),
              ),
              // Segmented Control
              Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.space3),
                child: Container(
                  height: 36,
                  decoration: BoxDecoration(
                    color: AppColors.surfaceCard,
                    borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
                    border: Border.all(color: AppColors.borderSubtle),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Container(
                          alignment: Alignment.center,
                          decoration: BoxDecoration(color: AppColors.surfaceSunken, borderRadius: BorderRadius.circular(AppSpacing.radiusLg - 1)),
                          child: const Text('All', style: TextStyle(fontFamily: 'Hanken Grotesk', fontWeight: FontWeight.w600, color: AppColors.ink900, fontSize: 13)),
                        ),
                      ),
                      Expanded(
                        child: Container(
                          alignment: Alignment.center,
                          child: const Text('In play', style: TextStyle(fontFamily: 'Hanken Grotesk', fontWeight: FontWeight.w600, color: AppColors.ink500, fontSize: 13)),
                        ),
                      ),
                      Expanded(
                        child: Container(
                          alignment: Alignment.center,
                          child: const Text('Ended', style: TextStyle(fontFamily: 'Hanken Grotesk', fontWeight: FontWeight.w600, color: AppColors.ink500, fontSize: 13)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (games.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: AppSpacing.space16),
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
                        "Tap the plus button to start a new game and find your best move.",
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
                )
              else
                ...games.map((game) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.space3),
                  child: GameCard(game: game),
                )),
            ];

            return ListView.builder(
              padding: const EdgeInsets.only(left: AppSpacing.space4, right: AppSpacing.space4, top: AppSpacing.space4, bottom: AppSpacing.space24),
              itemCount: content.length,
              itemBuilder: (context, index) => content[index],
            );
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppColors.brand,
        foregroundColor: AppColors.onBrand,
        elevation: 4,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppSpacing.radiusPill)),
        onPressed: () {
          showDialog(
            context: context,
            builder: (context) => const AddGameDialog(),
          );
        },
        child: const Icon(Icons.add),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.startFloat,
    );
  }
}
