/* SPDX-License-Identifier: MIT */
/* One bounded RAM-file transfer from one allowed host; no execution or flash I/O. */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#ifndef BIND_ADDR
#define BIND_ADDR "127.0.0.1"
#endif
#ifndef ALLOWED_ADDR
#define ALLOWED_ADDR "127.0.0.1"
#endif
#ifndef PORT
#define PORT 18083
#endif
#ifndef OUTPUT_PATH
#define OUTPUT_PATH "/var/tmp/h267a-transfer.bin"
#endif

static int exact(int fd, void *buffer, size_t size)
{
    unsigned char *p = buffer;
    while (size) {
        ssize_t n = read(fd, p, size);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        p += n; size -= n;
    }
    return 0;
}

int main(void)
{
    int server = -1, client = -1, output = -1, result = 1, yes = 1;
    struct sockaddr_in local, peer;
    socklen_t peer_size = sizeof(peer);
    struct timeval deadline = {30, 0};
    unsigned char buffer[8192];
    uint32_t remaining;
    alarm(60);
    server = socket(AF_INET, SOCK_STREAM, 0);
    if (server < 0) goto done;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));
    local.sin_family = AF_INET; local.sin_port = htons(PORT);
    local.sin_addr.s_addr = inet_addr(BIND_ADDR);
    if (bind(server, (struct sockaddr *)&local, sizeof(local)) || listen(server, 1)) goto done;
    client = accept(server, (struct sockaddr *)&peer, &peer_size);
    if (client < 0 || peer.sin_addr.s_addr != inet_addr(ALLOWED_ADDR)) goto done;
    close(server); server = -1;
    setsockopt(client, SOL_SOCKET, SO_RCVTIMEO, &deadline, sizeof(deadline));
    if (exact(client, &remaining, sizeof(remaining))) goto done;
    remaining = ntohl(remaining);
    if (!remaining || remaining > 20U * 1024U * 1024U) goto done;
    output = open(OUTPUT_PATH, O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (output < 0) goto done;
    while (remaining) {
        size_t count = remaining < sizeof(buffer) ? remaining : sizeof(buffer);
        unsigned char *p = buffer;
        size_t unwritten = count;
        if (exact(client, buffer, count)) goto done;
        while (unwritten) {
            ssize_t n = write(output, p, unwritten);
            if (n < 0 && errno == EINTR) continue;
            if (n <= 0) goto done;
            p += n; unwritten -= n;
        }
        remaining -= count;
    }
    if (fsync(output)) goto done;
    if (write(client, "OK\n", 3) != 3) goto done;
    result = 0;
done:
    if (output >= 0) close(output);
    if (client >= 0) close(client);
    if (server >= 0) close(server);
    return result;
}
