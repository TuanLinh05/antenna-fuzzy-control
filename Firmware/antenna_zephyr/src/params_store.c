/*
 * Parameters live in one NVS record with a version and a CRC-32. Writing
 * erases/programs internal flash, which stalls the CPU for tens of ms, so
 * the protocol only allows it while the azimuth is not moving.
 */
#include "params_store.h"

#include <stddef.h>
#include <string.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/fs/nvs.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/sys/crc.h>

#define PARAMS_ID 1

typedef struct {
	uint16_t version;
	uint16_t size;
	acore_params_t p;
	uint32_t crc;
} blob_t;

static struct nvs_fs fs;
static bool mounted;

int params_store_init(void)
{
	struct flash_pages_info info;
	int rc;

	fs.flash_device = FIXED_PARTITION_DEVICE(storage_partition);
	if (!device_is_ready(fs.flash_device)) {
		return -ENODEV;
	}
	fs.offset = FIXED_PARTITION_OFFSET(storage_partition);
	rc = flash_get_page_info_by_offs(fs.flash_device, fs.offset, &info);
	if (rc) {
		return rc;
	}
	fs.sector_size = (uint16_t)info.size;
	fs.sector_count = (uint16_t)(FIXED_PARTITION_SIZE(storage_partition) / info.size);
	rc = nvs_mount(&fs);
	mounted = (rc == 0);
	return rc;
}

static uint32_t blob_crc(const blob_t *b)
{
	return crc32_ieee((const uint8_t *)b, offsetof(blob_t, crc));
}

int params_store_load(acore_params_t *p)
{
	blob_t b;
	ssize_t n;

	if (!mounted) {
		return -ENODEV;
	}
	n = nvs_read(&fs, PARAMS_ID, &b, sizeof(b));
	if (n != (ssize_t)sizeof(b)) {
		return -ENOENT;
	}
	if (b.version != ACORE_VERSION || b.size != sizeof(acore_params_t) ||
	    b.crc != blob_crc(&b) || acore_params_check(&b.p) != 0) {
		return -EINVAL;
	}
	*p = b.p;
	return 0;
}

int params_store_save(const acore_params_t *p)
{
	blob_t b;
	ssize_t n;

	if (!mounted) {
		return -ENODEV;
	}
	memset(&b, 0, sizeof(b));
	b.version = ACORE_VERSION;
	b.size = sizeof(acore_params_t);
	b.p = *p;
	b.crc = blob_crc(&b);
	n = nvs_write(&fs, PARAMS_ID, &b, sizeof(b));
	/* 0 = identical data already stored */
	return (n == (ssize_t)sizeof(b) || n == 0) ? 0 : -EIO;
}
