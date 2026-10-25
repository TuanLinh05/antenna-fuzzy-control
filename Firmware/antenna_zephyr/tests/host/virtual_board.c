/*
 * Virtual board: the firmware's line protocol and control core on
 * stdin/stdout. MATLAB starts it as a child process to test the PIL scripts
 * without hardware; the same scripts then talk to the STM32 over UART.
 * "Flash" is emulated in memory; read_raw returns the raw value of the last
 * PIL sample (or 0).
 */
#include <stdio.h>
#include <string.h>

#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

#include "antenna_core.h"
#include "link_proto.h"

static acore_params_t par, flash_par;
static int flash_valid;
static acore_t core;
static link_ctx_t lk;

static void vb_write(link_ctx_t *l, const char *text)
{
	(void)l;
	fputs(text, stdout);
	fflush(stdout);
}

static int vb_save(link_ctx_t *l)
{
	(void)l;
	flash_par = par;
	flash_valid = 1;
	return 0;
}

static int vb_load(link_ctx_t *l)
{
	(void)l;
	if (!flash_valid) {
		acore_params_default(&par);
		return -1;
	}
	par = flash_par;
	return 0;
}

static int vb_read_raw(link_ctx_t *l, uint16_t *raw)
{
	(void)l;
	*raw = 0;
	return 0;
}

static uint32_t vb_cycles(link_ctx_t *l)
{
	(void)l;
	return 0u;
}

static void vb_telemetry(link_ctx_t *l)
{
	char buf[160];

	if (link_format_telemetry(buf, sizeof(buf), l->core, l->core->tick * 10u, 0, 0, 0,
				  l->pil)) {
		vb_write(l, buf);
	}
}

int main(void)
{
	static const link_hooks_t hooks = {
		.write = vb_write,
		.save_params = vb_save,
		.load_params = vb_load,
		.read_raw = vb_read_raw,
		.cycles_now = vb_cycles,
		.telemetry = vb_telemetry,
	};
	char line[LINK_LINE_MAX + 8];

#ifdef _WIN32
	_setmode(_fileno(stdout), _O_BINARY);
	_setmode(_fileno(stdin), _O_BINARY);
#endif
	acore_params_default(&par);
	acore_init(&core, &par);
	link_init(&lk, &core, &par, &hooks, NULL);
	vb_write(&lk, "# virtual board ready\n");
	while (fgets(line, sizeof(line), stdin)) {
		size_t n = strlen(line);

		while (n && (line[n - 1] == '\n' || line[n - 1] == '\r')) {
			line[--n] = 0;
		}
		if (strcmp(line, "EXIT") == 0) {
			break;
		}
		link_handle_line(&lk, line);
	}
	return 0;
}
