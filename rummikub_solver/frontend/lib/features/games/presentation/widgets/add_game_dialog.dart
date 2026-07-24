// Create a new saved game.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_spacing.dart';
import '../../data/games_provider.dart';

class AddGameDialog extends ConsumerStatefulWidget {
  const AddGameDialog({super.key});

  @override
  ConsumerState<AddGameDialog> createState() => _AddGameDialogState();
}

class _AddGameDialogState extends ConsumerState<AddGameDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {
      ref.read(gamesProvider.notifier).createGame(
        _nameController.text.trim(),
        _descController.text.trim().isEmpty ? null : _descController.text.trim(),
      );
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: AppColors.surfaceCard,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppSpacing.radius2xl)),
      title: const Text(
        'New game',
        style: TextStyle(
          fontFamily: 'Bricolage Grotesque',
          fontWeight: FontWeight.w700,
          letterSpacing: -0.015,
          color: AppColors.ink900,
        ),
      ),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextFormField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Game name',
                border: OutlineInputBorder(),
                labelStyle: TextStyle(fontFamily: 'Hanken Grotesk', color: AppColors.ink500),
              ),
              style: const TextStyle(fontFamily: 'Hanken Grotesk', color: AppColors.ink900),
              validator: (val) {
                if (val == null || val.trim().isEmpty) return 'Please enter a name';
                return null;
              },
            ),
            const SizedBox(height: AppSpacing.space4),
            TextFormField(
              controller: _descController,
              decoration: const InputDecoration(
                labelText: 'Description (optional)',
                labelStyle: TextStyle(fontFamily: 'Hanken Grotesk', color: AppColors.ink500),
              ),
              style: const TextStyle(fontFamily: 'Hanken Grotesk', color: AppColors.ink900),
              maxLines: 3,
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel', style: TextStyle(color: AppColors.ink500, fontFamily: 'Hanken Grotesk')),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.brand,
            foregroundColor: AppColors.onBrand,
            elevation: 0,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppSpacing.radiusPill)),
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space6, vertical: AppSpacing.space2),
          ),
          onPressed: _submit,
          child: const Text('Create', style: TextStyle(fontWeight: FontWeight.w600, fontFamily: 'Hanken Grotesk')),
        ),
      ],
    );
  }
}
