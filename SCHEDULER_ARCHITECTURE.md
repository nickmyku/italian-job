# Scheduler Architecture - Why 1 Worker?

## The Problem

You asked: **"Does the number of workers need to be limited to 1 to prevent scheduler conflicts?"**

**Short answer:** With the current setup (app.py), **YES**. But there's a better way for scalability.

## Understanding the Issue

### How Gunicorn Workers Work
- Each Gunicorn worker is a **separate operating system process**
- Each process has its own **independent memory space**
- Python global variables are **NOT shared** between processes

### Current Scheduler Singleton Check

In `scheduler.py` lines 64-67:
```python
# Prevent multiple scheduler instances (important for Flask reloader)
if _scheduler is not None and _scheduler.running:
    print("Scheduler already running. Skipping start.")
    return _scheduler
```

**This only prevents multiple schedulers WITHIN one process!**

### What Happens with Multiple Workers

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Worker 1      │     │   Worker 2      │     │   Worker 3      │
│   (Process A)   │     │   (Process B)   │     │   (Process C)   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ _scheduler=None │     │ _scheduler=None │     │ _scheduler=None │
│      ↓          │     │      ↓          │     │      ↓          │
│ Starts Scheduler│     │ Starts Scheduler│     │ Starts Scheduler│
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ↓                       ↓                       ↓
   DB Write               DB Write                DB Write
   (duplicate!)           (duplicate!)            (duplicate!)
```

### Problems This Causes
1. ❌ **Duplicate database writes** - Each worker scrapes and saves data every 6 hours
2. ❌ **Screenshot file conflicts** - Multiple workers writing to same `current.bmp` file
3. ❌ **Wasted resources** - Running N identical schedulers doing the same work
4. ❌ **Unpredictable behavior** - Race conditions on shared resources

## Two Solutions

### Solution 1: Single Worker (Current - Simpler)

**Files used:** `app.py` + `gunicorn.conf.py` (workers=1)

**How it works:**
```
┌─────────────────────────────┐
│   Gunicorn Worker 1         │
│   - Handles HTTP requests   │
│   - Runs scheduler          │
│   - Updates DB every 6h     │
│   - Takes screenshots       │
└─────────────────────────────┘
```

**Pros:**
- ✅ Simple to deploy (one command)
- ✅ No duplicate updates
- ✅ Less resource usage
- ✅ Works immediately

**Cons:**
- ❌ Limited to 1 process (can't handle high traffic)
- ❌ No horizontal scaling
- ❌ If worker crashes, no requests handled until restart

**Best for:**
- Low to medium traffic
- Simple deployments
- Development/testing
- Single-server setups

### Solution 2: Multi-Worker with Separate Scheduler (Better for Scale)

**Files used:** `app_no_scheduler.py` + `worker.py` + `gunicorn.conf.py` (workers=N)

**How it works:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Gunicorn        │     │ Gunicorn        │     │ Gunicorn        │
│ Worker 1        │     │ Worker 2        │     │ Worker 3        │
│ (HTTP only)     │     │ (HTTP only)     │     │ (HTTP only)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ↓                       ↓                       ↓
        └───────────────────────┴───────────────────────┘
                                │
                                │ Handle HTTP requests
                                ↓
                    ┌───────────────────────┐
                    │  Separate Process     │
                    │  worker.py            │
                    │  - Runs scheduler     │
                    │  - Updates DB         │
                    │  - Screenshots        │
                    └───────────────────────┘
```

**Pros:**
- ✅ Multiple workers handle more traffic
- ✅ Better resource utilization
- ✅ Horizontal scalability
- ✅ If one web worker crashes, others continue
- ✅ Only ONE scheduler running

**Cons:**
- ❌ More complex setup (2 processes to manage)
- ❌ Need process manager (systemd, supervisor, pm2)
- ❌ More resource usage (more workers)

**Best for:**
- Production environments
- High traffic loads
- Multi-core servers
- When you need reliability/redundancy

## Deployment Commands

### Single Worker
```bash
# Simple - Just one command
gunicorn -c gunicorn.conf.py app:app
```

### Multi-Worker
```bash
# 1. Edit gunicorn.conf.py - uncomment multi-worker line
# workers = multiprocessing.cpu_count() * 2 + 1

# 2. Start scheduler worker (background)
python3 worker.py &

# 3. Start Gunicorn with multiple workers
gunicorn -c gunicorn.conf.py app_no_scheduler:app
```

### With Process Manager (Production)
```bash
# systemd example
sudo systemctl start ship-tracker-worker   # Starts worker.py
sudo systemctl start ship-tracker-web      # Starts gunicorn
```

## Why Can't We Make It Smarter?

**Could we use file locking or database flags to prevent duplicates?**

Yes, but it adds complexity:
- Distributed locks (Redis, file locks)
- Database semaphores
- More failure modes
- Latency overhead

**The separate worker process is cleaner because:**
- Clear separation of concerns
- Scheduler runs once, guaranteed
- Web workers are stateless
- Easy to monitor and restart independently
- Standard production pattern

## Recommendation

| Your Situation | Use This |
|----------------|----------|
| Just starting, low traffic | Single worker (app.py) |
| Expecting growth | Multi-worker (app_no_scheduler.py + worker.py) |
| High traffic now | Multi-worker |
| Multiple servers | Multi-worker (run worker.py on one server only) |
| Kubernetes/Docker | Multi-worker (scheduler as separate pod/container) |

## TL;DR

**Yes, you need 1 worker with `app.py`** because Python's global variables don't prevent cross-process duplicates.

**But you can scale with `app_no_scheduler.py` + `worker.py`** by running the scheduler in a separate process.

Current PR keeps it simple with 1 worker, but includes the multi-worker option for when you need to scale! 🚀
