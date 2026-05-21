import 'package:flutter/material.dart';

/// Hebrew-friendly text aligned to the visual right (start in RTL).
class RtlText extends StatelessWidget {
  const RtlText(
    this.data, {
    super.key,
    this.style,
    this.maxLines,
  });

  final String data;
  final TextStyle? style;
  final int? maxLines;

  @override
  Widget build(BuildContext context) {
    return Text(
      data,
      style: style,
      maxLines: maxLines,
      textAlign: TextAlign.start,
      textDirection: TextDirection.rtl,
    );
  }
}
