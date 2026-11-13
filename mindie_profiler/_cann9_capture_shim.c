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
 *   - WorkerSlot reservation preserves claimed == 1 across zero-initialization
 *     and publishes acked_generation atomically per session generation.
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
#include <math.h>
#include <signal.h>
#include <sys/mman.h>
#include <sys/stat.h>
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

static int g_shm_fd = -1;
static pid_t g_pid = 0;
static int32_t g_logical_dev = -1, g_physical_dev = -1;
static uint64_t g_seen_generation = 0, g_overflow_reported_gen = 0ULL, g_gen_start_step = 0ULL;
static uint32_t g_explicit_step_mode = 0, g_seen_graph_replay = 0U;
static uint32_t g_group_replay_idx = 0U, g_pending_replay_step = 0U;
static uint32_t g_pending_multi_stream = 0U, g_post_replay_sync_budget = 0U;
static aclrtStream g_pending_replay_stream = NULL;
static __thread uint32_t g_in_shim_sync = 0U;
static volatile uint32_t g_capturing = 0;
static uint64_t g_step_durations_ring[MINDIE_MAX_WINDOW_STEPS];
static uint32_t g_step_ring_count = 0, g_step_ring_pos = 0;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;

static fn_aclrtSetDevice_t orig_aclrtSetDevice;
static fn_aclrtGetDevice_t orig_aclrtGetDevice;
static fn_aclrtSynchronizeStream_t orig_aclrtSynchronizeStream;
static fn_aclrtSynchronizeDevice_t orig_aclrtSynchronizeDevice;
static fn_aclrtMalloc_t orig_aclrtMalloc;
static fn_ri_begin_t orig_ri_begin;
static fn_ri_to_model_begin_t orig_ri_to_model_begin;
static fn_ri_end_t orig_ri_end;
static fn_ri_exec_async_t orig_ri_exec_async;
static fn_ri_exec_t orig_ri_exec;
static void *g_msprof_dl;
static aclprofConfig *g_prof_cfg;
static fn_aclprofInit_t p_aclprofInit;
static fn_aclprofFinalize_t p_aclprofFinalize;
static fn_aclprofCreateConfig_t p_aclprofCreateConfig;
static fn_aclprofDestroyConfig_t p_aclprofDestroyConfig;
static fn_aclprofStart_t p_aclprofStart;
static fn_aclprofStop_t p_aclprofStop;
static char g_prof_worker_dir[688];

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
    if (g_logical_dev < 0) return NULL;
    for (uint32_t i = 0; i < MINDIE_MAX_WORKERS; ++i) {
        MindieWorkerSlot *slot = &g_shm->slots[i];
        uint32_t expected = 0U;
        if (__atomic_compare_exchange_n(&slot->claimed, &expected, 1U, 0, __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) {
            memset(((char *)slot) + offsetof(MindieWorkerSlot, pid), 0,
                   sizeof(*slot) - offsetof(MindieWorkerSlot, pid));
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
    uint64_t cur_gen = __atomic_load_n(&g_shm->header.generation, __ATOMIC_ACQUIRE);
    for (uint32_t i = 0; i < MINDIE_MAX_WORKERS; ++i) {
        MindieWorkerSlot *slot = &g_shm->slots[i];
        int32_t old_pid = slot->pid;
        if (__atomic_load_n(&slot->claimed, __ATOMIC_ACQUIRE) == 2U &&
            slot->acked_generation != cur_gen &&
            old_pid > 0 && kill((pid_t)old_pid, 0) != 0 && errno == ESRCH) {
            uint32_t expected = 2U;
            if (__atomic_compare_exchange_n(&slot->claimed, &expected, 1U, 0, __ATOMIC_ACQ_REL, __ATOMIC_RELAXED)) {
                if (slot->pid != old_pid) {
                    __atomic_store_n(&slot->claimed, 2U, __ATOMIC_RELEASE);
                    continue;
                }
                memset(((char *)slot) + offsetof(MindieWorkerSlot, pid), 0,
                       sizeof(*slot) - offsetof(MindieWorkerSlot, pid));
                slot->pid = (int32_t)g_pid;
                slot->logical_device_id = g_logical_dev;
                slot->physical_device_id = g_physical_dev;
                slot->worker_state = WORKER_IDLE;
                __atomic_store_n(&slot->claimed, 2U, __ATOMIC_RELEASE);
                g_slot_idx = (int)i;
                return slot;
            }
        }
    }
    uint64_t report_tag = cur_gen + 1ULL;
    if (g_overflow_reported_gen != report_tag) {
        g_overflow_reported_gen = report_tag;
        __atomic_add_fetch(&g_shm->header.slot_overflow_count, 1U, __ATOMIC_ACQ_REL);
    }
    return NULL;
}

static inline int is_step_tracking_active_locked(const MindieWorkerSlot *slot) {
    if (!slot || !g_shm) return 0;
    uint32_t st = __atomic_load_n(&slot->worker_state, __ATOMIC_ACQUIRE);
    if (st == WORKER_CAPTURING || __atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) return 1;
    if (st == WORKER_DONE || st == WORKER_ERROR) return 0;
    uint32_t ph = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
    return (ph == PHASE_ARMED || ph == PHASE_START_NOW) ? 1 : 0;
}

static void sync_device_or_stream_locked(aclrtStream stream) {
    g_in_shim_sync = 1U;
    if (stream != NULL && orig_aclrtSynchronizeStream) orig_aclrtSynchronizeStream(stream);
    else if (orig_aclrtSynchronizeDevice) orig_aclrtSynchronizeDevice();
    else if (orig_aclrtSynchronizeStream) orig_aclrtSynchronizeStream(NULL);
    g_in_shim_sync = 0U;
}

static inline int fail_slot_locked(MindieWorkerSlot *slot, int32_t code, const char *msg, int arg) {
    slot->last_error_code = code;
    snprintf(slot->error_msg, sizeof(slot->error_msg), msg, arg);
    __atomic_store_n(&slot->worker_state, WORKER_ERROR, __ATOMIC_RELEASE);
    return -1;
}

static int start_capture_locked(MindieWorkerSlot *slot, aclrtStream stream) {
    sync_device_or_stream_locked(stream);
    if (g_shm->header.gear == GEAR_FAST_MSPTI) {
        int mspti_err = 0;
        if (arm_mspti_activities_once(&mspti_err, slot->error_msg, sizeof(slot->error_msg)) != 0) {
            slot->last_error_code = mspti_err ? mspti_err : -106;
            __atomic_store_n(&slot->worker_state, WORKER_ERROR, __ATOMIC_RELEASE);
            return -1;
        }
        __atomic_store_n(&g_mspti_win_start_ts, UINT64_MAX, __ATOMIC_RELEASE);
        if (p_msptiActivityFlushAll) p_msptiActivityFlushAll(1U);
        size_t discarded = 0;
        if (p_msptiActivityGetNumDroppedRecords) {
            (void)p_msptiActivityGetNumDroppedRecords(NULL, 0U, &discarded);
        }
        pthread_mutex_lock(&g_agg_lock);
        memset(g_agg_table, 0, sizeof(g_agg_table));
        g_interval_count = g_interval_overflow = g_agg_overflow = 0U;
        g_agg_dropped_records = slot->mspti_records_captured = slot->mspti_records_dropped = 0ULL;
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
        if (!p_aclprofInit || !p_aclprofCreateConfig || !p_aclprofStart || !p_aclprofStop)
            return fail_slot_locked(slot, -101, "cannot resolve aclprof symbols from libmsprofiler.so", 0);
        int32_t ldev = slot->logical_device_id >= 0 ? slot->logical_device_id : 0;
        int32_t pdev = slot->physical_device_id >= 0 ? slot->physical_device_id : ldev;
        int n_dir = snprintf(
            g_prof_worker_dir, sizeof(g_prof_worker_dir), "%s/rank_%d_device_%d_pid%d_gen%llu",
            g_shm->header.output_dir, g_slot_idx >= 0 ? g_slot_idx : 0, (int)pdev,
            (int)g_pid, (unsigned long long)g_seen_generation);
        if (n_dir < 0 || (size_t)n_dir >= sizeof(g_prof_worker_dir))
            return fail_slot_locked(slot, -105, "Gear-2 output directory path truncated", 0);
        mkdir(g_prof_worker_dir, 0755);
        aclError rc = p_aclprofInit(g_prof_worker_dir, (size_t)n_dir);
        if (rc != 0) return fail_slot_locked(slot, (int32_t)rc, "aclprofInit failed rc=%d", (int)rc);
        uint32_t dev_arr[1] = {(uint32_t)ldev};
        uint64_t mask = g_shm->header.aclprof_data_type_mask
                            ? g_shm->header.aclprof_data_type_mask : DEFAULT_GEAR2_DATA_MASK;
        g_prof_cfg = p_aclprofCreateConfig(
            dev_arr, 1U, (aclprofAicoreMetrics)g_shm->header.aclprof_aicore_metrics, NULL, mask);
        if (!g_prof_cfg) {
            p_aclprofFinalize();
            return fail_slot_locked(slot, -102, "aclprofCreateConfig returned NULL", 0);
        }
        rc = p_aclprofStart(g_prof_cfg);
        if (rc != 0) {
            p_aclprofDestroyConfig(g_prof_cfg);
            g_prof_cfg = NULL;
            p_aclprofFinalize();
            return fail_slot_locked(slot, (int32_t)rc, "aclprofStart failed rc=%d", (int)rc);
        }
    }
    slot->capture_start_mono_ns = slot->last_step_ns = mono_ns();
    slot->capture_start_step = slot->total_steps;
    slot->captured_steps = slot->graph_captures_in_window = slot->allocs_in_window = 0ULL;
    slot->window_capture_min_step_ns = UINT64_MAX;
    slot->window_capture_max_step_ns = slot->window_capture_sum_step_ns = slot->window_capture_sum_sq_us = 0ULL;
    __atomic_store_n(&g_capturing, 1U, __ATOMIC_RELEASE);
    __atomic_store_n(&slot->worker_state, WORKER_CAPTURING, __ATOMIC_RELEASE);
    return 0;
}

static void stop_capture_locked(MindieWorkerSlot *slot, aclrtStream stream) {
    if (!__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) return;
    sync_device_or_stream_locked(stream);
    slot->capture_end_mono_ns = mono_ns();
    if (g_shm->header.gear == GEAR_FAST_MSPTI) {
        uint64_t ts_end = 0ULL, entry_recs = __atomic_load_n(&slot->mspti_records_captured, __ATOMIC_ACQUIRE);
        uint64_t prev_recs = entry_recs;
        if (p_msptiGetTimestamp) p_msptiGetTimestamp(&ts_end);
        __atomic_store_n(&g_mspti_win_end_ts, ts_end > 0ULL ? ts_end : (UINT64_MAX - 1ULL), __ATOMIC_RELEASE);
        for (int tick = 0; tick < 20; ++tick) {
            if (p_msptiActivityFlushAll) p_msptiActivityFlushAll(1U);
            uint64_t cur_recs = __atomic_load_n(&slot->mspti_records_captured, __ATOMIC_ACQUIRE);
            if (tick >= 2 && cur_recs > entry_recs && cur_recs == prev_recs) break;
            if (tick >= 8 && cur_recs > 0ULL && cur_recs == prev_recs) break;
            prev_recs = cur_recs;
            usleep(10000);
        }
        if (p_msptiActivityFlushAll) p_msptiActivityFlushAll(1U);
        __atomic_store_n(&g_mspti_win_start_ts, UINT64_MAX, __ATOMIC_RELEASE);
        __atomic_store_n(&g_capturing, 0U, __ATOMIC_RELEASE);
        size_t dropped = 0;
        if (p_msptiActivityGetNumDroppedRecords &&
            p_msptiActivityGetNumDroppedRecords(NULL, 0U, &dropped) == MSPTI_SUCCESS) {
            slot->mspti_records_dropped = (uint64_t)dropped;
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
        if (rc != 0) { (void)fail_slot_locked(slot, (int32_t)rc, "aclprofStop failed rc=%d", (int)rc); return; }
    }
    int n_art = snprintf(slot->artifact_path, sizeof(slot->artifact_path), "%s", g_prof_worker_dir);
    if (n_art < 0 || (size_t)n_art >= sizeof(slot->artifact_path)) {
        (void)fail_slot_locked(slot, -105, "Gear-2 artifact_path truncated", 0);
        return;
    }
    __atomic_store_n(&slot->summary_written, 1U, __ATOMIC_RELEASE);
    __atomic_store_n(&slot->worker_state, WORKER_DONE, __ATOMIC_RELEASE);
}

static void record_step_interval_locked(MindieWorkerSlot *slot, uint64_t now) {
    if (slot->last_step_ns > 0ULL) {
        uint64_t dt = now >= slot->last_step_ns ? (now - slot->last_step_ns) : 0ULL;
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
}

static void finalize_pending_replay_locked(MindieWorkerSlot *slot) {
    if (!slot || !g_pending_replay_step) return;
    sync_device_or_stream_locked(g_pending_multi_stream ? NULL : g_pending_replay_stream);
    g_pending_replay_step = g_pending_multi_stream = g_group_replay_idx = g_post_replay_sync_budget = 0U;
    g_pending_replay_stream = NULL;
    record_step_interval_locked(slot, mono_ns());
}

static void sync_session_generation_locked(MindieWorkerSlot *slot) {
    if (!slot || !g_shm) return;
    uint64_t gen = __atomic_load_n(&g_shm->header.generation, __ATOMIC_ACQUIRE);
    if (gen != g_seen_generation) {
        if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) {
            finalize_pending_replay_locked(slot);
            stop_capture_locked(slot, NULL);
        }
        g_seen_generation = gen;
        g_gen_start_step = slot->total_steps;
        g_seen_graph_replay = 0U;
        g_group_replay_idx = g_pending_replay_step = g_pending_multi_stream = g_post_replay_sync_budget = 0U;
        g_pending_replay_stream = NULL;
        g_step_ring_count = g_step_ring_pos = 0U;
        slot->last_step_ns = 0ULL;
        slot->summary_written = 0U;
        slot->last_error_code = 0;
        slot->error_msg[0] = '\0';
        slot->artifact_path[0] = '\0';
        slot->capture_start_mono_ns = slot->capture_end_mono_ns = 0ULL;
        slot->capture_start_step = slot->captured_steps = 0ULL;
        slot->graph_captures_in_window = slot->allocs_in_window = 0ULL;
        slot->mspti_records_captured = slot->mspti_records_dropped = 0ULL;
        uint32_t phase = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
        __atomic_store_n(&slot->worker_state, phase == PHASE_STANDBY ? WORKER_IDLE : WORKER_WARMUP, __ATOMIC_RELEASE);
        __atomic_store_n(&slot->acked_generation, gen, __ATOMIC_RELEASE);
    }
}

static int evaluate_steady_gate_locked(MindieWorkerSlot *slot) {
    if (slot->active_graph_captures > 0U) return 0;
    uint32_t min_warm = g_shm->header.min_warmup_steps;
    uint32_t win_steps = g_shm->header.steady_window_steps;
    if (win_steps == 0U) win_steps = 1U;
    if (win_steps > MINDIE_MAX_WINDOW_STEPS) win_steps = MINDIE_MAX_WINDOW_STEPS;
    uint64_t gen_steps = slot->total_steps >= g_gen_start_step ? (slot->total_steps - g_gen_start_step) : slot->total_steps;
    if (gen_steps < (uint64_t)(min_warm + win_steps)) return 0;
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

static void account_step_locked(MindieWorkerSlot *slot, aclrtStream stream, uint64_t ts_override_ns, int from_replay) {
    if (!slot || slot->active_graph_captures > 0U) return;
    uint32_t phase = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
    uint32_t state = __atomic_load_n(&slot->worker_state, __ATOMIC_ACQUIRE);
    if (phase == PHASE_STOP_NOW || phase == PHASE_SHUTDOWN || phase == PHASE_STANDBY) {
        if (state == WORKER_CAPTURING) stop_capture_locked(slot, stream);
        else if (phase == PHASE_STANDBY && (state == WORKER_WARMUP || state == WORKER_GATE_READY))
            __atomic_store_n(&slot->worker_state, WORKER_IDLE, __ATOMIC_RELEASE);
        return;
    }
    if (state == WORKER_DONE || state == WORKER_ERROR) return;
    uint64_t now = ts_override_ns > 0ULL ? ts_override_ns : mono_ns();
    if (slot->last_step_ns > 0ULL) {
        uint64_t dt = now >= slot->last_step_ns ? (now - slot->last_step_ns) : 0ULL;
        if (dt < g_shm->header.min_step_interval_ns && !g_explicit_step_mode && !from_replay) return;
    }
    g_pending_replay_step = g_pending_multi_stream = 0U;
    g_pending_replay_stream = NULL;
    record_step_interval_locked(slot, now);

    if (state == WORKER_CAPTURING) {
        uint32_t target = g_shm->header.target_capture_steps;
        if (target > 0U && slot->captured_steps >= (uint64_t)target) stop_capture_locked(slot, stream);
        return;
    }
    if (state == WORKER_IDLE) {
        state = WORKER_WARMUP;
        __atomic_store_n(&slot->worker_state, WORKER_WARMUP, __ATOMIC_RELEASE);
    }
    if (phase == PHASE_START_NOW) {
        start_capture_locked(slot, stream);
        return;
    }
    if (phase == PHASE_ARMED) {
        if (evaluate_steady_gate_locked(slot)) {
            if (g_shm->header.control_mode == MODE_AUTONOMOUS) start_capture_locked(slot, stream);
            else __atomic_store_n(&slot->worker_state, WORKER_GATE_READY, __ATOMIC_RELEASE);
        } else if (state == WORKER_GATE_READY) {
            __atomic_store_n(&slot->worker_state, WORKER_WARMUP, __ATOMIC_RELEASE);
        }
    }
}

static void on_step_boundary_ex(aclrtStream stream, uint64_t ts_override_ns, int from_replay) {
    if (!g_shm) return;
    pthread_mutex_lock(&g_lock);
    MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
    if (slot) {
        sync_session_generation_locked(slot);
        account_step_locked(slot, stream, ts_override_ns, from_replay);
    }
    pthread_mutex_unlock(&g_lock);
}

__attribute__((visibility("default")))
void mindie_capture_mark_step(void) {
    __atomic_store_n(&g_explicit_step_mode, 1U, __ATOMIC_RELEASE);
    on_step_boundary_ex(NULL, 0ULL, 0);
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
            sync_session_generation_locked(slot);
        }
        arm_mspti_activities_once(NULL, NULL, 0);
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

static int record_graph_capture_begin(int *in_win_out) {
    *in_win_out = 0;
    if (!g_shm) return 0;
    int recorded = 0;
    pthread_mutex_lock(&g_lock);
    MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
    arm_mspti_activities_once(NULL, NULL, 0);
    if (slot) {
        sync_session_generation_locked(slot);
        slot->active_graph_captures += 1U;
        slot->graph_captures_total += 1ULL;
        if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) {
            slot->graph_captures_in_window += 1ULL;
            *in_win_out = 1;
        }
        recorded = 1;
    }
    pthread_mutex_unlock(&g_lock);
    return recorded;
}

static void rollback_graph_capture_begin(int in_win) {
    if (!g_shm || g_slot_idx < 0) return;
    pthread_mutex_lock(&g_lock);
    MindieWorkerSlot *slot = &g_shm->slots[g_slot_idx];
    if (slot->active_graph_captures > 0U) slot->active_graph_captures -= 1U;
    if (slot->graph_captures_total > 0ULL) slot->graph_captures_total -= 1ULL;
    if (in_win && slot->graph_captures_in_window > 0ULL) slot->graph_captures_in_window -= 1ULL;
    pthread_mutex_unlock(&g_lock);
}

static aclError hook_ri_begin(aclrtStream stream, aclmdlRICaptureMode mode) {
    int in_win = 0, rec = record_graph_capture_begin(&in_win);
    aclError rc = orig_ri_begin ? orig_ri_begin(stream, mode) : 0;
    if (rc != 0 && rec) rollback_graph_capture_begin(in_win);
    return rc;
}

static aclError hook_ri_to_model_begin(aclrtStream stream, aclmdlRI *model_ri) {
    int in_win = 0, rec = record_graph_capture_begin(&in_win);
    aclError rc = orig_ri_to_model_begin ? orig_ri_to_model_begin(stream, model_ri) : 0;
    if (rc != 0 && rec) rollback_graph_capture_begin(in_win);
    return rc;
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

static uint32_t prepare_replay_pre_launch_locked(MindieWorkerSlot *slot, aclrtStream stream) {
    sync_session_generation_locked(slot);
    uint32_t rps = g_shm->header.replays_per_step > 0U ? g_shm->header.replays_per_step : 1U;
    slot->graph_replays_total += 1ULL;
    g_post_replay_sync_budget = 0U;
    if (slot->active_graph_captures == 0U) g_seen_graph_replay = 1U;
    if (__atomic_load_n(&g_explicit_step_mode, __ATOMIC_ACQUIRE) || slot->active_graph_captures > 0U) return rps;
    if (!is_step_tracking_active_locked(slot)) {
        g_group_replay_idx = g_pending_replay_step = g_pending_multi_stream = 0U;
        g_pending_replay_stream = NULL;
        slot->last_step_ns = 0ULL;
        uint32_t ph0 = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
        uint32_t st0 = __atomic_load_n(&slot->worker_state, __ATOMIC_ACQUIRE);
        if (ph0 == PHASE_STANDBY && (st0 == WORKER_WARMUP || st0 == WORKER_GATE_READY))
            __atomic_store_n(&slot->worker_state, WORKER_IDLE, __ATOMIC_RELEASE);
        return rps;
    }
    if (g_group_replay_idx == 0U) {
        if (g_pending_replay_step) {
            aclrtStream pending_s = g_pending_multi_stream ? NULL : g_pending_replay_stream;
            sync_device_or_stream_locked(pending_s);
            g_pending_replay_step = g_pending_multi_stream = 0U;
            g_pending_replay_stream = NULL;
            account_step_locked(slot, pending_s, mono_ns(), 1);
        }
        uint32_t ph = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
        uint32_t st = __atomic_load_n(&slot->worker_state, __ATOMIC_ACQUIRE);
        if (ph == PHASE_STOP_NOW || ph == PHASE_SHUTDOWN || ph == PHASE_STANDBY) {
            if (st == WORKER_CAPTURING) stop_capture_locked(slot, stream);
        } else if (ph == PHASE_START_NOW && (st == WORKER_IDLE || st == WORKER_WARMUP || st == WORKER_GATE_READY)) {
            start_capture_locked(slot, stream);
        }
        if (is_step_tracking_active_locked(slot) && slot->last_step_ns == 0ULL) slot->last_step_ns = mono_ns();
    }
    return rps;
}

static aclError hook_ri_exec_async(aclmdlRI model_ri, aclrtStream stream) {
    uint32_t rps = 1U, tracked = 0U;
    if (g_shm && !g_in_shim_sync) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        if (slot) {
            rps = prepare_replay_pre_launch_locked(slot, stream);
            if (!__atomic_load_n(&g_explicit_step_mode, __ATOMIC_ACQUIRE) &&
                slot->active_graph_captures == 0U && is_step_tracking_active_locked(slot)) {
                tracked = 1U;
            }
        }
        pthread_mutex_unlock(&g_lock);
    }
    aclError rc = orig_ri_exec_async ? orig_ri_exec_async(model_ri, stream) : 0;
    if (rc == 0 && tracked && g_shm) {
        pthread_mutex_lock(&g_lock);
        if (g_group_replay_idx == 0U) { g_pending_replay_stream = stream; g_pending_multi_stream = 0U; }
        else if (stream != g_pending_replay_stream) g_pending_multi_stream = 1U;
        if (++g_group_replay_idx >= rps) { g_group_replay_idx = 0U; g_pending_replay_step = 1U; }
        pthread_mutex_unlock(&g_lock);
    }
    return rc;
}

static aclError hook_ri_exec(aclmdlRI model_ri, int32_t timeout) {
    uint32_t rps = 1U, tracked = 0U;
    if (g_shm && !g_in_shim_sync) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        if (slot) {
            rps = prepare_replay_pre_launch_locked(slot, NULL);
            if (!__atomic_load_n(&g_explicit_step_mode, __ATOMIC_ACQUIRE) &&
                slot->active_graph_captures == 0U && is_step_tracking_active_locked(slot)) tracked = 1U;
        }
        pthread_mutex_unlock(&g_lock);
    }
    aclError rc = orig_ri_exec ? orig_ri_exec(model_ri, timeout) : 0;
    if (rc == 0 && tracked && g_shm) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        if (++g_group_replay_idx >= rps) {
            g_group_replay_idx = g_pending_replay_step = g_pending_multi_stream = 0U;
            g_pending_replay_stream = NULL;
            g_post_replay_sync_budget = 1U;
            if (slot) { sync_session_generation_locked(slot); account_step_locked(slot, NULL, mono_ns(), 1); }
        }
        pthread_mutex_unlock(&g_lock);
    }
    return rc;
}

static aclError hook_aclrtSynchronizeStream(aclrtStream stream) {
    aclError rc = orig_aclrtSynchronizeStream ? orig_aclrtSynchronizeStream(stream) : 0;
    if (rc == 0 && g_shm && !g_in_shim_sync && !__atomic_load_n(&g_explicit_step_mode, __ATOMIC_ACQUIRE)) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        if (slot) {
            sync_session_generation_locked(slot);
            if (g_pending_replay_step) {
                if (!g_pending_multi_stream && stream == g_pending_replay_stream) {
                    g_pending_replay_step = 0U;
                    g_pending_replay_stream = NULL;
                    g_post_replay_sync_budget = 1U;
                    account_step_locked(slot, stream, mono_ns(), 1);
                }
            } else if (g_group_replay_idx > 0U) {
                /* Mid-group sync inside multi-segment replays_per_step */
            } else if (g_post_replay_sync_budget > 0U) {
                g_post_replay_sync_budget -= 1U;
            } else if (!g_seen_graph_replay && is_step_tracking_active_locked(slot)) {
                account_step_locked(slot, stream, 0ULL, 0);
            }
        }
        pthread_mutex_unlock(&g_lock);
    }
    return rc;
}

static aclError hook_aclrtSynchronizeDevice(void) {
    aclError rc = orig_aclrtSynchronizeDevice ? orig_aclrtSynchronizeDevice() : 0;
    if (rc == 0 && g_shm && !g_in_shim_sync && !__atomic_load_n(&g_explicit_step_mode, __ATOMIC_ACQUIRE)) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = ensure_worker_slot_locked(-1);
        if (slot) {
            sync_session_generation_locked(slot);
            if (g_pending_replay_step) {
                g_pending_replay_step = g_pending_multi_stream = 0U;
                g_pending_replay_stream = NULL;
                g_post_replay_sync_budget = 1U;
                account_step_locked(slot, NULL, mono_ns(), 1);
            } else if (g_group_replay_idx > 0U) {
                /* Mid-group sync inside multi-segment replays_per_step */
            } else if (g_post_replay_sync_budget > 0U) {
                g_post_replay_sync_budget -= 1U;
            } else if (!g_seen_graph_replay && is_step_tracking_active_locked(slot)) {
                account_step_locked(slot, NULL, 0ULL, 0);
            }
        }
        pthread_mutex_unlock(&g_lock);
    }
    return rc;
}

static void install_acl_hooks(void) {
    fn_aclrtGetFunction_t get_fn = (fn_aclrtGetFunction_t)dlsym(RTLD_DEFAULT, "aclrtApiInjectionGetFunc");
    fn_aclrtSetFunction_t set_fn = (fn_aclrtSetFunction_t)dlsym(RTLD_DEFAULT, "aclrtApiInjectionSetFunc");
    if (!get_fn || !set_fn) {
        const char *acl_so = getenv("MINDIE_CAPTURE_LIBASCENDCL");
        dlopen((acl_so && acl_so[0]) ? acl_so : "libascendcl.so", RTLD_NOW | RTLD_GLOBAL);
        get_fn = (fn_aclrtGetFunction_t)dlsym(RTLD_DEFAULT, "aclrtApiInjectionGetFunc");
        set_fn = (fn_aclrtSetFunction_t)dlsym(RTLD_DEFAULT, "aclrtApiInjectionSetFunc");
    }
    orig_aclrtGetDevice = (fn_aclrtGetDevice_t)dlsym(RTLD_DEFAULT, "aclrtGetDevice");
    orig_aclrtSynchronizeDevice = (fn_aclrtSynchronizeDevice_t)dlsym(RTLD_DEFAULT, "aclrtSynchronizeDevice");
    if (!get_fn || !set_fn) return;

    aclrtApiFunc o = NULL, c = NULL;
    if (get_fn("aclrtGetDevice", &o, &c) == 0 && (c || o)) orig_aclrtGetDevice = (fn_aclrtGetDevice_t)(c ? c : o);
#define BIND_ACL_HOOK(sym, orig_var, fn_type, hook_fn) \
    do { o = NULL; c = NULL; if (get_fn(sym, &o, &c) == 0 && (c || o)) { \
        orig_var = (fn_type)(c ? c : o); set_fn(sym, (aclrtApiFunc)(hook_fn)); \
    } } while (0)
    BIND_ACL_HOOK("aclrtSetDevice", orig_aclrtSetDevice, fn_aclrtSetDevice_t, hook_aclrtSetDevice);
    BIND_ACL_HOOK("aclrtMalloc", orig_aclrtMalloc, fn_aclrtMalloc_t, hook_aclrtMalloc);
    BIND_ACL_HOOK("aclmdlRICaptureBegin", orig_ri_begin, fn_ri_begin_t, hook_ri_begin);
    BIND_ACL_HOOK("aclmdlRICaptureToModelRIBegin", orig_ri_to_model_begin, fn_ri_to_model_begin_t, hook_ri_to_model_begin);
    BIND_ACL_HOOK("aclmdlRICaptureEnd", orig_ri_end, fn_ri_end_t, hook_ri_end);
    BIND_ACL_HOOK("aclmdlRIExecuteAsync", orig_ri_exec_async, fn_ri_exec_async_t, hook_ri_exec_async);
    BIND_ACL_HOOK("aclmdlRIExecute", orig_ri_exec, fn_ri_exec_t, hook_ri_exec);
    BIND_ACL_HOOK("aclrtSynchronizeStream", orig_aclrtSynchronizeStream, fn_aclrtSynchronizeStream_t, hook_aclrtSynchronizeStream);
    BIND_ACL_HOOK("aclrtSynchronizeDevice", orig_aclrtSynchronizeDevice, fn_aclrtSynchronizeDevice_t, hook_aclrtSynchronizeDevice);
#undef BIND_ACL_HOOK
}

static void on_fork_child(void) {
    pthread_mutex_init(&g_lock, NULL);
    pthread_mutex_init(&g_agg_lock, NULL);
    g_pid = getpid();
    g_slot_idx = g_logical_dev = g_physical_dev = -1;
    g_seen_generation = g_overflow_reported_gen = g_gen_start_step = 0ULL;
    g_seen_graph_replay = g_group_replay_idx = g_pending_replay_step = 0U;
    g_pending_multi_stream = g_post_replay_sync_budget = 0U;
    g_pending_replay_stream = NULL;
    g_capturing = g_step_ring_count = g_step_ring_pos = g_mspti_activity_armed = 0U;
    g_mspti_win_start_ts = UINT64_MAX; g_mspti_win_end_ts = 1ULL;
    g_prof_cfg = NULL; g_mspti_sub = NULL;
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
}

__attribute__((destructor))
static void mindie_cann9_shim_fini(void) {
    if (g_shm && g_slot_idx >= 0) {
        pthread_mutex_lock(&g_lock);
        MindieWorkerSlot *slot = &g_shm->slots[g_slot_idx];
        if (slot->pid == (int32_t)g_pid) {
            if (__atomic_load_n(&g_capturing, __ATOMIC_ACQUIRE)) {
                finalize_pending_replay_locked(slot);
                stop_capture_locked(slot, NULL);
            } else {
                uint64_t gen = __atomic_load_n(&g_shm->header.generation, __ATOMIC_ACQUIRE);
                uint32_t st = __atomic_load_n(&slot->worker_state, __ATOMIC_ACQUIRE);
                uint32_t ph = __atomic_load_n(&g_shm->header.desired_phase, __ATOMIC_ACQUIRE);
                if (slot->acked_generation == gen &&
                    (st == WORKER_WARMUP || st == WORKER_GATE_READY) &&
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
    if (g_shm) { munmap(g_shm, sizeof(MindieCaptureShm)); g_shm = NULL; }
    if (g_shm_fd >= 0) { close(g_shm_fd); g_shm_fd = -1; }
}
