#pragma once


#if defined(_WIN32)


class MemPerfCounters
{
public:
    MemPerfCounters();
    ~MemPerfCounters();

    static unsigned long Get();
};


#else
#error "Unsupported platform"
#endif
