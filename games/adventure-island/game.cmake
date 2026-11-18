# Adventure Island Classic (Europe), CNROM, PAL.
# The legacy iNES header leaves timing unspecified, so select PAL explicitly.
set(GAME_TITLE "Adventure Island Classic Recomp")
set(GAME_ARTIFACT AdventureIslandRecomp)
set(GAME_ROM_CRC32 86867830)
set(GAME_ROM_MAPPER 3)
set(GAME_REGION PAL)
set(GAME_CYCLE_SEEDS "${GAME_MODULE_DIR}/cyc_seeds.txt")
set(GAME_BASELINE_PPU LLE)
# FRAME on PAL CNROM needs mstan/nesrecomp#113 (open upstream PR).
set(GAME_OPTIMIZED_PPU FRAME)
