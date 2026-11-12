# SPDX-License-Identifier: GPL-2.0-only
"""Exercise the actual allocation function with isolated OS stubs."""
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).read_text()
start = source.index('PNET_DEV RtmpOSNetDevCreate(')
opening = source.index('{', start)
depth = 1
end = opening + 1
while depth:
    depth += (source[end] == '{') - (source[end] == '}')
    end += 1
function = source[start:end]
prefix = r'''
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#define INT_APCLI 0x100
#define IN
#define LINUX_VERSION_CODE 0x030400
#define KERNEL_VERSION(a,b,c) (((a)<<16)|((b)<<8)|(c))
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define DBGPRINT(level,args) ((void)0)
typedef int INT32; typedef unsigned UINT32; typedef int INT;
typedef char RTMP_STRING; typedef void VOID; typedef void *PVOID;
struct net_device_ops { int unused; };
struct net_device { char name[16]; struct net_device_ops *netdev_ops; };
typedef struct net_device *PNET_DEV;
static int occupied, fail_alloc;
static int RtmpOSNetDevAlloc(PNET_DEV *dev, int bytes) {
    if(fail_alloc) return 1;
    *dev=calloc(1,sizeof(**dev)); return *dev ? 0 : 1;
}
static int RtmpOSNetDevOpsAlloc(PVOID *ops) { *ops=calloc(1,sizeof(struct net_device_ops)); return *ops ? 0 : 1; }
static void RtmpOSNetDevFree(PNET_DEV dev) { free(dev->netdev_ops); free(dev); }
static int RtmpOSNetDevRequestName(INT32 row, UINT32 *io, PNET_DEV dev, char *prefix, int index) {
    if(occupied && !strcmp(prefix,"wlan") && index==0) index=1;
    snprintf(dev->name,sizeof(dev->name),"%s%d",prefix,index); return 0;
}
'''
suffix = r'''
int main(void) {
    unsigned io=0; PNET_DEV dev;
    dev=RtmpOSNetDevCreate(0,&io,0,0,0,"wlan"); assert(dev && !strcmp(dev->name,"wlan0")); RtmpOSNetDevFree(dev);
    occupied=1;
    dev=RtmpOSNetDevCreate(0,&io,INT_APCLI,0,0,"wlan"); assert(dev && !strcmp(dev->name,"wlan2")); RtmpOSNetDevFree(dev);
    dev=RtmpOSNetDevCreate(0,&io,INT_APCLI,1,0,"wlan"); assert(dev && !strcmp(dev->name,"wlan3")); RtmpOSNetDevFree(dev);
    dev=RtmpOSNetDevCreate(0,&io,INT_APCLI,0,0,"apcli"); assert(dev && !strcmp(dev->name,"apcli0")); RtmpOSNetDevFree(dev);
    fail_alloc=1; assert(!RtmpOSNetDevCreate(0,&io,INT_APCLI,0,0,"wlan"));
    puts("Initial private APCLI names, primary/legacy names and allocation failure: PASS");
}
'''
with tempfile.TemporaryDirectory(prefix='h267a-name-test-') as directory:
    root = Path(directory)
    (root / 'test.c').write_text(prefix + function + suffix)
    subprocess.run(['cc', '-std=c99', '-O2', str(root / 'test.c'), '-o', str(root / 'test')], check=True)
    subprocess.run([str(root / 'test')], check=True, cwd=root)
