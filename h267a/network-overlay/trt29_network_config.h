/* Network-layout compatibility only; this is not a hardware acceptance claim. */
#include <linux/kconfig.h>
#undef CONFIG_XFRM
#undef CONFIG_VLAN_8021Q
#undef CONFIG_VLAN_8021Q_MODULE
#undef CONFIG_XPS
#define CONFIG_XPS 1
#undef CONFIG_RFS_ACCEL
#define CONFIG_RFS_ACCEL 1
#undef CONFIG_BQL
#define CONFIG_BQL 1
#define PMSG_INVALID ((pm_message_t){ .event = -1 })

/* The actual TRT29 export table has no firmware_class loader. */
#undef CONFIG_FW_LOADER
#undef CONFIG_FW_LOADER_MODULE
