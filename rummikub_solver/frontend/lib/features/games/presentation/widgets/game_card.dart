// One row in the games list.

import 'package:flutter/material.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../domain/game.dart';
import '../../data/games_provider.dart';

class GameCard extends ConsumerWidget {
  final Game game;

  const GameCard({super.key, required this.game});

  void _showDeleteConfirmation(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete Game?'),
        content: Text('Are you sure you want to delete "${game.name}"? This action cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancel', style: TextStyle(color: AppColors.ink500, fontFamily: 'Hanken Grotesk')),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(dialogContext).pop();
              ref.read(gamesProvider.notifier).deleteGame(game.id);
            },
            child: const Text('Delete', style: TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold, fontFamily: 'Hanken Grotesk')),
          ),
        ],
      ),
    );
  }


  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dateFormat = DateFormat('MMM d, yyyy');

    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppSpacing.radiusLg),
        side: const BorderSide(color: AppColors.borderDefault),
      ),
      color: AppColors.surfaceCard,
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.space3),
        child: Row(
          children: [
            // Felt Preview Box
            Container(
              width: 64,
              height: 56,
              decoration: BoxDecoration(
                color: AppColors.surfaceFelt,
                borderRadius: BorderRadius.circular(AppSpacing.radiusSm),
                border: Border.all(color: AppColors.borderFelt), // Simulates inset shadow
              ),
              alignment: Alignment.center,
              // Placeholder for tiles
              child: const Icon(Icons.style, color: AppColors.paper50, size: 24),
            ),
            const SizedBox(width: AppSpacing.space3),
            // Main content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    game.name,
                    style: const TextStyle(
                      fontFamily: 'Bricolage Grotesque',
                      fontSize: 18, // text-lg
                      fontWeight: FontWeight.w700,
                      color: AppColors.ink900,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    'Updated ${dateFormat.format(game.lastUpdated)}',
                    style: const TextStyle(
                      fontFamily: 'Hanken Grotesk',
                      fontSize: 13, // text-sm
                      color: AppColors.ink500,
                    ),
                  ),
                ],
              ),
            ),
            // Right side
            Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  height: 22,
                  padding: const EdgeInsets.symmetric(horizontal: 9),
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: AppColors.brandTint,
                    borderRadius: BorderRadius.circular(AppSpacing.radiusPill),
                  ),
                  child: const Text(
                    'In play',
                    style: TextStyle(
                      fontFamily: 'Hanken Grotesk',
                      fontSize: 12, // text-xs
                      fontWeight: FontWeight.w700,
                      color: AppColors.brandHover,
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                // Small actions (Delete)
                GestureDetector(
                  onTap: () => _showDeleteConfirmation(context, ref),
                  child: const Icon(Icons.delete_outline_rounded, color: AppColors.danger, size: 18),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
