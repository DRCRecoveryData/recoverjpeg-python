/*
 * This file is part of the recoverjpeg program.
 *
 * Copyright (c) 2004-2016 Samuel Tardieu <sam@rfc1149.net>
 * http://www.rfc1149.net/devel/recoverjpeg
 *
 * recoverjpeg is released under the GNU General Public License
 * version 2 that you can find in the COPYING file bundled with the
 * distribution.
 */

#ifndef _UTILS_H
#define _UTILS_H

#include <sys/types.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

size_t atol_suffix(char *arg);

void display_version_and_exit(const char *program_name)
    __attribute__((noreturn));

void record_chdir(const char *directory);

void perform_chdirs();

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* _UTILS_H */
