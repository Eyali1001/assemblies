def get_free_memory() -> int:
    """Return amount of free memory, kilobytes"""
    with open('/proc/meminfo', 'r') as mem:
        free_memory = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                free_memory += int(sline[1])
        return free_memory


def protecc_ram(pctg: float = 0.5):
    """Limit RAM usage to at most some percentage of available RAM"""
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (int(get_free_memory() * 1024 * pctg), hard))
    except:  # noqa
        pass
