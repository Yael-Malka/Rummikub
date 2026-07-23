// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'games_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, type=warning

@ProviderFor(gamesApiClient)
final gamesApiClientProvider = GamesApiClientProvider._();

final class GamesApiClientProvider
    extends $FunctionalProvider<GamesApiClient, GamesApiClient, GamesApiClient>
    with $Provider<GamesApiClient> {
  GamesApiClientProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'gamesApiClientProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$gamesApiClientHash();

  @$internal
  @override
  $ProviderElement<GamesApiClient> $createElement($ProviderPointer pointer) =>
      $ProviderElement(pointer);

  @override
  GamesApiClient create(Ref ref) {
    return gamesApiClient(ref);
  }

  /// {@macro riverpod.override_with_value}
  Override overrideWithValue(GamesApiClient value) {
    return $ProviderOverride(
      origin: this,
      providerOverride: $SyncValueProvider<GamesApiClient>(value),
    );
  }
}

String _$gamesApiClientHash() => r'0f21f1087c44a3cf999a27a134aa0260595ee75c';

@ProviderFor(GamesNotifier)
final gamesProvider = GamesNotifierProvider._();

final class GamesNotifierProvider
    extends $AsyncNotifierProvider<GamesNotifier, List<Game>> {
  GamesNotifierProvider._()
    : super(
        from: null,
        argument: null,
        retry: null,
        name: r'gamesProvider',
        isAutoDispose: true,
        dependencies: null,
        $allTransitiveDependencies: null,
      );

  @override
  String debugGetCreateSourceHash() => _$gamesNotifierHash();

  @$internal
  @override
  GamesNotifier create() => GamesNotifier();
}

String _$gamesNotifierHash() => r'772a5dd363013265695b82ada597b35d7a3b94b0';

abstract class _$GamesNotifier extends $AsyncNotifier<List<Game>> {
  FutureOr<List<Game>> build();
  @$mustCallSuper
  @override
  WhenComplete runBuild() {
    final ref = this.ref as $Ref<AsyncValue<List<Game>>, List<Game>>;
    final element =
        ref.element
            as $ClassProviderElement<
              AnyNotifier<AsyncValue<List<Game>>, List<Game>>,
              AsyncValue<List<Game>>,
              Object?,
              Object?
            >;
    return element.handleCreate(ref, build);
  }
}
