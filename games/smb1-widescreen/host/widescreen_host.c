/* Widescreen-only cycle host glue for Super Mario Bros.
 *
 * Derived from SuperMarioBrosNESRecomp's src/cycle_bridge.c and
 * src/cycle_extras.c (pinned at external/SuperMarioBrosNESRecomp), keeping
 * only what its widescreen renderer needs: the guest bridge, the NMI hook and
 * the host extras. Co-op, voxel and player-character mods are left out.
 * Copyright the SuperMarioBrosNESRecomp authors; PolyForm Noncommercial 1.0.0
 * (see external/SuperMarioBrosNESRecomp/LICENSE). Noncommercial use only.
 *
 * GAME_WIDESCREEN_DEFAULT (compile definition) turns the renderer on at power
 * on with that aspect ("16:9", "21:9", "32:9" or "fit"); "--widescreen off"
 * on the command line still restores the stock picture. */
#include "cycle_bridge.h"
#include "cyc_host_extras.h"
#include "cyc_ring.h"
#include "cyc_presentation.h"
#include "hw_internal.h"
#include "cpu6502.h"
#include "game_widescreen.h"
#include "smb_ws_actors.h"
#include "mod_runtime.h"
#include "nes_video.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#undef nes_mod_register_function_entry_plugin

#ifndef GAME_WIDESCREEN_DEFAULT
#define GAME_WIDESCREEN_DEFAULT "off"
#endif

/* ---- guest bridge (cycle_bridge.c) ---- */
CPU6502State smb1_cycle_cpu;
int g_ws_oam_sidecar, g_ws_obj_ctx_valid;
uint64_t g_frame_count;
static CycCompositorFn compositor_fn;
static void *compositor_user;
static SmbSpriteSuppress suppress_fn;
static void *suppress_user;
static const uint8_t *opaque;
static int opaque_width = 256, opaque_height = 240;

static void read_regs(void) {
    g_cpu.A = cpu.a; g_cpu.X = cpu.x; g_cpu.Y = cpu.y; g_cpu.S = cpu.s; g_cpu.P = cpu_get_p(0);
    g_cpu.C = cpu.c; g_cpu.Z = cpu.z; g_cpu.I = cpu.i; g_cpu.D = cpu.d; g_cpu.V = cpu.v; g_cpu.N = cpu.n;
}
static CycModRegs regs(void) {
    return (CycModRegs){g_cpu.A, g_cpu.X, g_cpu.Y, g_cpu.S,
        (uint8_t)(g_cpu.C | (g_cpu.Z << 1) | (g_cpu.I << 2) | (g_cpu.D << 3) | 0x20 | (g_cpu.V << 6) | (g_cpu.N << 7)), cpu.pc};
}
static void write_regs(void) { CycModRegs r = regs(); cyc_mod_set_regs(&r); }
void smb1_cycle_sync(void) { cyc_presentation_sync(); read_regs(); }
static void native_opaque(void) { opaque = NULL; opaque_width = 256; opaque_height = 240; }
uint8_t nes_read(uint16_t address) { return cyc_mod_peek(address); }
uint8_t mapper_peek_prg(uint16_t address) { return cyc_mod_peek(address); }
int mapper_get_mirroring(void) {
    switch (hw_cart.mirroring) { case 0: return 3; case 1: return 2; case 2: return 0; case 3: return 1; default: return 4; }
}
void runtime_begin_unclocked(void) {}
void runtime_end_unclocked(void) {}
int runtime_get_vblank_depth(void) { return 1; }
int call_by_address(uint16_t address) {
    CycModRegs r = regs();
    bool ok = cyc_mod_isolated() ? cyc_mod_call(address, &r) : cyc_mod_call_commit_hooked(address, &r);
    read_regs(); return ok;
}
void smb1_cycle_call(uint16_t address) {
    if (!call_by_address(address)) { fprintf(stderr, "[SMB1 cycle] guest call $%04x failed\n", address); abort(); }
}
typedef struct { NESModFunctionEntryCallback fn; uint16_t address; } Entry;
static Entry entries[96]; static unsigned entry_count;
static int hook(unsigned n, uint16_t address) {
    (void)address; read_regs(); int result = entries[n].fn(entries[n].address); write_regs(); return result;
}
#define HOOK(n) static int hook##n(uint16_t a) { return hook(n, a); }
#include "cycle_hook_wrappers.inc"
int smb1_cycle_register_hook(const char *id, uint16_t address, NESModFunctionEntryCallback fn) {
    if (entry_count >= 96) return 0; unsigned n = entry_count++;
    entries[n] = (Entry){fn, address}; return nes_mod_register_function_entry_plugin(id, address, callbacks[n]);
}
int ppu_renderer_background_opaque(int x, int y) {
    if (x < 0 || y < 0 || x >= opaque_width || y >= opaque_height) return 0;
    return opaque ? opaque[y * opaque_width + x] : cyc_frame_bg_opaque()[y * 256 + x];
}
void ppu_renderer_set_background_opaque_frame(const uint8_t *pixels, int width, int height) {
    opaque = pixels; opaque_width = width; opaque_height = height;
}
void ppu_renderer_set_sprite_suppress(SmbSpriteSuppress fn, void *user) { suppress_fn = fn; suppress_user = user; }
int ppu_renderer_sprite_suppressed(int slot, int x, int y) { return suppress_fn ? suppress_fn(slot, x, y, suppress_user) : 0; }
static int place_sprite(int slot, int x, int y, int *out_x, void *user) {
    (void)user; *out_x = x; return !ppu_renderer_sprite_suppressed(slot, x, y);
}
const uint32_t *smb1_cycle_native_picture(void) {
    static uint32_t filtered[256 * 240];
    const uint8_t *oam = cyc_render_oam(); bool any = false;
    for (int i = 0; i < 64; i++)
        if (oam[i * 4] < 239 && ppu_renderer_sprite_suppressed(i, oam[i * 4 + 3], oam[i * 4] + 1)) { any = true; break; }
    if (!any || !cyc_render_background(filtered)) return cyc_frame_argb();
    cyc_render_sprites(filtered, 256, 240, 0, cyc_frame_bg_opaque(), place_sprite, NULL);
    return filtered;
}
static int compositor(uint32_t *out, int w, int h, int x0, const uint32_t *native, void *user) {
    (void)user; (void)native; smb1_cycle_sync(); native_opaque();
    return compositor_fn ? compositor_fn(out, w, h, x0, smb1_cycle_native_picture(), compositor_user) : 0;
}
int ppu_renderer_set_custom_render(CycCompositorFn fn, void *user) {
    native_opaque(); compositor_fn = fn; compositor_user = user; cyc_render_set_compositor(fn ? compositor : NULL, NULL); return 1;
}
int ppu_renderer_custom_render_active(void) { return compositor_fn != NULL; }
void runtime_get_visible_frame_start(uint8_t *ctrl, uint8_t *x, uint8_t *y, void *a, void *b) {
    (void)a; (void)b;
    int scroll_x = cyc_render_line_scroll_x(32);
    if (ctrl) *ctrl = (uint8_t)((cyc_frame_lines()[32].ctrl & ~1u) | ((unsigned)scroll_x >> 8));
    if (x) *x = (uint8_t)scroll_x;
    if (y) *y = (uint8_t)(cyc_render_line_scroll_y(32) % 240);
}
static int nmi(uint16_t address) { (void)address; game_widescreen_begin_frame(); return 0; }
void smb1_cycle_init(void) {
    smb1_cycle_sync();
    if (!nes_mod_set_function_hook_enabled("smb.cycle.nmi", 1)) abort();
}
NES_MOD_CONSTRUCTOR(register_cycle_latch) { smb1_cycle_register_hook("smb.cycle.nmi", 0x8082, nmi); }

/* ---- host extras (cycle_extras.c) ---- */
static uint32_t picture[NES_MAX_RENDER_WIDTH * 240];
static bool default_applied;
static int suppress(int slot, int x, int y, void *user) { (void)x; (void)y; (void)user; return smb_ws_actors_suppress_sprite(slot); }
static void power_on(void *ctx) {
    (void)ctx; smb1_cycle_init(); cyc_render_capture_background(true); g_frame_count = 0;
    game_widescreen_init(); ppu_renderer_set_sprite_suppress(suppress, NULL);
    if (!default_applied) { default_applied = true; game_widescreen_arg("--widescreen", GAME_WIDESCREEN_DEFAULT); }
}
static void input(void *ctx, uint8_t buttons[2]) {
    (void)ctx; (void)buttons; smb1_cycle_sync(); g_frame_count = cyc_ring_frame;
}
static void frame_begin(void *ctx) { (void)ctx; smb1_cycle_sync(); g_frame_count = cyc_ring_frame; }
static void frame_end(void *ctx) { (void)ctx; smb1_cycle_sync(); g_frame_count = cyc_ring_frame; game_widescreen_update(); }
static const uint32_t *present(void *ctx, int *width, int *height) {
    (void)ctx; smb1_cycle_sync(); const uint32_t *source = cyc_render_present(width, height);
    if (*width == 256) source = smb1_cycle_native_picture();
    memcpy(picture, source, (size_t)*width * *height * sizeof(*picture));
    return picture;
}
static bool option(void *ctx, const char *key, const char *value) {
    (void)ctx;
    if (!strcmp(key, "--widescreen-hud") && strcmp(value, "edges") && strcmp(value, "center")) return false;
    if (!strcmp(key, "--widescreen-camera") && strcmp(value, "edges") && strcmp(value, "centered")) return false;
    if (!strcmp(key, "--widescreen-enemies") && strcmp(value, "viewport") && strcmp(value, "classic") && strcmp(value, "native")) return false;
    if (!strcmp(key, "--widescreen")) {
        NesAspectMode mode;
        if (strcmp(value, "off") && (!nes_video_aspect_from_name(value, &mode) || mode == NES_ASPECT_STOCK)) return false;
        default_applied = true;
    }
    return game_widescreen_arg(key, value) != 0;
}
void debug_server_send_fmt(const char *format, ...) { (void)format; }
static void state_loaded(void *ctx) { (void)ctx; smb1_cycle_sync(); }
const CycHostExtras *cyc_host_extras(void) {
    static const CycHostOption options[] = {
        {"--widescreen", true, "fit|16:9|21:9|32:9|off"}, {"--widescreen-hud", true, "edges|center"},
        {"--widescreen-enemies", true, "viewport|classic|native"}, {"--widescreen-camera", true, "edges|centered"},
    };
    static const CycHostExtras x = {.present = present, .power_on = power_on, .input = input,
        .frame_begin = frame_begin, .frame_end = frame_end, .options = options,
        .option_count = sizeof options / sizeof options[0], .option = option, .state_loaded = state_loaded};
    return &x;
}
