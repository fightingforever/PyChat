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
#include <arpa/inet.h>

#include <pulse/simple.h>
#include <pulse/error.h>

#define BUFSIZE 4096
#define PORT 63336

int
main(int argc, char *argv[])
{
    if (argc < 2) {
        exit(1);
    }
    
/*
 *  This didn't work    
 *  see how-to-use-echo-cancellation-module-in-pulseaudio
 *  [http://stackoverflow.com/questions/13363241/
 *  how-to-use-echo-cancellation-module-in-pulseaudio]
 *  setenv("PULSE_PROP", "filter.want=echo-cancel", 1);
 */ 
    
    char data[BUFSIZE];
    ssize_t length = 0;
    memset(data, 0, BUFSIZE);
    
    static const pa_sample_spec pass = {
        .format = PA_SAMPLE_S16LE,
        .rate = 22050,
        .channels = 1
    };
    pa_simple *pas = NULL;
    int error = 0;
    if ((pas = pa_simple_new(NULL, "yyclient", PA_STREAM_RECORD, NULL, "record", &pass, NULL, NULL, &error)) == NULL) {
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
    
    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(struct sockaddr_in));
    server_addr.sin_family = AF_INET;
    if(inet_pton(AF_INET, argv[1], &server_addr.sin_addr) <= 0){
        perror("inet_pton errno");
        close(socket_fd);
        exit(1);
    }
    server_addr.sin_port = htons(PORT);
    
    int connect_fd;
    if ((connect_fd = connect(socket_fd, (struct sockaddr*) &server_addr, sizeof(server_addr))) == -1) {
        perror("connect error");
        close(socket_fd);
        exit(1);
    }
    
    do {
         if (pa_simple_read(pas, data, BUFSIZE, &error) < 0) {
            fprintf(stderr, __FILE__": pa_simple_read() failed: %s\n", pa_strerror(error));
            if (pas) {
                pa_simple_free(pas);
            }
            close(connect_fd);
            close(socket_fd);
            exit(error);
        }
    } while ((length = send(socket_fd, data, BUFSIZE, 0)) == BUFSIZE);
    
    if (length == -1) {
        perror("send error");
        close(connect_fd);
        close(socket_fd);
        exit(errno);
    }
    
    close(connect_fd);
    close(socket_fd);
    
    exit(0);
}
