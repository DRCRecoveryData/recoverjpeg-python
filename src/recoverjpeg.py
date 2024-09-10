import os
import sys
import errno
import mmap

# Global configuration variables
verbose = False
quiet = False
max_size = 6 * 1024 * 1024
ignore_size = 0

# Utilities (converted from utils.h/utils.c)

def atol_suffix(s: str) -> int:
    """Convert size string to bytes (e.g., "512m" -> 512 * 1024 * 1024)"""
    suffixes = {'k': 1024, 'm': 1024 * 1024, 'g': 1024 * 1024 * 1024}
    if s[-1].lower() in suffixes:
        return int(s[:-1]) * suffixes[s[-1].lower()]
    return int(s)

def record_chdir(directory: str):
    """Change directory, or die if it fails"""
    try:
        os.chdir(directory)
    except OSError as e:
        print(f"recoverjpeg: unable to change to directory {directory} ({e})", file=sys.stderr)
        sys.exit(1)

def perform_chdirs():
    """Perform directory changes if necessary"""
    pass

def display_version_and_exit(progname: str):
    """Display version information and exit"""
    print(f"{progname} version 1.0")
    sys.exit(0)

# Main script

def usage(clean_exit=True):
    print("Usage: recoverjpeg [options] file|device")
    print("Options:")
    print("   -b blocksize   Block size in bytes (default: 512)")
    print("   -d format      Directory format string in printf syntax")
    print("   -f format      File format string in printf syntax")
    print("   -h             This help message")
    print("   -i index       Initial picture index")
    print("   -m maxsize     Max jpeg file size in bytes (default: 6m)")
    print("   -o directory   Restore jpeg files into this directory")
    print("   -q             Be quiet")
    print("   -r readsize    Size of disk reads in bytes (default: 128m)")
    print("   -s cutoff      Minimal file size in bytes to restore")
    print("   -S skipsize    Size to skip at the beginning")
    print("   -v             Be verbose")
    print("   -V             Display version and exit")
    sys.exit(0 if clean_exit else 1)

def progressbar():
    return not (quiet or verbose)

def display_progressbar(offset, n):
    gib_mode = False
    if offset < 1024 * 1024 * 1024:
        to_display = (offset // 1024) * 10 // 1024
    else:
        gib_mode = True
        to_display = (offset // (1024 * 1024)) * 10 // 1024
    print(f"\rRecovered files: {n:4}        Analyzed: {to_display / 10.0:.1f} {'GiB' if gib_mode else 'MiB'}  ", end="")
    sys.stdout.flush()

def cleanup_progressbar():
    print("\r                                                     \r", end="")

def jpeg_size(start):
    if start[0] != 0xff or start[1] != 0xd8:
        return 0

    if verbose:
        print("Candidate jpeg found")

    addr = 2
    while addr < len(start):
        if start[addr] != 0xff:
            if verbose:
                print(f"   Incorrect marker {start[addr]:02x}, stopping prematurely")
            return 0

        code = start[addr + 1]
        addr += 2

        if code == 0xd9:
            if verbose:
                print(f"   Found end of image after {addr + 1} bytes")
            return addr + 1

        if code == 0x01 or code == 0xff:
            if verbose:
                print(f"   Found lengthless section {code:02x}")
            continue

        size = (start[addr] << 8) + start[addr + 1]
        addr += size

        if verbose:
            print(f"   Found section {code:02x} of len {size}")

        if size < 2 or size > max_size:
            if verbose:
                print("   Section size is out of bounds, aborting")
            return 0

        if code == 0xda:
            if verbose:
                print("   Looking for end marker... ", end="")
                sys.stdout.flush()

            while addr < len(start) and ((start[addr] != 0xff or start[addr + 1] == 0 or
                                          (0xd0 <= start[addr + 1] <= 0xd7))):
                addr += 1

            if addr >= max_size:
                if verbose:
                    print("too big, aborting")
                return 0

            if verbose:
                print(f"found at offset {addr}")

    return 0

def file_name(dir_format, file_format, index):
    if dir_format:
        dir_buffer = dir_format % (index // 100)
        if not os.path.exists(dir_buffer):
            os.makedirs(dir_buffer)
        return os.path.join(dir_buffer, file_format % index)
    return file_format % index

def recoverjpeg(argv):
    global verbose, quiet, max_size, ignore_size

    read_size = 128 * 1024 * 1024
    block_size = 512
    skip_size = 0
    begin_index = 0
    file_format = "image%05d.jpg"
    dir_format = None

    if len(argv) != 2:
        usage()

    filename = argv[1]

    try:
        fd = open(filename, 'rb')
    except OSError as e:
        print(f"recoverjpeg: unable to open {filename} for reading ({e.strerror})")
        sys.exit(1)

    # Memory mapping for large file reading
    size = os.path.getsize(filename)
    mmapped_file = mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ)

    offset = 0
    i = 0

    while offset < size:
        if progressbar():
            display_progressbar(offset, i)

        # Search for jpeg segments
        jpeg_size_found = jpeg_size(mmapped_file[offset:])
        if jpeg_size_found > ignore_size:
            filepath = file_name(dir_format, file_format, begin_index + i)
            with open(filepath, 'wb') as output_file:
                output_file.write(mmapped_file[offset:offset + jpeg_size_found])

            i += 1
            offset += ((jpeg_size_found + block_size - 1) // block_size) * block_size
        else:
            offset += block_size

    if progressbar():
        cleanup_progressbar()

    if not quiet:
        print(f"Restored {i} picture{'s' if i > 1 else ''}")

if __name__ == "__main__":
    recoverjpeg(sys.argv)
