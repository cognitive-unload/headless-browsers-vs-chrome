"""Pure decisions for site observations; callers supply elapsed time explicitly."""
def paint_decision(page_ready, paint_ready, elapsed, pending_images):
    if not page_ready:
        return None
    if paint_ready:
        return dict(state='ready', paint_state='complete')
    if elapsed >= 15:
        return dict(state='ready', paint_state='incomplete', pending_images=pending_images,
                    note=f'ready, {pending_images} images still loading')
    return None

def process_growth(previous, current):
    return previous is not None and current is not None and current > previous

def current_pids(snapshot):
    value=snapshot.get('files',{}).get('/sys/fs/cgroup/pids.current')
    return int(value) if isinstance(value,str) and value.isdecimal() else None

def pids_limit(phase):
    if phase not in ('preflight','wpt','sites','speed','benchmark'):
        raise ValueError('unknown phase')
    return 1024 if phase in ('sites','speed') else 512

if __name__=='__main__':
    import sys
    print(pids_limit(sys.argv[1]))
