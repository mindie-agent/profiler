/*
 * CANN 9.x Native Capture Shared-Memory ABI & Gear-1 MSPTI Aggregator
 *
 * [Role]
 *   Define the fixed-size /dev/shm control-plane layout shared between Python
 *   and C, process-filtering/device-mapping helpers, plus the Gear-1 MSPTI
 *   fixed buffer pool, FNV-1a streaming operator table, device-interval
 *   busy-union sweep, and atomic worker JSON writer.
 *
 * [Invariants]
 *   - sizeof(MindieCaptureHeader) == 1024, sizeof(MindieWorkerSlot) == 1024,
 *     sizeof(MindieCaptureShm) == 33792 (enforced at compile time).
 *   - Steady MSPTI buffer memory is bounded to 8 x 2 MiB = 16 MiB per NPU
 *     worker; non-capturing buffers return to the pool in O(1) without parsing.
 *   - Worker summary JSON is written to a .tmp file and published via rename().
 *
 * [Timeouts & Locks]
 *   Protected by g_agg_lock during active capture completion and JSON flush.
 *
 * [Side-Effect Policy]
 *   Writes only worker_pid*_dev*_gen*.json inside header.output_dir.
 */

#ifndef MINDIE_CANN9_CAPTURE_MSPTI_H
#define MINDIE_CANN9_CAPTURE_MSPTI_H

#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <mspti.h>

#define MINDIE_CAPTURE_MAGIC 0x4D494E4449454339ULL /* "MINDIEC9" */
#define MINDIE_CAPTURE_ABI_VERSION 3U
#define MINDIE_MAX_WORKERS 32U
#define MINDIE_MAX_WINDOW_STEPS 64U

#define GEAR_FAST_MSPTI 1U
#define GEAR_DEEP_ACLPROF 2U

#define MODE_AUTONOMOUS 0U
#define MODE_COORDINATED 1U

#define PHASE_STANDBY 0U
#define PHASE_ARMED 1U
#define PHASE_START_NOW 2U
#define PHASE_STOP_NOW 3U
#define PHASE_SHUTDOWN 4U

#define WORKER_IDLE 0U
#define WORKER_WARMUP 1U
#define WORKER_GATE_READY 2U
#define WORKER_CAPTURING 3U
#define WORKER_DONE 4U
#define WORKER_ERROR 5U

#define POOL_BUF_COUNT 8U
#define POOL_BUF_BYTES (2UL * 1024UL * 1024UL)
#define AGG_BUCKETS 4096U
#define MAX_INTERVALS 65536U

typedef struct MindieCaptureHeader {
    uint64_t magic;
    uint32_t abi_version;
    uint32_t gear;
    uint32_t control_mode;
    uint32_t desired_phase;
    uint64_t generation;
    uint32_t min_warmup_steps;
    uint32_t steady_window_steps;
    uint32_t target_capture_steps;
    uint32_t max_cv_ppm;
    uint32_t replays_per_step;
    uint32_t require_zero_alloc_steps;
    uint64_t min_step_interval_ns;
    uint64_t aclprof_data_type_mask;
    uint32_t aclprof_aicore_metrics;
    uint32_t active_worker_slots;
    uint64_t controller_arm_mono_ns;
    uint64_t controller_start_mono_ns;
    uint64_t controller_stop_mono_ns;
    char session_id[64];
    char output_dir[512];
    char libmsprofiler_path[256];
    uint32_t slot_overflow_count;
    uint8_t reserved[84];
} MindieCaptureHeader;

typedef struct MindieWorkerSlot {
    uint32_t claimed;
    int32_t pid;
    int32_t logical_device_id;
    int32_t physical_device_id;
    uint32_t worker_state;
    uint32_t active_graph_captures;
    uint64_t acked_generation;
    uint64_t total_steps;
    uint64_t graph_replays_total;
    uint64_t graph_captures_total;
    uint64_t alloc_calls_total;
    uint64_t last_alloc_step;
    uint64_t last_step_ns;
    uint64_t last_step_duration_ns;
    uint64_t window_mean_ns;
    uint64_t window_cv_ppm;
    uint64_t capture_start_mono_ns;
    uint64_t capture_end_mono_ns;
    uint64_t capture_start_step;
    uint64_t captured_steps;
    uint64_t graph_captures_in_window;
    uint64_t allocs_in_window;
    uint64_t window_capture_min_step_ns;
    uint64_t window_capture_max_step_ns;
    uint64_t window_capture_sum_step_ns;
    uint64_t window_capture_sum_sq_us;
    uint64_t mspti_records_captured;
    uint64_t mspti_records_dropped;
    int32_t last_error_code;
    uint32_t summary_written;
    char error_msg[128];
    char artifact_path[688];
} MindieWorkerSlot;

typedef struct MindieCaptureShm {
    MindieCaptureHeader header;
    MindieWorkerSlot slots[MINDIE_MAX_WORKERS];
} MindieCaptureShm;

_Static_assert(sizeof(MindieCaptureHeader) == 1024, "MindieCaptureHeader must be 1024 bytes");
_Static_assert(sizeof(MindieWorkerSlot) == 1024, "MindieWorkerSlot must be 1024 bytes");
_Static_assert(sizeof(MindieCaptureShm) == 33792, "MindieCaptureShm must be 33792 bytes");

static inline uint64_t mono_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static inline int should_skip_process(void) {
    char comm[64] = {0};
    int fd = open("/proc/self/comm", O_RDONLY);
    if (fd < 0) return 0;
    ssize_t n = read(fd, comm, sizeof(comm) - 1);
    close(fd);
    if (n <= 0) return 0;
    for (ssize_t i = 0; i < n; ++i) {
        if (comm[i] == '\n' || comm[i] == '\r') { comm[i] = '\0'; break; }
    }
    static const char *const skip_list[] = {
        "sh", "bash", "dash", "zsh", "env", "gcc", "g++", "cc1", "cc1plus",
        "collect2", "ld", "as", "bisheng", "clang", "uname", "lscpu",
        "npu-smi", "msprof", "git", "rm", "cp", "mv", "mkdir", "cat",
        "grep", "sed", "awk", NULL
    };
    for (int i = 0; skip_list[i] != NULL; ++i) {
        if (strcmp(comm, skip_list[i]) == 0) return 1;
    }
    return 0;
}

static inline int32_t map_physical_device(int32_t logical_id) {
    if (logical_id < 0) return -1;
    const char *vis = getenv("ASCEND_RT_VISIBLE_DEVICES");
    if (!vis || !vis[0]) return logical_id;
    int32_t idx = 0;
    const char *p = vis;
    while (*p) {
        while (*p == ' ' || *p == ',') p++;
        if (!*p) break;
        char *endp = NULL;
        long val = strtol(p, &endp, 10);
        if (endp == p) return logical_id;
        if (idx == logical_id) return (int32_t)val;
        idx++;
        p = endp;
        while (*p && *p != ',') p++;
    }
    return logical_id;
}

typedef struct AggEntry {
    uint32_t used;
    uint32_t kind; /* 1=kernel, 2=hccl, 3=comm */
    uint64_t count;
    uint64_t total_ns;
    uint64_t min_ns;
    uint64_t max_ns;
    uint64_t comm_count_sum;
    double bw_gbps_sum;
    char op_type[64];
    char name[192];
    char comm_name[64];
} AggEntry;

typedef struct DevInterval {
    uint64_t start_ns;
    uint64_t end_ns;
    uint32_t is_comm;
    uint32_t stream_id;
} DevInterval;

typedef msptiResult (*fn_msptiSubscribe_t)(msptiSubscriberHandle *, msptiCallbackFunc, void *);
typedef msptiResult (*fn_msptiUnsubscribe_t)(msptiSubscriberHandle);
typedef msptiResult (*fn_msptiEnableCallback_t)(uint32_t, msptiSubscriberHandle, msptiCallbackDomain, msptiCallbackId);
typedef msptiResult (*fn_msptiActivityRegisterCallbacks_t)(msptiBuffersCallbackRequestFunc, msptiBuffersCallbackCompleteFunc);
typedef msptiResult (*fn_msptiActivityEnable_t)(msptiActivityKind);
typedef msptiResult (*fn_msptiActivityDisable_t)(msptiActivityKind);
typedef msptiResult (*fn_msptiActivityGetNextRecord_t)(uint8_t *, size_t, msptiActivity **);
typedef msptiResult (*fn_msptiActivityFlushAll_t)(uint32_t);
typedef msptiResult (*fn_msptiActivityGetNumDroppedRecords_t)(void *, uint32_t, size_t *);
typedef msptiResult (*fn_msptiGetTimestamp_t)(uint64_t *);

static pthread_mutex_t g_agg_lock = PTHREAD_MUTEX_INITIALIZER;
static MindieCaptureShm *g_shm = NULL;
static int g_slot_idx = -1;
static uint8_t *g_pool_base = NULL;
static uint32_t g_pool_in_use[POOL_BUF_COUNT];
static AggEntry g_agg_table[AGG_BUCKETS];
static DevInterval g_intervals[MAX_INTERVALS];
static uint32_t g_interval_count = 0;
static uint32_t g_interval_overflow = 0;
static uint32_t g_agg_overflow = 0;
static uint64_t g_agg_dropped_records = 0ULL;
static uint32_t g_mspti_activity_armed = 0;
static msptiSubscriberHandle g_mspti_sub = NULL;
static volatile uint64_t g_mspti_win_start_ts = UINT64_MAX;
static volatile uint64_t g_mspti_win_end_ts = 1ULL;
static fn_msptiSubscribe_t p_msptiSubscribe = NULL;
static fn_msptiActivityRegisterCallbacks_t p_msptiActivityRegisterCallbacks = NULL;
static fn_msptiActivityEnable_t p_msptiActivityEnable = NULL;
static fn_msptiActivityGetNextRecord_t p_msptiActivityGetNextRecord = NULL;
static fn_msptiActivityFlushAll_t p_msptiActivityFlushAll = NULL;
static fn_msptiActivityGetNumDroppedRecords_t p_msptiActivityGetNumDroppedRecords = NULL;
static fn_msptiGetTimestamp_t p_msptiGetTimestamp = NULL;

static inline void release_pool_buf(uint8_t *buf) {
    if (!buf) {
        return;
    }
    if (g_pool_base && buf >= g_pool_base &&
        buf < g_pool_base + (POOL_BUF_COUNT * POOL_BUF_BYTES)) {
        size_t idx = (size_t)(buf - g_pool_base) / POOL_BUF_BYTES;
        if (idx < POOL_BUF_COUNT) {
            __atomic_store_n(&g_pool_in_use[idx], 0U, __ATOMIC_RELEASE);
            return;
        }
    }
    free(buf);
}

static void mspti_buf_requested(uint8_t **buffer, size_t *size, size_t *max_num_records) {
    *max_num_records = 0;
    *size = POOL_BUF_BYTES;
    if (g_pool_base) {
        for (uint32_t i = 0; i < POOL_BUF_COUNT; ++i) {
            uint32_t expected = 0U;
            if (__atomic_compare_exchange_n(
                    &g_pool_in_use[i], &expected, 1U, 0, __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) {
                *buffer = g_pool_base + ((size_t)i * POOL_BUF_BYTES);
                return;
            }
        }
    }
    *buffer = (uint8_t *)malloc(POOL_BUF_BYTES);
    if (!*buffer) {
        *size = 0;
    }
}

static inline uint64_t fnv1a_hash(uint32_t kind, const char *op_type, const char *name) {
    uint64_t h = 1469598103934665603ULL ^ (uint64_t)kind;
    for (const unsigned char *p = (const unsigned char *)op_type; p && *p; ++p) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    h ^= 0xFFULL;
    for (const unsigned char *p = (const unsigned char *)name; p && *p; ++p) {
        h ^= (uint64_t)(*p);
        h *= 1099511628211ULL;
    }
    return h;
}

static void record_agg_locked(
    uint32_t kind,
    const char *op_type,
    const char *name,
    const char *comm_name,
    uint64_t start_ns,
    uint64_t end_ns,
    uint32_t stream_id,
    uint64_t comm_count,
    double bw_gbps
) {
    if (end_ns < start_ns) {
        return;
    }
    uint64_t dur = end_ns - start_ns;
    const char *safe_type = op_type ? op_type : "";
    const char *safe_name = (name && name[0]) ? name : "unknown";
    const char *safe_comm = comm_name ? comm_name : "";

    if (kind == 1U || kind == 2U) {
        if (g_interval_count < MAX_INTERVALS) {
            g_intervals[g_interval_count].start_ns = start_ns;
            g_intervals[g_interval_count].end_ns = end_ns;
            g_intervals[g_interval_count].is_comm = (kind == 2U) ? 1U : 0U;
            g_intervals[g_interval_count].stream_id = stream_id;
            g_interval_count++;
        } else {
            g_interval_overflow = 1U;
        }
    }

    uint64_t h = fnv1a_hash(kind, safe_type, safe_name);
    for (uint32_t probe = 0; probe < AGG_BUCKETS; ++probe) {
        uint32_t idx = (uint32_t)((h + probe) & (AGG_BUCKETS - 1U));
        AggEntry *e = &g_agg_table[idx];
        if (!e->used) {
            e->used = 1U;
            e->kind = kind;
            e->count = 1ULL;
            e->total_ns = dur;
            e->min_ns = dur;
            e->max_ns = dur;
            e->comm_count_sum = comm_count;
            e->bw_gbps_sum = bw_gbps;
            snprintf(e->op_type, sizeof(e->op_type), "%s", safe_type);
            snprintf(e->name, sizeof(e->name), "%s", safe_name);
            snprintf(e->comm_name, sizeof(e->comm_name), "%s", safe_comm);
            return;
        }
        if (e->kind == kind &&
            strncmp(e->op_type, safe_type, sizeof(e->op_type) - 1) == 0 &&
            strncmp(e->name, safe_name, sizeof(e->name) - 1) == 0) {
            e->count += 1ULL;
            e->total_ns += dur;
            if (dur < e->min_ns) e->min_ns = dur;
            if (dur > e->max_ns) e->max_ns = dur;
            e->comm_count_sum += comm_count;
            e->bw_gbps_sum += bw_gbps;
            return;
        }
    }
    g_agg_overflow = 1U;
    g_agg_dropped_records += 1ULL;
}

static inline void fprint_json_escaped(FILE *fp, const char *s) {
    fputc('"', fp);
    if (s) {
        for (const unsigned char *p = (const unsigned char *)s; *p; ++p) {
            unsigned char c = *p;
            if (c == '"') fputs("\\\"", fp);
            else if (c == '\\') fputs("\\\\", fp);
            else if (c == '\n') fputs("\\n", fp);
            else if (c == '\r') fputs("\\r", fp);
            else if (c == '\t') fputs("\\t", fp);
            else if (c < 0x20) fprintf(fp, "\\u%04x", (unsigned int)c);
            else fputc((int)c, fp);
        }
    }
    fputc('"', fp);
}

static int cmp_interval_start(const void *a, const void *b) {
    const DevInterval *ia = (const DevInterval *)a;
    const DevInterval *ib = (const DevInterval *)b;
    if (ia->start_ns != ib->start_ns) return ia->start_ns < ib->start_ns ? -1 : 1;
    if (ia->end_ns != ib->end_ns) return ia->end_ns < ib->end_ns ? -1 : 1;
    return 0;
}

static uint64_t compute_union_ns(const DevInterval *arr, uint32_t n, int filter_comm) {
    uint64_t total = 0ULL, cur_s = 0ULL, cur_e = 0ULL;
    int active = 0;
    for (uint32_t i = 0; i < n; ++i) {
        if (filter_comm >= 0 && (int)arr[i].is_comm != filter_comm) continue;
        uint64_t s = arr[i].start_ns, e = arr[i].end_ns;
        if (e <= s) continue;
        if (!active) {
            cur_s = s; cur_e = e; active = 1;
        } else if (s <= cur_e) {
            if (e > cur_e) cur_e = e;
        } else {
            total += (cur_e - cur_s);
            cur_s = s; cur_e = e;
        }
    }
    if (active) total += (cur_e - cur_s);
    return total;
}

static void write_gear1_worker_json(
    const char *output_dir,
    int pid,
    uint64_t generation,
    MindieWorkerSlot *slot
) {
    char final_path[sizeof(slot->artifact_path)];
    char tmp_path[sizeof(slot->artifact_path) + 16];
    int32_t dev_tag = slot->physical_device_id >= 0 ? slot->physical_device_id : slot->logical_device_id;
    int n_final = snprintf(
        final_path, sizeof(final_path), "%s/worker_pid%d_dev%d_gen%llu.json",
        output_dir, pid, (int)dev_tag, (unsigned long long)generation);
    int n_tmp = snprintf(tmp_path, sizeof(tmp_path), "%s.tmp", final_path);
    if (n_final < 0 || (size_t)n_final >= sizeof(final_path) ||
        n_tmp < 0 || (size_t)n_tmp >= sizeof(tmp_path)) {
        slot->last_error_code = -105;
        snprintf(slot->error_msg, sizeof(slot->error_msg), "worker summary artifact path truncated");
        return;
    }

    pthread_mutex_lock(&g_agg_lock);
    if (g_interval_count > 1U) {
        qsort(g_intervals, g_interval_count, sizeof(DevInterval), cmp_interval_start);
    }
    uint64_t span_ns = 0ULL;
    if (g_interval_count > 0U) {
        uint64_t min_s = g_intervals[0].start_ns, max_e = g_intervals[0].end_ns;
        for (uint32_t i = 1; i < g_interval_count; ++i) {
            if (g_intervals[i].end_ns > max_e) max_e = g_intervals[i].end_ns;
        }
        if (max_e > min_s) span_ns = max_e - min_s;
    }
    uint64_t busy_union_ns = compute_union_ns(g_intervals, g_interval_count, -1);
    uint64_t non_comm_union_ns = compute_union_ns(g_intervals, g_interval_count, 0);
    uint64_t exposed_comm_ns = busy_union_ns > non_comm_union_ns ? (busy_union_ns - non_comm_union_ns) : 0ULL;
    uint64_t uncovered_ns = span_ns > busy_union_ns ? (span_ns - busy_union_ns) : 0ULL;

    FILE *fp = fopen(tmp_path, "wb");
    if (!fp) {
        slot->last_error_code = errno ? errno : -1;
        snprintf(slot->error_msg, sizeof(slot->error_msg), "fopen failed for worker summary");
        pthread_mutex_unlock(&g_agg_lock);
        return;
    }

    fprintf(fp, "{\n  \"pid\": %d,\n  \"logical_device_id\": %d,\n  \"physical_device_id\": %d,\n",
            pid, (int)slot->logical_device_id, (int)slot->physical_device_id);
    fprintf(fp, "  \"generation\": %llu,\n  \"captured_steps\": %llu,\n  \"capture_start_step\": %llu,\n",
            (unsigned long long)generation, (unsigned long long)slot->captured_steps,
            (unsigned long long)slot->capture_start_step);
    fprintf(fp, "  \"capture_wall_ns\": %llu,\n  \"observed_event_span_ns\": %llu,\n",
            (unsigned long long)(slot->capture_end_mono_ns > slot->capture_start_mono_ns
                                     ? (slot->capture_end_mono_ns - slot->capture_start_mono_ns) : 0ULL),
            (unsigned long long)span_ns);
    fprintf(fp, "  \"device_busy_union_ns\": %llu,\n  \"compute_union_ns\": %llu,\n",
            (unsigned long long)busy_union_ns, (unsigned long long)non_comm_union_ns);
    fprintf(fp, "  \"exposed_comm_ns\": %llu,\n  \"device_uncovered_ns\": %llu,\n",
            (unsigned long long)exposed_comm_ns, (unsigned long long)uncovered_ns);
    fprintf(fp, "  \"interval_count\": %u,\n  \"interval_overflow\": %s,\n",
            g_interval_count, g_interval_overflow ? "true" : "false");
    fprintf(fp, "  \"operator_table_overflow\": %s,\n  \"operator_records_dropped\": %llu,\n",
            g_agg_overflow ? "true" : "false", (unsigned long long)g_agg_dropped_records);
    fprintf(fp, "  \"mspti_records_captured\": %llu,\n  \"mspti_records_dropped\": %llu,\n",
            (unsigned long long)slot->mspti_records_captured, (unsigned long long)slot->mspti_records_dropped);
    fprintf(fp, "  \"graph_captures_in_window\": %llu,\n  \"allocs_in_window\": %llu,\n  \"operators\": [\n",
            (unsigned long long)slot->graph_captures_in_window, (unsigned long long)slot->allocs_in_window);

    int first = 1;
    for (uint32_t i = 0; i < AGG_BUCKETS; ++i) {
        const AggEntry *e = &g_agg_table[i];
        if (!e->used) continue;
        if (!first) fprintf(fp, ",\n");
        first = 0;
        const char *kind_str = (e->kind == 1U) ? "kernel" : ((e->kind == 2U) ? "hccl" : "comm");
        fprintf(fp, "    {\"kind\": \"%s\", \"op_type\": ", kind_str);
        fprint_json_escaped(fp, e->op_type);
        fprintf(fp, ", \"name\": ");
        fprint_json_escaped(fp, e->name);
        fprintf(fp, ", \"comm_name\": ");
        fprint_json_escaped(fp, e->comm_name);
        fprintf(fp, ", \"count\": %llu, \"total_ns\": %llu, \"min_ns\": %llu, \"max_ns\": %llu",
                (unsigned long long)e->count, (unsigned long long)e->total_ns,
                (unsigned long long)e->min_ns, (unsigned long long)e->max_ns);
        fprintf(fp, ", \"comm_count_sum\": %llu, \"bw_gbps_mean\": %.4f}",
                (unsigned long long)e->comm_count_sum,
                e->count > 0 ? (e->bw_gbps_sum / (double)e->count) : 0.0);
    }
    fprintf(fp, "\n  ]\n}\n");
    fclose(fp);
    pthread_mutex_unlock(&g_agg_lock);

    if (rename(tmp_path, final_path) == 0) {
        int n_art = snprintf(slot->artifact_path, sizeof(slot->artifact_path), "%s", final_path);
        if (n_art < 0 || (size_t)n_art >= sizeof(slot->artifact_path)) {
            slot->last_error_code = -105;
            snprintf(slot->error_msg, sizeof(slot->error_msg), "worker artifact_path truncated");
            return;
        }
        __atomic_store_n(&slot->summary_written, 1U, __ATOMIC_RELEASE);
    } else {
        slot->last_error_code = errno ? errno : -2;
        snprintf(slot->error_msg, sizeof(slot->error_msg), "rename failed for worker summary");
    }
}

static void mspti_noop_cb(void *ud, msptiCallbackDomain dom, msptiCallbackId cbid, const msptiCallbackData *cb) {
    (void)ud; (void)dom; (void)cbid; (void)cb;
}

static void mspti_buf_completed(uint8_t *buffer, size_t size, size_t valid_size) {
    (void)size;
    if (!buffer) return;
    uint64_t t0 = __atomic_load_n(&g_mspti_win_start_ts, __ATOMIC_ACQUIRE);
    uint64_t t1 = __atomic_load_n(&g_mspti_win_end_ts, __ATOMIC_ACQUIRE);
    if (t0 == UINT64_MAX || valid_size == 0 || !p_msptiActivityGetNextRecord) {
        release_pool_buf(buffer);
        return;
    }
    pthread_mutex_lock(&g_agg_lock);
    msptiActivity *rec = NULL;
    msptiResult st;
    uint64_t added = 0;
    do {
        st = p_msptiActivityGetNextRecord(buffer, valid_size, &rec);
        if (st == MSPTI_SUCCESS && rec != NULL) {
            if (rec->kind == MSPTI_ACTIVITY_KIND_KERNEL) {
                msptiActivityKernel *k = (msptiActivityKernel *)rec;
                if (k->start >= t0 && (t1 == 0ULL || k->end <= t1)) {
                    record_agg_locked(1U, k->type, k->name, "", k->start, k->end, k->ds.streamId, 0ULL, 0.0);
                    added++;
                }
            } else if (rec->kind == MSPTI_ACTIVITY_KIND_HCCL) {
                msptiActivityHccl *h = (msptiActivityHccl *)rec;
                if (h->start >= t0 && (t1 == 0ULL || h->end <= t1)) {
                    record_agg_locked(2U, "HCCL", h->name, h->commName, h->start, h->end, h->ds.streamId, 0ULL, h->bandWidth);
                    added++;
                }
            } else if (rec->kind == MSPTI_ACTIVITY_KIND_COMMUNICATION) {
                msptiActivityCommunication *c = (msptiActivityCommunication *)rec;
                if (c->start >= t0 && (t1 == 0ULL || c->end <= t1)) {
                    record_agg_locked(3U, c->algType ? c->algType : "COMM", c->name, c->commName,
                                      c->start, c->end, c->ds.streamId, c->count, 0.0);
                    added++;
                }
            }
        }
    } while (st == MSPTI_SUCCESS);
    if (added > 0 && g_shm && g_slot_idx >= 0) {
        __atomic_add_fetch(&g_shm->slots[g_slot_idx].mspti_records_captured, added, __ATOMIC_RELAXED);
    }
    pthread_mutex_unlock(&g_agg_lock);
    release_pool_buf(buffer);
}

static int arm_mspti_activities_once(int *err_out, char *msg_buf, size_t msg_cap) {
    if (g_mspti_activity_armed) return 0;
    if (!g_shm || g_shm->header.gear != GEAR_FAST_MSPTI) return 0;
    if (!p_msptiActivityRegisterCallbacks) {
        p_msptiSubscribe = (fn_msptiSubscribe_t)dlsym(RTLD_DEFAULT, "msptiSubscribe");
        if (!p_msptiSubscribe) {
            const char *mspti_so = getenv("MINDIE_CAPTURE_LIBMSPTI");
            dlopen((mspti_so && mspti_so[0]) ? mspti_so : "libmspti.so", RTLD_NOW | RTLD_GLOBAL);
            p_msptiSubscribe = (fn_msptiSubscribe_t)dlsym(RTLD_DEFAULT, "msptiSubscribe");
        }
        p_msptiActivityRegisterCallbacks = (fn_msptiActivityRegisterCallbacks_t)dlsym(RTLD_DEFAULT, "msptiActivityRegisterCallbacks");
        p_msptiActivityEnable = (fn_msptiActivityEnable_t)dlsym(RTLD_DEFAULT, "msptiActivityEnable");
        p_msptiActivityGetNextRecord = (fn_msptiActivityGetNextRecord_t)dlsym(RTLD_DEFAULT, "msptiActivityGetNextRecord");
        p_msptiActivityFlushAll = (fn_msptiActivityFlushAll_t)dlsym(RTLD_DEFAULT, "msptiActivityFlushAll");
        p_msptiActivityGetNumDroppedRecords = (fn_msptiActivityGetNumDroppedRecords_t)dlsym(RTLD_DEFAULT, "msptiActivityGetNumDroppedRecords");
        p_msptiGetTimestamp = (fn_msptiGetTimestamp_t)dlsym(RTLD_DEFAULT, "msptiGetTimestamp");
    }
    if (!p_msptiSubscribe || !p_msptiActivityRegisterCallbacks || !p_msptiActivityEnable ||
        !p_msptiActivityGetNextRecord || !p_msptiActivityFlushAll || !p_msptiGetTimestamp) {
        if (err_out) *err_out = -106;
        if (msg_buf && msg_cap > 0) snprintf(msg_buf, msg_cap, "cannot resolve MSPTI symbols from libmspti.so");
        return -1;
    }
    if (!g_pool_base) {
        g_pool_base = (uint8_t *)malloc(POOL_BUF_COUNT * POOL_BUF_BYTES);
        if (!g_pool_base) {
            if (err_out) *err_out = -107;
            if (msg_buf && msg_cap > 0) snprintf(msg_buf, msg_cap, "failed to allocate 16 MiB MSPTI buffer pool");
            return -1;
        }
        memset(g_pool_in_use, 0, sizeof(g_pool_in_use));
    }
    msptiResult rc = p_msptiSubscribe(&g_mspti_sub, mspti_noop_cb, NULL);
    if (rc != MSPTI_SUCCESS) {
        if (err_out) *err_out = (int)rc;
        if (msg_buf && msg_cap > 0) snprintf(msg_buf, msg_cap, "msptiSubscribe failed rc=%d", (int)rc);
        return -1;
    }
    rc = p_msptiActivityRegisterCallbacks(mspti_buf_requested, mspti_buf_completed);
    if (rc != MSPTI_SUCCESS) {
        if (err_out) *err_out = (int)rc;
        if (msg_buf && msg_cap > 0) snprintf(msg_buf, msg_cap, "msptiActivityRegisterCallbacks failed rc=%d", (int)rc);
        return -1;
    }
    const msptiActivityKind kinds[3] = {
        MSPTI_ACTIVITY_KIND_KERNEL, MSPTI_ACTIVITY_KIND_HCCL, MSPTI_ACTIVITY_KIND_COMMUNICATION
    };
    for (int i = 0; i < 3; ++i) {
        rc = p_msptiActivityEnable(kinds[i]);
        if (rc != MSPTI_SUCCESS) {
            if (err_out) *err_out = (int)rc;
            if (msg_buf && msg_cap > 0) snprintf(msg_buf, msg_cap, "msptiActivityEnable(%d) failed rc=%d", (int)kinds[i], (int)rc);
            return -1;
        }
    }
    g_mspti_activity_armed = 1U;
    return 0;
}

#endif /* MINDIE_CANN9_CAPTURE_MSPTI_H */
