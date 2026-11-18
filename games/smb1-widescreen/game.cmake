# Super Mario Bros. (World) with upstream's experimental widescreen renderer.
# Same cartridge as smb1; a separate NRO, launcher entry and SD folder.
set(GAME_TITLE "Super Mario Bros. Widescreen Recomp")
set(GAME_ARTIFACT SuperMarioBrosWidescreenRecomp)
set(GAME_ROM_CRC32 D445F698)
set(GAME_ROM_MAPPER 0)
set(GAME_REGION NTSC)
# Shares the smb1 SD folder (rom.nes); the NRO has its own name.
set(GAME_SD_DIR smb1)
set(smb "${GAME_REPO_ROOT}/external/SuperMarioBrosNESRecomp")
# The enhanced project's config adds the function-entry hook sites mods use.
set(GAME_CONFIG_FILE "${smb}/game-cycle.toml")
set(GAME_CYCLE_SEEDS "${smb}/cyc_seeds.txt")
set(GAME_BASELINE_PPU LLE)
set(GAME_OPTIMIZED_PPU FRAME)
# Mods: the mod runtime provides the function hooks; no package catalog is read.
set(GAME_MODS_ID super-mario-bros-world)
set(GAME_DESKTOP_SDL ON)
set(GAME_HOST_EXTRAS
    "${GAME_MODULE_DIR}/host/widescreen_host.c"
    "${smb}/src/cycle_calls.c"
    "${smb}/src/game_widescreen.c"
    "${smb}/src/smb_ws_world.c"
    "${smb}/src/smb_ws_actors.c"
    "${NESRECOMP_ROOT}/runner/cyc/cyc_presentation.c")
set(GAME_INCLUDE_DIRS "${smb}" "${smb}/src" "${NESRECOMP_ROOT}/runner/include")
set(GAME_DEFINITIONS SMB1_CYCLE NESRECOMP_CYCLE_PRESENTATION NESRECOMP_TRACE=0
    "GAME_WIDESCREEN_DEFAULT=\"16:9\"")
