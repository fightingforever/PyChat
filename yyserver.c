/*
 *  Copyright (C) 2014 Guangmu Zhu <guangmuzhu@gmail.com>
 *
 *  This file is part of PyChat.
 *
 *  PyChat is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  PyChat is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with PyChat.  If not, see <http://www.gnu.org/licenses/>.
 */
 
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <memory.h>
#include <errno.h>

#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>

#include <sys/socket.h>
#include <netinet/in.h>

#include <pulse/simple.h>
#include <pulse/error.h>

#define BUFSIZE 4096
#define PORT 63336

int
main(int argc, char *argv[])
{
    char buf[BUFSIZE], data[BUFSIZE];
    ssize_t length = 0, count = 0;
    memset(buf, 0, BUFSIZE);
    memset(data, 0, BUFSIZE);
    
    static const pa_sample_spec pass = {
        .format = PA_SAMPLE_S16LE,
        .rate = 22050,
        .channels = 1
    };
    pa_simple *pas = NULL;
    int error = 0;
    if ((pas = pa_simple_new(NULL, "yyserver", PA_STREAM_PLAYBACK, NULL, "playback", &pass, NULL, NULL, &error)) == NULL) {
        fprintf(stderr, __FILE__": pa_simple_new() failed: %s\n", pa_strerror(error));
        if (pas) {
            pa_simple_free(pas);
        }
        exit(error);
    }
    
    int socket_fd;
    if ((socket_fd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        perror("server socket error");
        exit(1);
    }
    
    int reuse = 1;
    if (setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) != 0) {
        perror("setsockopt error");
        close(socket_fd);
        exit(1);
    }
    
    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(struct sockaddr_in));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    server_addr.sin_port = htons(PORT);
    if (bind(socket_fd, &server_addr, sizeof(server_addr)) == -1) {
        perror("bind error");
        close(socket_fd);
        exit(1);
    }
    
    if (listen(socket_fd, 1) == -1) {
        perror("listen error");
        close(socket_fd);
        exit(1);
    }
    
    int connect_fd;
    while (true) {
        if ((connect_fd = accept(socket_fd, (struct sockaddr*) NULL, 0)) == -1) {
            perror("accept error");
            continue;
        }
    
        while ((length = recv(connect_fd, buf, BUFSIZE, 0)) > 0) {
            if (count + length <= BUFSIZE) {
                memcpy(data + count, buf, length);
                count += length;
                if (count == BUFSIZE) {
                     if (pa_simple_write(pas, data, BUFSIZE, &error) < 0) {
                        fprintf(stderr, __FILE__": pa_simple_write() failed: %s\n", pa_strerror(error));
                        break;
                    }
                    count = 0;
                }
            } else {
                 if (pa_simple_write(pas, data, count, &error) < 0) {
                    fprintf(stderr, __FILE__": pa_simple_write() failed: %s\n", pa_strerror(error));
                    break;
                }
                memcpy(data, buf, length);
                count = length;
            }
        }
        
        if (length == -1) {
            perror("recv error");
        }
        
        if (pa_simple_drain(pas, &error) < 0) {
            fprintf(stderr, __FILE__": pa_simple_drain() failed: %s\n", pa_strerror(error));
        }
    
        close(connect_fd);
    }
    close(socket_fd);
    
    if (pas) {
        pa_simple_free(pas);
    }
    
    exit(0);
}
