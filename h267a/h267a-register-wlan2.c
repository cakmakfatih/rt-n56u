/* SPDX-License-Identifier: GPL-2.0-only */
/* Fixed RAM-only OEM registration: br0/wlan2, unused LAN port index 6. */
typedef unsigned int word;
struct port_config { char name[16]; unsigned short index; unsigned char enable, pad; };
struct if_request { char name[16]; word data; unsigned char pad[12]; };
typedef char require_port_size[sizeof(struct port_config) == 20 ? 1 : -1];
typedef char require_ifreq_size[sizeof(struct if_request) == 32 ? 1 : -1];
static struct port_config config = { "wlan2", 6, 1, 0 };
static word arguments[4] = { 106, (word)&config, 0, 0 };
static struct if_request request = { "br0", (word)arguments, { 0 } };

static inline int syscall3(word number, word first, word second, word third)
{
    register word result __asm__("$2") = number;
    register word a0 __asm__("$4") = first;
    register word a1 __asm__("$5") = second;
    register word a2 __asm__("$6") = third;
    register word failed __asm__("$7");
    __asm__ volatile("syscall" : "+r"(result), "=r"(failed)
                     : "r"(a0), "r"(a1), "r"(a2) : "memory");
    return failed ? -(int)result : (int)result;
}

void _start(void)
{
    int fd = syscall3(4183, 2, 2, 0);
    int status = 1;
    if (fd >= 0) {
        status = syscall3(4054, (word)fd, 0x89f0, (word)&request) < 0 ? 2 : 0;
        syscall3(4006, (word)fd, 0, 0);
    }
    syscall3(4001, (word)status, 0, 0);
    for (;;) { }
}
