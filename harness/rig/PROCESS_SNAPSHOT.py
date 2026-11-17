"""Read cgroup PID evidence without starting another process, including on EAGAIN."""
import pathlib,time

def snapshot(root=pathlib.Path('/sys/fs/cgroup'),proc=pathlib.Path('/proc/self/status')):
    result={'monotonic_ns':time.monotonic_ns(),'files':{}}
    # Docker's cgroup namespace normally exposes the container at the mount root.
    # Also support the legacy pids-controller mount, without guessing host paths.
    for base in (root,root/'pids'):
        for name in ('pids.current','pids.max','pids.peak','pids.events'):
            p=base/name
            try:result['files'][str(p)]=p.read_text().strip()
            except OSError as e:result['files'][str(p)]={'errno':e.errno,'error':str(e)}
    try:
        result['process_threads']=next((l.split(':',1)[1].strip() for l in proc.read_text().splitlines() if l.startswith('Threads:')),None)
    except OSError as e:result['process_threads']={'errno':e.errno,'error':str(e)}
    return result
