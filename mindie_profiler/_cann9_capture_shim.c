/*
 * CANN 9.x Native Steady-State Profiling Shim (libmindie_cann9_capture.so)
 *
 * [Role]
 *   In-process preload shim built strictly on CANN 9.x public C headers
 *   (<mspti.h>, <acl/acl_rt.h>, <acl/acl_prof.h>).  Implements lazy NPU worker
 *   slot registration over /dev/shm, official aclrtApiInjectionSetFunc runtime
 *   hooks (NPUGraph capture/replay + stream sync + HBM malloc churn), a 3-level
 *   SteadyStateGate, Gear-1 MSPTI window control, and Gear-2 sniper aclprof.
 *
 * [Invariants]
 *   - Shell/compiler helper processes skip initialization immediately; CPU-only
 *     processes never claim a /dev/shm WorkerSlot until an NPU device is bound.
 *   - SteadyStateGate blocks capture while active_graph_captures > 0, while
 *     warmup/window steps are incomplete, or while step-duration CV exceeds
 *     max_cv_ppm.
 *
 * [Timeouts & Locks]
 *   Protected by g_lock across step state transitions; fork-safe via
 *   pthread_atfork child reset.
 *
 * [Side-Effect Policy]
 *   Touches only the session /dev/shm file and header.output_dir.  No network.
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <math.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <acl/acl_prof.h>
#include <acl/acl_rt.h>

#include "_cann9_capture_mspti.h"

#define DEFAULT_GEAR2_DATA_MASK ( \
    ACL_PROF_ACL_API | ACL_PROF_TASK_TIME | ACL_PROF_AICORE_METRICS | \
    ACL_PROF_AICPU | ACL_PROF_HCCL_TRACE | ACL_PROF_MSPROFTX | \
    ACL_PROF_RUNTIME_API | ACL_PROF_OP_ATTR | ACL_PROF_AICORE_SHAPE)

typedef aclError (*fn_aclrtGetFunction_t)(const char *, aclrtApiFunc *, aclrtApiFunc *);
typedef aclError (*fn_aclrtSetFunction_t)(const char *, aclrtApiFunc);
typedef aclError (*fn_aclrtSetDevice_t)(int32_t);
typedef aclError (*fn_aclrtGetDevice_t)(int32_t *);
typedef aclError (*fn_aclrtSynchronizeStream_t)(aclrtStream);
typedef aclError (*fn_aclrtSynchronizeDevice_t)(void);
typedef aclError (*fn_aclrtMalloc_t)(void **, size_t, aclrtMemMallocPolicy);
typedef aclError (*fn_ri_begin_t)(aclrtStream, aclmdlRICaptureMode);
typedef aclError (*fn_ri_to_model_begin_t)(aclrtStream, aclmdlRI *);
typedef aclError (*fn_ri_end_t)(aclrtStream, aclmdlRI *);
typedef aclError (*fn_ri_exec_async_t)(aclmdlRI, aclrtStream);
typedef aclError (*fn_ri_exec_t)(aclmdlRI, int32_t);

typedef aclError (*fn_aclprofInit_t)(const char *, size_t);
typedef aclError (*fn_aclprofFinalize_t)(void);
typedef aclprofConfig *(*fn_aclprofCreateConfig_t)(
    uint32_t *, uint32_t, aclprofAicoreMetrics, const aclprofAicoreEvents *, uint64_t);
typedef aclError (*fn_aclprofDestroyConfig_t)(const aclprofConfig *);
typedef aclError (*fn_aclprofStart_t)(const aclprofConfig *);
typedef aclError (*fn_aclprofStop_t)(const aclprofConfig *);

static MindieCaptureShm *g_shm = NULL;
static int g_shm_fd = -1;
static int g_slot_idx = -1;
static pid_t g_pid = 0;
static int32_t g_logical_dev = -1;
static int32_t g_physical_dev = -1;
static uint64_t g_seen_generation = 0;
static uint32_t g_explicit_step_mode = 0;
static uint64_t g_replay_substep = 0;
static volatile uint32_t g_capturing = 0;
static uint64_t g_step_durations_ring[MINDIE_MAX_WINDOW_STEPS];
static uint32_t g_step_ring_count = 0;
static uint32_t g_step_ring_pos = 0;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;

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

static fn_aclrtSetDevice_t orig_aclrtSetDevice = NULL;
static fn_aclrtGetDevice_t orig_aclrtGetDevice = NULL;
static fn_aclrtSynchronizeStream_t orig_aclrtSynchronizeStream = NULL;
static fn_aclrtSynchronizeDevice_t orig_aclrtSynchronizeDevice = NULL;
static fn_aclrtMalloc_t orig_aclrtMalloc = NULL;
static fn_ri_begin_t orig_ri_begin = NULL;
static fn_ri_to_model_begin_t orig_ri_to_model_begin = NULL;
static fn_ri_end_t orig_ri_end = NULL;
static fn_ri_exec_async_t orig_ri_exec_async = NULL;
static fn_ri_exec_t orig_ri_exec = NULL;

static void *g_msprof_dl = NULL;
static aclprofConfig *g_prof_cfg = NULL;
static fn_aclprofInit_t p_aclprofInit = NULL;
static fn_aclprofFinalize_t p_aclprofFinalize = NULL;
static fn_aclprofCreateConfig_t p_aclprofCreateConfig = NULL;
static fn_aclprofDestroyConfig_t p_aclprofDestroyConfig = NULL;
static fn_aclprofStart_t p_aclprofStart = NULL;
static fn_aclprofStop_t p_aclprofStop = NULL;
static char g_prof_worker_dir[512];

static uint64_t mono_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static int should_skip_process(void) {
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

static int32_t map_physical_device(int32_t logical_id) {
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

static void arm_mspti_activities_once(void) {
    if (g_mspti_activity_armed || !g_shm || g_shm->header.gear != GEAR_FAST_MSPTI) return;
    if (!p_msptiActivityRegisterCallbacks) {
        p_msptiSubscribe = (fn_msptiSubscribe_t)dlsym(RTLD_DEFAULT, "msptiSubscribe");
        p_msptiActivityRegisterCallbacks = (fn_msptiActivityRegisterCallbacks_t)dlsym(RTLD_DEFAULT, "msptiActivityRegisterCallbacks");
        p_msptiActivityEnable = (fn_msptiActivityEnable_t)dlsym(RTLD_DEFAULT, "msptiActivityEnable");
        p_msptiActivityGetNextRecord = (fn_msptiActivityGetNextRecord_t)dlsym(RTLD_DEFAULT, "msptiActivityGetNextRecord");
        p_msptiActivityFlushAll = (fn_msptiActivityFlushAll_t)dlsym(RTLD_DEFAULT, "msptiActivityFlushAll");
        p_msptiActivityGetNumDroppedRecords = (fn_msptiActivityGetNumDroppedRecords_t)dlsym(RTLD_DEFAULT, "msptiActivityGetNumDroppedRecords");
        p_msptiGetTimestamp = (fn_msptiGetTimestamp_t)dlsym(RTLD_DEFAULT, "msptiGetTimestamp");
    }
    if (!p_msptiSubscribe || !p_msptiActivityRegisterCallbacks || !p_msptiActivityEnable) return;
    if (!g_pool_base) {
        g_pool_base = (uint8_t *)malloc(POOL_BUF_COUNT * POOL_BUF_BYTES);
        if (g_pool_base) memset(g_pool_in_use, 0, sizeof(g_pool_in_use));
    }
    p_msptiSubscribe(&g_mspti_sub, mspti_noop_cb, NULL);
    p_msptiActivityRegisterCallbacks(mspti_buf_requested, mspti_buf_completed);
    p_msptiActivityEnable(MSPTI_ACTIVITY_KIND_KERNEL);
    p_msptiActivityEnable(MSPTI_ACTIVITY_KIND_HCCL);
    p_msptiActivityEnable(MSPTI_ACTIVITY_KIND_COMMUNICATION);
    g_mspti_activity_armed = 1U;
}

static MindieWorkerSlot *ensure_worker_slot_locked(int32_t dev_hint) {
    if (!g_shm) return NULL;
    if (dev_hint >= 0 && g_logical_dev < 0) {
        g_logical_dev = dev_hint;
        g_physical_dev = map_physical_device(dev_hint);
    } else if (g_logical_dev < 0 && orig_aclrtGetDevice) {
        int32_t queried = -1;
        if (orig_aclrtGetDevice(&queried) == 0 && queried >= 0) {
            g_logical_dev = queried;
            g_physical_dev = map_physical_device(queried);
        }
    }
    if (g_slot_idx >= 0) {
        MindieWorkerSlot *slot = &g_shm->slots[g_slot_idx];
        if (g_logical_dev >= 0 && slot->logical_device_id < 0) {
            slot->logical_device_id = g_logical_dev;
            slot->physical_device_id = g_physical_dev;
        }
        return slot;
    }
    for (uint32_t i = 0; i < MINDIE_MAX_WORKERS; ++i) {
        MindieWorkerSlot *slot = &g_shm->slots[i];
        uint32_t expected = 0U;
        if (__atomic_compare_exchange_n(&slot->claimed, &expected, 1U, 0, __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) {
            memset(slot, 0, sizeof(*slot));
            slot->claimed = 1U;
            slot->pid = (int32_t)g_pid;
            slot->logical_device_id = g_logical_dev;
            slot->physical_device_id = g_physical_dev;
            slot->worker_state = WORKER_IDLE;
            __atomic_store_n(&slot->claimed, 2U, __ATOMIC_RELEASE);
            __atomic_add_fetch(&g_shm->header.active_worker_slots, 1U, __ATOMIC_ACQ_REL);
            g_slot_idx = (int)i;
            return slot;
        }
    }
    return NULL;
}

static int start_capture_locked(MindieWorkerSlot *slot, aclrtStream stream) {
    if (stream != NULL && orig_aclrtSynchronizeStream) {
        orig_aclrtSynchronizeStream(stream);
    } else if (orig_aclrtSynchronizeDevice) {
        orig_aclrtSynchronizeDevice();
    }
    if (g_shm->header.gear == GEAR_FAST_MSPTI) {
        arm_mspti_activities_once();
        __atomic_store_n(&g_mspti_win_start_ts, UINT64_MAX, __ATOMIC_RELEASE);
        if (p_msptiActivityFlushAll) p_msptiActivityFlushAll(1U);
        g_dropped_baseline = 0;
        if (p_msptiActivityGetNumDroppedRecords) {
            size_t dropped = 0;
            if (p_msptiActivityGetNumDroppedRecords(NULL, 0U, &dropped) == MSPTI_SUCCESS) {
                g_dropped_baseline = dropped;
            }
        }
        pthread_mutex_lock(&g_agg_lock);
        memset(g_agg_table, 0, sizeof(g_agg_table));
        g_interval_count = 0U;
        g_interval_overflow = 0U;
        slot->mspti_records_captured = 0ULL;
        slot->mspti_records_dropped = 0ULL;
        pthread_mutex_unlock(&g_agg_lock);
        uint64_t ts_start = 0ULL;
        if (p_msptiGetTimestamp) p_msptiGetTimestamp(&ts_start);
        __atomic_store_n(&g_mspti_win_end_ts, 0ULL, __ATOMIC_RELEASE);
        __atomic_store_n(&g_mspti_win_start_ts, ts_start, __ATOMIC_RELEASE);
    } else {
        if (!g_msprof_dl) {
            const char *so_path = g_shm->header.libmsprofiler_path[0]
                                      ? g_shm->header.libmsprofiler_path : "libmsprofiler.so";
            g_msprof_dl = dlopen(so_path, RTLD_LAZY | RTLD_LOCAL);
            if (g_msprof_dl) {
                p_aclprofInit = (fn_aclprofInit_t)dlsym(g_msprof_dl, "aclprofInit");
                p_aclprofFinalize = (fn_aclprofFinalize_t)dlsym(g_msprof_dl, "aclprofFinalize");
                p_aclprofCreateConfig = (fn_aclprofCreateConfig_t)dlsym(g_msprof_dl, "aclprofCreateConfig");
                p_aclprofDestroyConfig = (fn_aclprofDestroyConfig_t)dlsym(g_msprof_dl, "aclprofDestroyConfig");
                p_aclprofStart = (fn_aclprofStart_t)dlsym(g_msprof_dl, "aclprofStart");
                p_aclprofStop = (fn_aclprofStop_t)dlsym(g_msprof_dl, "aclprofStop");
            }
        }
        if (!p_aclprofInit || !p_aclprofCreateConfig || !p_aclprofStart || !p_aclprofStop) {
            slot->last_error_code = -101;
            snprintf(slot->error_msg, sizeof(slot->error_msg), "cannot resolve aclprof symbols from libmsprofiler.so");
            __atomic_store_n(&slot->worker_state, WORKER_ERROR, __ATOMIC_RELEASE);
            return -1;
        }
        int32_t ldev = slot->logical_device_id >= 0 ? slot->logical_device_id : 0;
        int32_t pdev = slot->physical_device_id >= 0 ? slot->physical_device_id : ldev;
        snprintf(g_prof_worker_dir, sizeof(g_prof_worker_dir), "%s/rank_%d_device_%d_pid%d_gen%llu",
                 g_shm->header.output_dir, g_slot_idx >= 0 ? g_slot_idx : 0, (int)pdev,
                 (int)g_pid, (unsigned long long)g_seen_generation);
        mkdir(g_prof_worker_dir, 0755);

        aclError rc = p_aclprofInit(g_prof_worker_dir, strlen(g_prof_worker_dir));
        if (rc != 0) {
            slot->last_error_code = (int32_t)rc;
            snprintf(slot->error_msg, sizeof(slot->error_msg), "aclprofInit failed rc=%d", (int)rc);
            __atomic_store_n(&slot->worker_state, WORKER_ERROR, __ATOMIC_RELEASE);
            return -1;
        }
        uint32_t dev_arr[1] = {(uint32_t)ldev};
        uint64_t mask = g_shm->header.aclprof_data_type_mask
                            ? g_shm->header.aclprof_data_type_mask : DEFAULT_GEAR2_DATA_MASK;
        g_prof_cfg = p_aclprofCreateConfig(
            dev_arr, 1U, (aclprofAicoreMetrics)g_shm->header.aclprof_aicore_metrics, NULL, mask);
        if (!g_prof_cfg) {
            p_aclprofFinalize();
            slot->last_error_code = -102;
            snprintf(slot->error_msg, sizeof(slot->error_msg), "aclprofCreateConfig returned NULL");
            __atomic_store_n(&slot->worker_state, WORKER_ERROR, __ATOMIC_RELEASE);
            return -1;
        }
        rc = p_aclprofStart(g_prof_cfg);
        if (rc != 0) {
            p_aclprofDestroyConfig(g_prof_cfg);
            g_prof_cfg = NULL;
            p_aclprofFinalize();
            slot->last_error_code = (int32_t)rc;
            snprintf(slot->error_msg, sizeof(slot->error_msg), "aclprofStart failed rc=%d", (int)rc);
            __atomic_store_n(&slot->worker_state, WORKER_ERROR, __ATOMIC_RELEASE);
            return -1;
        }
    }

    slot->capture_start_mono_ns = mono_ns();
    slot->last_step_ns = slot->capture_start_mono_ns;
    slot->capture_start_step = slot->total_steps;
    slot->captured_steps = 0ULL;
    slot->graph_captures_in_window = 0ULL;
    slot->allocs_in_window = 0ULL;
    slot->window_capture_min_step_ns = UINT64_MAX;
    slot->window_capture_max_step_ns = 0ULL;
    slot->window_capture_sum_step_ns = 0ULL;
    slot->window_capture_sum_sq_us = 0ULL;
    __atomic_store_n(&g_capturing, 1U, __ATOMIC_RELEASE);
    __atomic_store_n(&slot->worker_state, WORKER_CAPTURING, __ATOMIC_RELEASE);
    return 0;
}

static void stop_capture_locked(MindieWorkerSlot *slot, aclrtStream stream) {
    if (!__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) return;
    if (stream != NULL && orig_aclrtSynchronizeStream) {
        orig_aclrtSynchronizeStream(stream);
    } else if (orig_aclrtSynchronizeDevice) {
        orig_aclrtSynchronizeDevice();
    }
    slot->capture_end_mono_ns = mono_ns();

    if (g_shm->header.gear == GEAR_FAST_MSPTI) {
        uint64_t ts_end = 0ULL;
        if (p_msptiGetTimestamp) p_msptiGetTimestamp(&ts_end);
        __atomic_store_n(&g_mspti_win_end_ts, ts_end > 0ULL ? ts_end : (UINT64_MAX - 1ULL), __ATOMIC_RELEASE);
        uint64_t prev_recs = 0ULL;
        for (int tick = 0; tick < 20; ++tick) {
            if (p_msptiActivityFlushAll) p_msptiActivityFlushAll(1U);
            uint64_t cur_recs = __atomic_load_n(&slot->mspti_records_captured, __ATOMIC_ACQUIRE);
            if (tick >= 2 && cur_recs > 0ULL && cur_recs == prev_recs) break;
            prev_recs = cur_recs;
            usleep(10000);
        }
        if (p_msptiActivityFlushAll) p_msptiActivityFlushAll(1U);
        __atomic_store_n(&g_mspti_win_start_ts, UINT64_MAX, __ATOMIC_RELEASE);
        __atomic_store_n(&g_capturing, 0U, __ATOMIC_RELEASE);
        if (p_msptiActivityGetNumDroppedRecords) {
            size_t dropped = 0;
            if (p_msptiActivityGetNumDroppedRecords(NULL, 0U, &dropped) == MSPTI_SUCCESS) {
                slot->mspti_records_dropped = dropped >= g_dropped_baseline ? (dropped - g_dropped_baseline) : dropped;
            }
        }
        write_gear1_worker_json(g_shm->header.output_dir, (int)g_pid, g_seen_generation, slot);
        __atomic_store_n(&slot->worker_state, slot->last_error_code == 0 ? WORKER_DONE : WORKER_ERROR, __ATOMIC_RELEASE);
        return;
    }

    __atomic_store_n(&g_capturing, 0U, __ATOMIC_RELEASE);
    if (g_prof_cfg) {
        aclError rc = p_aclprofStop ? p_aclprofStop(g_prof_cfg) : 0;
        if (p_aclprofDestroyConfig) p_aclprofDestroyConfig(g_prof_cfg);
        g_prof_cfg = NULL;
        if (p_aclprofFinalize) p_aclprofFinalize();
        if (rc != 0) {
            slot->last_error_code = (int32_t)rc;
            snprintf(slot->error_msg, sizeof(slot->error_msg), "aclprofStop failed rc=%d", (int)rc);
            __atomic_store_n(&slot->worker_state, WORKER_ERROR, __ATOMIC_RELEASE);
            return;
        }
    }
    snprintf(slot->artifact_path, sizeof(slot->artifact_path), "%s", g_prof_worker_dir);
    __atomic_store_n(&slot->summary_written, 1U, __ATOMIC_RELEASE);
    __atomic_store_n(&slot->worker_state, WORKER_DONE, __ATOMIC_RELEASE);
}

static void sync_session_generation_locked(MindieWorkerSlot *slot) {
    uint64_t gen = __atomic_load_n(&g_shm->header.generation, __ATOMIC_ACQUIRE);
    if (gen != g_seen_generation) {
        if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) {
            stop_capture_locked(slot, NULL);
        }
        g_seen_generation = gen;
        g_step_ring_count = 0U;
        g_step_ring_pos = 0U;
        slot->summary_written = 0U;
        slot->last_error_code = 0;
        slot->error_msg[0] = '\0';
        slot->artifact_path[0] = '\0';
        slot->captured_steps = 0ULL;
        uint32_t phase = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
        __atomic_store_n(&slot->worker_state, phase == PHASE_STANDBY ? WORKER_IDLE : WORKER_WARMUP, __ATOMIC_RELEASE);
    }
}

static int evaluate_steady_gate_locked(MindieWorkerSlot *slot) {
    if (slot->active_graph_captures > 0U) return 0;
    uint32_t min_warm = g_shm->header.min_warmup_steps;
    uint32_t win_steps = g_shm->header.steady_window_steps;
    if (win_steps == 0U) win_steps = 1U;
    if (win_steps > MINDIE_MAX_WINDOW_STEPS) win_steps = MINDIE_MAX_WINDOW_STEPS;
    if (slot->total_steps < (uint64_t)(min_warm + win_steps)) return 0;
    if (g_shm->header.require_zero_alloc_steps &&
        slot->alloc_calls_total > 0ULL &&
        (slot->total_steps - slot->last_alloc_step) < (uint64_t)win_steps) {
        return 0;
    }
    if (g_step_ring_count < win_steps) return 0;

    double sum = 0.0;
    for (uint32_t i = 0; i < win_steps; ++i) {
        uint32_t idx = (g_step_ring_pos + MINDIE_MAX_WINDOW_STEPS - 1U - i) % MINDIE_MAX_WINDOW_STEPS;
        sum += (double)g_step_durations_ring[idx];
    }
    double mean = sum / (double)win_steps;
    if (mean <= 0.0) return 0;
    double var_sum = 0.0;
    for (uint32_t i = 0; i < win_steps; ++i) {
        uint32_t idx = (g_step_ring_pos + MINDIE_MAX_WINDOW_STEPS - 1U - i) % MINDIE_MAX_WINDOW_STEPS;
        double diff = (double)g_step_durations_ring[idx] - mean;
        var_sum += diff * diff;
    }
    uint64_t cv_ppm = (uint64_t)((sqrt(var_sum / (double)win_steps) / mean) * 1000000.0);
    slot->window_mean_ns = (uint64_t)mean;
    slot->window_cv_ppm = cv_ppm;

    uint32_t max_cv = g_shm->header.max_cv_ppm;
    if (max_cv > 0U && cv_ppm > (uint64_t)max_cv) return 0;
    return 1;
}

static void on_step_boundary(aclrtStream stream) {
    if (!g_shm) return;
    pthread_mutex_lock(&g_lock);
    MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
    if (!slot) { pthread_mutex_unlock(&g_lock); return; }
    sync_session_generation_locked(slot);
    if (slot->active_graph_captures > 0U) { pthread_mutex_unlock(&g_lock); return; }

    uint64_t now = mono_ns();
    if (slot->last_step_ns > 0ULL) {
        uint64_t dt = now >= slot->last_step_ns ? (now - slot->last_step_ns) : 0ULL;
        if (dt < g_shm->header.min_step_interval_ns && !g_explicit_step_mode && slot->graph_replays_total == 0ULL) {
            pthread_mutex_unlock(&g_lock);
            return;
        }
        slot->last_step_duration_ns = dt;
        g_step_durations_ring[g_step_ring_pos] = dt;
        g_step_ring_pos = (g_step_ring_pos + 1U) % MINDIE_MAX_WINDOW_STEPS;
        if (g_step_ring_count < MINDIE_MAX_WINDOW_STEPS) g_step_ring_count++;
        if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) {
            slot->captured_steps += 1ULL;
            if (dt < slot->window_capture_min_step_ns) slot->window_capture_min_step_ns = dt;
            if (dt > slot->window_capture_max_step_ns) slot->window_capture_max_step_ns = dt;
            slot->window_capture_sum_step_ns += dt;
            uint64_t dt_us = dt / 1000ULL;
            slot->window_capture_sum_sq_us += (dt_us * dt_us);
        }
    }
    slot->last_step_ns = now;
    slot->total_steps += 1ULL;

    uint32_t phase = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
    uint32_t state = __atomic_load_n(&slot->worker_state, __ATOMIC_ACQUIRE);

    if (phase == PHASE_STOP_NOW || phase == PHASE_SHUTDOWN) {
        if (state == WORKER_CAPTURING) stop_capture_locked(slot, stream);
        pthread_mutex_unlock(&g_lock);
        return;
    }
    if (state == WORKER_CAPTURING) {
        uint32_t target = g_shm->header.target_capture_steps;
        if (target > 0U && slot->captured_steps >= (uint64_t)target) {
            stop_capture_locked(slot, stream);
        }
        pthread_mutex_unlock(&g_lock);
        return;
    }
    if (state == WORKER_DONE || state == WORKER_ERROR || phase == PHASE_STANDBY) {
        pthread_mutex_unlock(&g_lock);
        return;
    }
    if (state == WORKER_IDLE) {
        state = WORKER_WARMUP;
        __atomic_store_n(&slot->worker_state, WORKER_WARMUP, __ATOMIC_RELEASE);
    }
    if (phase == PHASE_START_NOW) {
        start_capture_locked(slot, stream);
        pthread_mutex_unlock(&g_lock);
        return;
    }
    if (phase == PHASE_ARMED) {
        if (evaluate_steady_gate_locked(slot)) {
            if (g_shm->header.control_mode == MODE_AUTONOMOUS) {
                start_capture_locked(slot, stream);
            } else {
                __atomic_store_n(&slot->worker_state, WORKER_GATE_READY, __ATOMIC_RELEASE);
            }
        } else if (state == WORKER_GATE_READY) {
            __atomic_store_n(&slot->worker_state, WORKER_WARMUP, __ATOMIC_RELEASE);
        }
    }
    pthread_mutex_unlock(&g_lock);
}

__attribute__((visibility("default")))
void mindie_capture_mark_step(void) {
    __atomic_store_n(&g_explicit_step_mode, 1U, __ATOMIC_RELEASE);
    on_step_boundary(NULL);
}

static aclError hook_aclrtSetDevice(int32_t device_id) {
    aclError rc = orig_aclrtSetDevice ? orig_aclrtSetDevice(device_id) : 0;
    if (rc == 0 && g_shm) {
        pthread_mutex_lock(&g_lock);
        g_logical_dev = device_id;
        g_physical_dev = map_physical_device(device_id);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(device_id);
        if (slot) {
            slot->logical_device_id = g_logical_dev;
            slot->physical_device_id = g_physical_dev;
        }
        pthread_mutex_unlock(&g_lock);
    }
    return rc;
}

static aclError hook_aclrtMalloc(void **dev_ptr, size_t size, aclrtMemMallocPolicy policy) {
    aclError rc = orig_aclrtMalloc ? orig_aclrtMalloc(dev_ptr, size, policy) : 0;
    if (rc == 0 && g_shm && g_slot_idx >= 0) {
        MindieWorkerSlot *slot = &g_shm->slots[g_slot_idx];
        __atomic_add_fetch(&slot->alloc_calls_total, 1ULL, __ATOMIC_RELAXED);
        __atomic_store_n(&slot->last_alloc_step, slot->total_steps, __ATOMIC_RELAXED);
        if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) {
            __atomic_add_fetch(&slot->allocs_in_window, 1ULL, __ATOMIC_RELAXED);
        }
    }
    return rc;
}

static aclError hook_ri_begin(aclrtStream stream, aclmdlRICaptureMode mode) {
    if (g_shm) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        if (slot) {
            slot->active_graph_captures += 1U;
            slot->graph_captures_total += 1ULL;
            if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) slot->graph_captures_in_window += 1ULL;
        }
        pthread_mutex_unlock(&g_lock);
    }
    return orig_ri_begin ? orig_ri_begin(stream, mode) : 0;
}

static aclError hook_ri_to_model_begin(aclrtStream stream, aclmdlRI *model_ri) {
    if (g_shm) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        if (slot) {
            slot->active_graph_captures += 1U;
            slot->graph_captures_total += 1ULL;
            if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) slot->graph_captures_in_window += 1ULL;
        }
        pthread_mutex_unlock(&g_lock);
    }
    return orig_ri_to_model_begin ? orig_ri_to_model_begin(stream, model_ri) : 0;
}

static aclError hook_ri_end(aclrtStream stream, aclmdlRI *model_ri) {
    aclError rc = orig_ri_end ? orig_ri_end(stream, model_ri) : 0;
    if (g_shm && g_slot_idx >= 0) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = &g_shm->slots[g_slot_idx];
        if (slot->active_graph_captures > 0U) slot->active_graph_captures -= 1U;
        pthread_mutex_unlock(&g_lock);
    }
    return rc;
}

static aclError hook_ri_exec_async(aclmdlRI model_ri, aclrtStream stream) {
    if (g_shm) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        uint32_t rps = g_shm->header.replays_per_step > 0U ? g_shm->header.replays_per_step : 1U;
        uint64_t sub = 0ULL;
        if (slot) {
            slot->graph_replays_total += 1ULL;
            g_replay_substep += 1ULL;
            sub = g_replay_substep;
        }
        pthread_mutex_unlock(&g_lock);
        if (!__atomic_load_n(&g_explicit_step_mode, __ATOMIC_ACQUIRE) &&
            sub > 0ULL && ((sub - 1ULL) % (uint64_t)rps) == 0ULL) {
            on_step_boundary(stream);
        }
    }
    return orig_ri_exec_async ? orig_ri_exec_async(model_ri, stream) : 0;
}

static aclError hook_ri_exec(aclmdlRI model_ri, int32_t timeout) {
    if (g_shm) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        uint32_t rps = g_shm->header.replays_per_step > 0U ? g_shm->header.replays_per_step : 1U;
        uint64_t sub = 0ULL;
        if (slot) {
            slot->graph_replays_total += 1ULL;
            g_replay_substep += 1ULL;
            sub = g_replay_substep;
        }
        pthread_mutex_unlock(&g_lock);
        if (!__atomic_load_n(&g_explicit_step_mode, __ATOMIC_ACQUIRE) &&
            sub > 0ULL && ((sub - 1ULL) % (uint64_t)rps) == 0ULL) {
            on_step_boundary(NULL);
        }
    }
    return orig_ri_exec ? orig_ri_exec(model_ri, timeout) : 0;
}

static aclError hook_aclrtSynchronizeStream(aclrtStream stream) {
    aclError rc = orig_aclrtSynchronizeStream ? orig_aclrtSynchronizeStream(stream) : 0;
    if (rc == 0 && g_shm && !__atomic_load_n(&g_explicit_step_mode, __ATOMIC_ACQUIRE)) {
        if (g_slot_idx < 0 || g_shm->slots[g_slot_idx].graph_replays_total == 0ULL) {
            on_step_boundary(stream);
        }
    }
    return rc;
}

static void install_acl_hooks(void) {
    fn_aclrtGetFunction_t get_fn = (fn_aclrtGetFunction_t)dlsym(RTLD_DEFAULT, "aclrtApiInjectionGetFunc");
    fn_aclrtSetFunction_t set_fn = (fn_aclrtSetFunction_t)dlsym(RTLD_DEFAULT, "aclrtApiInjectionSetFunc");
    orig_aclrtGetDevice = (fn_aclrtGetDevice_t)dlsym(RTLD_DEFAULT, "aclrtGetDevice");
    orig_aclrtSynchronizeDevice = (fn_aclrtSynchronizeDevice_t)dlsym(RTLD_DEFAULT, "aclrtSynchronizeDevice");
    if (!get_fn || !set_fn) return;

    aclrtApiFunc o = NULL, c = NULL;
    if (get_fn("aclrtSetDevice", &o, &c) == 0) {
        orig_aclrtSetDevice = (fn_aclrtSetDevice_t)(c ? c : o);
        set_fn("aclrtSetDevice", (aclrtApiFunc)hook_aclrtSetDevice);
    }
    o = NULL; c = NULL;
    if (get_fn("aclrtMalloc", &o, &c) == 0) {
        orig_aclrtMalloc = (fn_aclrtMalloc_t)(c ? c : o);
        set_fn("aclrtMalloc", (aclrtApiFunc)hook_aclrtMalloc);
    }
    o = NULL; c = NULL;
    if (get_fn("aclmdlRICaptureBegin", &o, &c) == 0) {
        orig_ri_begin = (fn_ri_begin_t)(c ? c : o);
        set_fn("aclmdlRICaptureBegin", (aclrtApiFunc)hook_ri_begin);
    }
    o = NULL; c = NULL;
    if (get_fn("aclmdlRICaptureToModelRIBegin", &o, &c) == 0) {
        orig_ri_to_model_begin = (fn_ri_to_model_begin_t)(c ? c : o);
        set_fn("aclmdlRICaptureToModelRIBegin", (aclrtApiFunc)hook_ri_to_model_begin);
    }
    o = NULL; c = NULL;
    if (get_fn("aclmdlRICaptureEnd", &o, &c) == 0) {
        orig_ri_end = (fn_ri_end_t)(c ? c : o);
        set_fn("aclmdlRICaptureEnd", (aclrtApiFunc)hook_ri_end);
    }
    o = NULL; c = NULL;
    if (get_fn("aclmdlRIExecuteAsync", &o, &c) == 0) {
        orig_ri_exec_async = (fn_ri_exec_async_t)(c ? c : o);
        set_fn("aclmdlRIExecuteAsync", (aclrtApiFunc)hook_ri_exec_async);
    }
    o = NULL; c = NULL;
    if (get_fn("aclmdlRIExecute", &o, &c) == 0) {
        orig_ri_exec = (fn_ri_exec_t)(c ? c : o);
        set_fn("aclmdlRIExecute", (aclrtApiFunc)hook_ri_exec);
    }
    o = NULL; c = NULL;
    if (get_fn("aclrtSynchronizeStream", &o, &c) == 0) {
        orig_aclrtSynchronizeStream = (fn_aclrtSynchronizeStream_t)(c ? c : o);
        set_fn("aclrtSynchronizeStream", (aclrtApiFunc)hook_aclrtSynchronizeStream);
    }
}

static void on_fork_child(void) {
    pthread_mutex_init(&g_lock, NULL);
    pthread_mutex_init(&g_agg_lock, NULL);
    g_pid = getpid();
    g_slot_idx = g_logical_dev = g_physical_dev = -1;
    g_seen_generation = g_replay_substep = 0;
    g_capturing = g_step_ring_count = g_step_ring_pos = g_mspti_activity_armed = 0U;
    g_mspti_win_start_ts = UINT64_MAX; g_mspti_win_end_ts = 1ULL;
    g_prof_cfg = NULL; g_mspti_sub = NULL;
    arm_mspti_activities_once();
}

__attribute__((constructor))
static void mindie_cann9_shim_init(void) {
    const char *shm_path = getenv("MINDIE_CAPTURE_SHM_PATH");
    if (!shm_path || !shm_path[0] || should_skip_process()) return;
    g_pid = getpid();
    int fd = open(shm_path, O_RDWR | O_CLOEXEC);
    if (fd < 0) return;
    struct stat st;
    if (fstat(fd, &st) != 0 || (size_t)st.st_size < sizeof(MindieCaptureShm)) { close(fd); return; }
    void *mapped = mmap(NULL, sizeof(MindieCaptureShm), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED) { close(fd); return; }
    MindieCaptureShm *candidate = (MindieCaptureShm *)mapped;
    if (candidate->header.magic != MINDIE_CAPTURE_MAGIC ||
        candidate->header.abi_version != MINDIE_CAPTURE_ABI_VERSION) {
        munmap(mapped, sizeof(MindieCaptureShm));
        close(fd);
        return;
    }
    g_shm_fd = fd;
    g_shm = candidate;
    pthread_atfork(NULL, NULL, on_fork_child);
    install_acl_hooks();
    arm_mspti_activities_once();
}

__attribute__((destructor))
static void mindie_cann9_shim_fini(void) {
    if (g_shm && g_slot_idx >= 0) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = &g_shm->slots[g_slot_idx];
        if (slot->pid == (int32_t)g_pid) {
            if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) {
                stop_capture_locked(slot, NULL);
            } else {
                uint32_t st = __atomic_load_n(&slot->worker_state, __ATOMIC_ACQUIRE);
                uint32_t ph = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
                if ((st == WORKER_WARMUP || st == WORKER_GATE_READY) &&
                    (ph == PHASE_ARMED || ph == PHASE_START_NOW)) {
                    slot->last_error_code = -109;
                    snprintf(slot->error_msg, sizeof(slot->error_msg),
                             "worker pid=%d exited before capture window started", (int)g_pid);
                    __atomic_store_n(&slot->worker_state, WORKER_ERROR, __ATOMIC_RELEASE);
                }
            }
        }
        pthread_mutex_unlock(&g_lock);
    }
    if (g_shm) {
        munmap(g_shm, sizeof(MindieCaptureShm));
        g_shm = NULL;
    }
    if (g_shm_fd >= 0) {
        close(g_shm_fd);
        g_shm_fd = -1;
    }
}
