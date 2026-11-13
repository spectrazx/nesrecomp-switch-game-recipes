# Title-owned identity, generation inputs and qualified build choices.
set(GAME_TITLE "Super Mario Bros. Recomp")
set(GAME_ARTIFACT SuperMarioBrosRecomp)
set(GAME_ROM_CRC32 D445F698)
set(GAME_ROM_MAPPER 0)
set(GAME_HARDWARE_PROFILE nrom-ntsc)
set(GAME_CYCLE_SEEDS "${NESRECOMP_SOURCES_ROOT}/SuperMarioBrosNESRecomp/cyc_seeds.txt")
set(GAME_BASELINE_PPU LLE)
set(GAME_OPTIMIZED_PPU HLE)
# No Mario-specific replacement code is needed by this build.
set(GAME_OPTIMIZATION_MODULES "")
